# Hostinger Cold Email Automation

This project automates the sending of professional cold emails using Hostinger's SMTP and IMAP servers.

## Environment Variables

To run this project, you will need to create a `.env` file in the root directory. This file should contain your email server configuration and credentials.

Create a file named `.env` and add the following variables:

```env
# SMTP Configuration (For sending emails)
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=465
SMTP_EMAIL=your_email@domain.com
SMTP_PASSWORD=your_email_password

# IMAP Configuration (For saving to the Sent folder / syncing)
IMAP_HOST=imap.hostinger.com
IMAP_PORT=993
```

> **Note**: Make sure to replace `your_email@domain.com` and `your_email_password` with your actual Hostinger email account credentials. Never commit your `.env` file to version control.
