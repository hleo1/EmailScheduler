To Setup:
- Need a "credentials.json" that is generated from your Google Cloud Project developer account
- Need a .env file that has the email and password of the email that you would like to send calendar events to, as well as the openai api key.
You need to make sure that IMAP is enabled through your email provider. For gmail, you also need to enable 2FA, and under 2FA settings, 
setup an application password for your desktop application. This will be the password you put in your .env file.

- "token.json" will get generated automatically