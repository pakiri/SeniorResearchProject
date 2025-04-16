import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def sendEmail(username, email, subject, htmlContent):
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = email
    msg["Subject"] = subject

    msg.attach(MIMEText(htmlContent, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            # server.set_debuglevel(1)  # enable debugging to see SMTP logs
            server.ehlo()
            server.starttls()  # upgrade connection to secure
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)

            response = server.sendmail(SMTP_USERNAME, email, msg.as_string())
            if response:
                print(f"SMTP reported delivery issues: {response}")
            else:
                print(f"Email sent to {username} at {email} successfully!\n")

    except smtplib.SMTPRecipientsRefused:
        print(f"❌ Recipient address rejected: {email}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error occurred while sending to {email}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error sending email to {username}: {e}")
