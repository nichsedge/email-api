import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional, Any
import structlog
from cryptography.fernet import Fernet
from utils.auth import decrypt_data

logger = structlog.get_logger(__name__)


class SecureEmailClient:
    """Secure email client with dynamic credential support"""

    def __init__(self):
        self.cipher_suite = Fernet(Fernet.generate_key())

    def send_email(
        self,
        email_credentials: Dict[str, Any],
        receiver_email: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """Send email using provided credentials"""
        try:
            # Validate email credentials
            if not self._validate_credentials(email_credentials):
                return {"status": "error", "message": "Invalid email credentials"}

            # Decrypt password if encrypted
            password = email_credentials.get("password")
            if password and password.startswith("encrypted:"):
                password = decrypt_data(password[10:])

            # Create message
            message = MIMEMultipart()
            message["From"] = email_credentials["email_address"]
            message["To"] = receiver_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(
                email_credentials["smtp_server"], email_credentials["smtp_port"]
            ) as server:
                server.starttls()
                server.login(email_credentials["email_address"], password)
                server.sendmail(
                    email_credentials["email_address"],
                    receiver_email,
                    message.as_string(),
                )

            logger.info(
                "Email sent successfully",
                from_email=email_credentials["email_address"],
                to_email=receiver_email,
            )

            return {"status": "success", "message": f"Email sent to {receiver_email}"}

        except Exception as e:
            logger.error("Failed to send email", error=str(e))
            return {"status": "error", "message": str(e)}

    def get_unread_emails(
        self,
        email_credentials: Dict[str, Any],
        filter_by: str = "today",
        mark_as_read: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get unread emails using provided credentials"""
        try:
            # Validate email credentials
            if not self._validate_credentials(email_credentials):
                return [{"error": "Invalid email credentials"}]

            # Decrypt password if encrypted
            password = email_credentials.get("password")
            if password and password.startswith("encrypted:"):
                password = decrypt_data(password[10:])

            unread_emails = []

            with imaplib.IMAP4_SSL(
                email_credentials["imap_server"], email_credentials["imap_port"]
            ) as mail:
                mail.login(email_credentials["email_address"], password)
                mail.select("inbox")

                # Build search criteria
                search_criteria = ["UNSEEN"]
                if filter_by == "today":
                    today_str = datetime.utcnow().strftime("%d-%b-%Y")
                    search_criteria += ["SENTSINCE", today_str]
                elif filter_by == "date_range":
                    # Date range filtering would require additional parameters
                    pass
                elif filter_by != "all":
                    return [{"error": "Invalid filter option"}]

                # Search for emails
                _, email_ids = mail.search(None, *search_criteria)

                for email_id in email_ids[0].split():
                    fetch_cmd = "(RFC822)" if mark_as_read else "(BODY.PEEK[])"
                    _, msg_data = mail.fetch(email_id, fetch_cmd)

                    for part in msg_data:
                        if isinstance(part, tuple):
                            msg = email.message_from_bytes(part[1])
                            body = self._extract_email_body(msg)

                            unread_emails.append(
                                {
                                    "id": email_id.decode(),
                                    "subject": msg.get("subject", ""),
                                    "from_email": msg.get("from", ""),  # fixed key
                                    "body": body,
                                    "message_id": msg.get(
                                        "Message-ID", ""
                                    ),  # fixed key
                                    "timestamp": datetime.utcnow(),  # optional if you want it filled
                                }
                            )

                logger.info(
                    "Retrieved unread emails",
                    count=len(unread_emails),
                    filter_by=filter_by,
                )

                return unread_emails

        except Exception as e:
            logger.error("Failed to retrieve emails", error=str(e))
            return [{"error": str(e)}]

    def mark_email_as_read(
        self, email_credentials: Dict[str, Any], email_id: str
    ) -> Dict[str, Any]:
        """Mark email as read using provided credentials"""
        try:
            # Validate email credentials
            if not self._validate_credentials(email_credentials):
                return {"status": "error", "message": "Invalid email credentials"}

            # Decrypt password if encrypted
            password = email_credentials.get("password")
            if password and password.startswith("encrypted:"):
                password = decrypt_data(password[10:])

            with imaplib.IMAP4_SSL(
                email_credentials["imap_server"], email_credentials["imap_port"]
            ) as mail:
                mail.login(email_credentials["email_address"], password)
                mail.select("inbox")

                # Mark email as read
                mail.store(email_id, "+FLAGS", "\\Seen")

                logger.info("Email marked as read", email_id=email_id)

                return {
                    "status": "success",
                    "message": f"Email {email_id} marked as read",
                }

        except Exception as e:
            logger.error("Failed to mark email as read", error=str(e))
            return {"status": "error", "message": str(e)}

    def mark_emails_as_read_batch(
        self, email_credentials: Dict[str, Any], email_ids: List[str]
    ) -> Dict[str, Any]:
        """Mark multiple emails as read using provided credentials"""
        try:
            # Validate email credentials
            if not self._validate_credentials(email_credentials):
                return {"status": "error", "message": "Invalid email credentials"}

            # Decrypt password if encrypted
            password = email_credentials.get("password")
            if password and password.startswith("encrypted:"):
                password = decrypt_data(password[10:])

            results = []

            with imaplib.IMAP4_SSL(
                email_credentials["imap_server"], email_credentials["imap_port"]
            ) as mail:
                mail.login(email_credentials["email_address"], password)
                mail.select("inbox")

                for email_id in email_ids:
                    try:
                        mail.store(email_id, "+FLAGS", "\\Seen")
                        results.append(
                            {
                                "email_id": email_id,
                                "status": "success",
                                "message": f"Email {email_id} marked as read",
                            }
                        )
                    except Exception as e:
                        results.append(
                            {"email_id": email_id, "status": "error", "message": str(e)}
                        )

                success_count = sum(1 for r in results if r["status"] == "success")
                failure_count = len(results) - success_count

                logger.info(
                    "Batch email read operation completed",
                    total_processed=len(email_ids),
                    success_count=success_count,
                    failure_count=failure_count,
                )

                return {
                    "status": "completed",
                    "total_processed": len(email_ids),
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "details": results,
                }

        except Exception as e:
            logger.error("Failed to batch mark emails as read", error=str(e))
            return {"status": "error", "message": str(e)}

    def mark_emails_as_unread_batch(
        self, email_credentials: Dict[str, Any], email_ids: List[str]
    ) -> Dict[str, Any]:
        """Mark multiple emails as unread using provided credentials"""
        try:
            # Validate email credentials
            if not self._validate_credentials(email_credentials):
                return {"status": "error", "message": "Invalid email credentials"}

            # Decrypt password if encrypted
            password = email_credentials.get("password")
            if password and password.startswith("encrypted:"):
                password = decrypt_data(password[10:])

            results = []

            with imaplib.IMAP4_SSL(
                email_credentials["imap_server"], email_credentials["imap_port"]
            ) as mail:
                mail.login(email_credentials["email_address"], password)
                mail.select("inbox")

                for email_id in email_ids:
                    try:
                        mail.store(email_id, "-FLAGS", "\\Seen")
                        results.append(
                            {
                                "email_id": email_id,
                                "status": "success",
                                "message": f"Email {email_id} marked as unread",
                            }
                        )
                    except Exception as e:
                        results.append(
                            {"email_id": email_id, "status": "error", "message": str(e)}
                        )

                success_count = sum(1 for r in results if r["status"] == "success")
                failure_count = len(results) - success_count

                logger.info(
                    "Batch email unread operation completed",
                    total_processed=len(email_ids),
                    success_count=success_count,
                    failure_count=failure_count,
                )

                return {
                    "status": "completed",
                    "total_processed": len(email_ids),
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "details": results,
                }

        except Exception as e:
            logger.error("Failed to batch mark emails as unread", error=str(e))
            return {"status": "error", "message": str(e)}

    def _validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate email credentials structure"""
        required_fields = [
            "email_address",
            "smtp_server",
            "smtp_port",
            "imap_server",
            "imap_port",
        ]
        return all(field in credentials for field in required_fields)

    def _extract_email_body(self, msg) -> str:
        """Extract email body from message"""
        body = ""
        if msg.is_multipart():
            for subpart in msg.walk():
                if (
                    subpart.get_content_type() == "text/plain"
                    and "attachment" not in str(subpart.get("Content-Disposition"))
                ):
                    try:
                        payload = subpart.get_payload(decode=True)
                        if payload:
                            body = payload.decode()
                        break
                    except (UnicodeDecodeError, TypeError):
                        body = "[Could not decode body]"
                        break
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode()
            except (UnicodeDecodeError, TypeError):
                body = "[Could not decode body]"

        return body

    def _parse_email_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date string"""
        if not date_str:
            return None

        try:
            # Try parsing with email utils
            from email.utils import parsedate_to_datetime

            return parsedate_to_datetime(date_str)
        except:
            try:
                # Fallback to simple parsing
                from datetime import datetime

                return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            except:
                return None


# Global email client instance
secure_email_client = SecureEmailClient()
