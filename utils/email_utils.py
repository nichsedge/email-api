import os
from dotenv import load_dotenv

# Load environment variables locally
if os.path.exists(".env"):
    load_dotenv()

SENDER_EMAIL = os.getenv("GMAIL_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

if not SENDER_EMAIL or not APP_PASSWORD:
    raise ValueError("Missing GMAIL_EMAIL or GMAIL_APP_PASSWORD in environment variables.")
