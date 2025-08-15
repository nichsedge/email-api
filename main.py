from fastapi import FastAPI, Query
from functions.get_unread_emails import get_filtered_unread_emails
from functions.send_email import send_email
from functions.mark_email_as_read import mark_email_as_read
from functions.mark_emails_as_read_batch import mark_emails_as_read_batch
from functions.mark_emails_as_unread_batch import mark_emails_as_unread_batch

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

@app.post("/emails/mark-read-batch")
def mark_emails_as_read_batch_endpoint(request: dict):
    """
    Mark multiple emails as read in batch.
    
    Args:
        request (dict): JSON body containing 'email_ids' key with list of email IDs
    
    Returns:
        dict: Batch operation results
    """
    email_ids = request.get("email_ids", [])
    if not email_ids:
        return {"error": "email_ids field is required"}
    
    return mark_emails_as_read_batch(email_ids)

@app.post("/emails/mark-unread-batch")
def mark_emails_as_unread_batch_endpoint(request: dict):
    """
    Mark multiple emails as unread in batch.
    
    Args:
        request (dict): JSON body containing 'email_ids' key with list of email IDs
    
    Returns:
        dict: Batch operation results
    """
    email_ids = request.get("email_ids", [])
    if not email_ids:
        return {"error": "email_ids field is required"}
    
    return mark_emails_as_unread_batch(email_ids)
