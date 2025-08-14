import imaplib
import email
from utils.email_utils import SENDER_EMAIL, APP_PASSWORD

def mark_email_as_read(email_id):
    """
    Mark a specific email as read by its ID.
    
    Args:
        email_id (str): The email ID (UID or sequence number) to mark as read
    
    Returns:
        dict: Status message indicating success or failure
    """
    imap_server = 'imap.gmail.com'
    imap_port = 993
    
    try:
        with imaplib.IMAP4_SSL(imap_server, imap_port) as mail:
            mail.login(SENDER_EMAIL, APP_PASSWORD)
            mail.select('inbox')
            
            # Mark the email as read using STORE command
            # '+FLAGS' means add flags, '\\Seen' is the flag for read emails
            mail.store(email_id, '+FLAGS', '\\Seen')
            
            return {"status": "success", "message": f"Email {email_id} marked as read"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}