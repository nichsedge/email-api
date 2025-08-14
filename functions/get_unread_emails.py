import imaplib
import email
from datetime import datetime
from utils.email_utils import SENDER_EMAIL, APP_PASSWORD

def get_filtered_unread_emails(
    filter_by='today',
    start_date=None,
    end_date=None,
    mark_as_read=False
):
    imap_server = 'imap.gmail.com'
    imap_port = 993
    unread_emails = []

    try:
        with imaplib.IMAP4_SSL(imap_server, imap_port) as mail:
            mail.login(SENDER_EMAIL, APP_PASSWORD)
            mail.select('inbox')

            search_criteria = ['UNSEEN']
            if filter_by == 'today':
                today_str = datetime.utcnow().strftime('%d-%b-%Y')
                search_criteria += ['SENTSINCE', today_str]
            elif filter_by == 'date_range':
                if not start_date or not end_date:
                    raise ValueError("start_date and end_date must be provided for 'date_range'")
                search_criteria += [
                    'SENTSINCE', start_date.strftime('%d-%b-%Y'),
                    'SENTBEFORE', end_date.strftime('%d-%b-%Y')
                ]
            elif filter_by != 'all':
                raise ValueError("Invalid filter_by option. Use 'today', 'date_range', or 'all'.")

            _, email_ids = mail.search(None, *search_criteria)
            for email_id in email_ids[0].split():
                fetch_cmd = '(RFC822)' if mark_as_read else '(BODY.PEEK[])'
                _, msg_data = mail.fetch(email_id, fetch_cmd)
                for part in msg_data:
                    if isinstance(part, tuple):
                        msg = email.message_from_bytes(part[1])
                        body = ""
                        if msg.is_multipart():
                            for subpart in msg.walk():
                                if subpart.get_content_type() == "text/plain" and 'attachment' not in str(subpart.get("Content-Disposition")):
                                    try:
                                        body = subpart.get_payload(decode=True).decode()
                                    except UnicodeDecodeError:
                                        body = "[Could not decode body]"
                                    break
                        else:
                            try:
                                body = msg.get_payload(decode=True).decode()
                            except UnicodeDecodeError:
                                body = "[Could not decode body]"

                        unread_emails.append({
                            "From": msg.get("from"),
                            "Subject": msg.get("subject"),
                            "Body": body
                        })

            return unread_emails

    except Exception as e:
        return {"error": str(e)}
