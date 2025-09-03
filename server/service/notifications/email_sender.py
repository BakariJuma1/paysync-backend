# server/service/notifications/email_sender.py
import os
import base64
import logging
from typing import IO, Dict, List, Optional, Union
import resend

# sends the email using resend 

logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY")
DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@example.com")

def _encode_attachment(filename: str, content: Union[bytes, IO[bytes]], mime: str = "application/pdf") -> Dict:
    if hasattr(content, "read"):
        content_bytes = content.read()
        try:
            content.seek(0)
        except Exception:
            pass
    else:
        content_bytes = content
    return {
        "filename": filename,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
        "type": mime,
    }

def send_email(
    to: str,
    subject: str,
    html: str,
    attachments: Optional[List[Dict]] = None,
    sender: Optional[str] = None,
) -> Dict:
    payload = {
        "from": sender or DEFAULT_SENDER,
        "to": to,
        "subject": subject,
        "html": html,
    }
    if attachments:
        payload["attachments"] = attachments
    logger.info(f"Sending email to {to} with subject '{subject}'")
    return resend.Emails.send(payload)

def make_pdf_attachment(filename: str, pdf_buffer: IO[bytes]) -> Dict:
    return _encode_attachment(filename=filename, content=pdf_buffer, mime="application/pdf")
