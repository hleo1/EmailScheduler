To Setup:
- Using Python v11
- Need a "credentials.json" that is generated from your Google Cloud Project developer account
- Need a .env file that has the email and password of the email that you would like to send calendar events to, as well as the openai api key.
You need to make sure that IMAP is enabled through your email provider. For gmail, you also need to enable 2FA, and under 2FA settings, 
setup an application password for your desktop application. This will be the password you put in your .env file.
- Need to download and install tesseract before using pytesseract: https://tesseract-ocr.github.io/tessdoc/Installation.html
Then in pytesseract.pytesseract.tesseract_cmd need to set the path to the location of the tesseract.exe file

- "token.json" will get generated automatically

To Deploy: 
- Once you confirm code is working locally, you can create your own AWS EC2 instance and run the program there. EC2 micro is free for 12 months.
You can also convert this into a AWS Lamda function that gets scheduled every 5 minutes (however I'm not too sure about Google's OAuth2 and 
whether user interaction is needed... I chose EC2 as a result, but a Lamda function uses less resources and is considered "free forever" in 
AWS free tier). Can also convert to a server and deploy on Heroku/AWS beanstalk. Any other ideas? Feel free to put in the issues tab!