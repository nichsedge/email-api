from fastapi import FastAPI, Query
from functions.get_unread_emails import get_filtered_unread_emails
from functions.send_email import send_email
from functions.mark_email_as_read import mark_email_as_read

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

@app.post("/emails/{id}/mark-read")
def mark_email_as_read_endpoint(id: str):
    return mark_email_as_read(id)
