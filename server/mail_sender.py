import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv

load_dotenv()
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_LOGIN = os.getenv("SMTP_LOGIN")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_NAME = os.getenv("SMTP_NAME")


# нужна отладка с конкретными параметрами подключения
def send_email(key_value, to_email):
    subject = "Notification"
    text = key_value

    msg = MIMEMultipart()
    msg['From'] = f"{SMTP_NAME} <{SMTP_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(text, 'plain'))

    try:
        smtp_server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        smtp_server.login(SMTP_LOGIN, SMTP_PASSWORD)
        smtp_server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        smtp_server.quit()
        print("Email sent successfully.")
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False
