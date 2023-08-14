import imaplib
import email
from email.header import decode_header
import ssl
import os
import pytesseract
# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Replace with the actual path
from PIL import Image
import openai
import json
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import time
from dotenv import load_dotenv

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
# Email credentials and server settings
EMAIL =  os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
openai.api_key =  os.getenv("OPENAI_API_KEY")
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

def create_calendar_event(start_time, end_time, description, location):
    #credentials.json taken from developer api
    #token.json made from user authorization
    """Creates a new event in the user's Google Calendar."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        print(start_time)
        print(end_time)

        # Create the event
        event = {
            'summary': description,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/New_York',
            },
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: %s' % created_event.get('htmlLink'))

    except HttpError as error:
        print('An error occurred: %s' % error)

def delete_all_calendar_events():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Get a list of events
        events_result = service.events().list(calendarId='primary', maxResults=2500).execute()
        events = events_result.get('items', [])

        # Delete each event
        for event in events:
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
            print(f"Deleted event: {event['summary']}")

    except HttpError as error:
        print('An error occurred: %s' % error)

# Connect to the IMAP server
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# Establish the connection and log in
mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(EMAIL, PASSWORD)

# delete_all_calendar_events()

try:
    while True:
        try:
            mail.select("Inbox")  # You can select other folders too
            print("checking email")
            now = datetime.now()
            search_date = now.strftime("%d-%b-%Y")
            # Search for emails today
            search_criteria = f'SINCE "{search_date}"'
            status, email_ids = mail.search(None, search_criteria)

            if status == "OK":
                email_id_list = email_ids[0].split()
                for email_id in email_id_list:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status == "OK":
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        subject = msg["Subject"]
                        from_name, from_addr = email.utils.parseaddr(msg["From"])

                        print("New Email:")
                        print("From:", from_name)
                        print("Subject:", subject)
                        # print("Attachment Detected: ", attachment_detected)
                        print("=" * 50)
                        
                        attachment_detected = False
                        for part in msg.walk():
                            if part.get_content_maintype() == "multipart":
                                continue
                            if part.get("Content-Disposition") is None:
                                continue
                            filename = part.get_filename()
                            attachment_detected = filename is not None
                        
                        
                        if attachment_detected:
                            filepath = os.path.join(".", filename)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                                print("Attachment saved:", filepath)

                            extracted_text = pytesseract.image_to_string(Image.open(filepath), lang='eng')
                            #remove the image after used
                            os.remove(filepath)
                            # Send the prompt to GPT-3
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",  # Use the GPT-3.5 Turbo model for chat
                                messages=[
                                    {"role": "system", "content": f"You are a helpful assistant. The current date is {datetime.now()} What is the start time and end time in YYYY-MM-DD + T + HH:DD:SS format (append the strings, omit the +). Put this in JSON format with StartTime, EndTime, Location, Summary (summarize the activity into 5 words or less)"},
                                    {"role": "user", "content": extracted_text}
                                ],
                                max_tokens=100,  # Set the desired response length
                                temperature=0.3
                            )
                            # Print the AI's response
                            json_string = response.choices[0].message["content"].strip()

                            event_data = json.loads(json_string)
                            start_time = event_data["StartTime"]
                            end_time = event_data["EndTime"]
                            description = event_data["Summary"]
                            location = event_data["Location"]
                            create_calendar_event(start_time, end_time, description, location)

                    mail.store(email_id.decode("utf-8"), '+FLAGS', '\\Deleted') # Mark the email as deleted
                    mail.expunge()  # Permanently delete the flagged email

                #delete email here
        except Exception as e:
            print("Error:", e)

        # Wait for 60 seconds before checking again
        time.sleep(30)  # Wait for 60 seconds before checking again

finally:
    # Disconnect from the server
    mail.logout()
