import imaplib
from utils.email_utils import SENDER_EMAIL, APP_PASSWORD

def mark_emails_as_unread_batch(email_ids):
    """
    Mark multiple emails as unread by their IDs.
    
    Args:
        email_ids (list): List of email IDs (UIDs or sequence numbers) to mark as unread
    
    Returns:
        dict: Status message indicating success or failure, with details for each email
    """
    imap_server = 'imap.gmail.com'
    imap_port = 993
    results = []
    
    try:
        with imaplib.IMAP4_SSL(imap_server, imap_port) as mail:
            mail.login(SENDER_EMAIL, APP_PASSWORD)
            mail.select('inbox')
            
            for email_id in email_ids:
                try:
                    # Mark the email as unread using STORE command
                    # '-FLAGS' means remove flags, '\\Seen' is the flag for read emails
                    mail.store(email_id, '-FLAGS', '\\Seen')
                    results.append({
                        "email_id": email_id,
                        "status": "success",
                        "message": f"Email {email_id} marked as unread"
                    })
                except Exception as e:
                    results.append({
                        "email_id": email_id,
                        "status": "error",
                        "message": str(e)
                    })
            
            # Count successes and failures
            success_count = sum(1 for r in results if r["status"] == "success")
            failure_count = len(results) - success_count
            
            return {
                "status": "completed",
                "total_processed": len(email_ids),
                "success_count": success_count,
                "failure_count": failure_count,
                "details": results
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Connection error: {str(e)}",
            "details": []
        }