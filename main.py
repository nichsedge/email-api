from fastapi import FastAPI, Query
from functions.get_unread_emails import get_filtered_unread_emails
from functions.send_email import send_email

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Email API is running"}

@app.get("/emails")
def read_emails(filter_by: str = "today", mark_as_read: bool = False):
    emails = get_filtered_unread_emails(filter_by=filter_by, mark_as_read=mark_as_read)
    return {"count": len(emails), "emails": emails}

@app.post("/send")
def send_email_endpoint(receiver_email: str, subject: str, body: str):
    return send_email(receiver_email, subject, body)
