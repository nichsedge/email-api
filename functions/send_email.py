import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.email_utils import SENDER_EMAIL, APP_PASSWORD

def send_email(receiver_email, subject, body):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    try:
        message = MIMEMultipart()
        message['From'] = SENDER_EMAIL
        message['To'] = receiver_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())

        return {"status": "success", "message": f"Email sent to {receiver_email}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
