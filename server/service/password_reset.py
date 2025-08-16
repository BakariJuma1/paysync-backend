import resend
import os
import logging

logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY")

def send_password_reset_email(email, name, reset_token):
    sender_email = os.getenv("MAIL_DEFAULT_SENDER")

    html_content = f"""
    <html>
    <body>
        <h1>Password Reset</h1>
        <p>Hello {name},</p>
        <p>Use the following token to reset your password:</p>
        <h2 style="font-size: 24px; letter-spacing: 3px; margin: 20px 0;">
            {reset_token}
        </h2>
        <p>This token expires in 15 minutes.</p>
        <p>If you did not request a password reset, please ignore this email.</p>
    </body>
    </html>
    """

    try:
        response = resend.Emails.send({
            "from": f"PaySync <{sender_email}>",
            "to": [email],
            "subject": "Password Reset Request",
            "html": html_content
        })
        logger.info(f"Password reset email sent to {email}. Response: {response}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}. Resend error: {e}")
