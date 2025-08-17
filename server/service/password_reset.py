import os
import logging
import resend

logger = logging.getLogger(__name__)

# Configure Resend API key once
resend.api_key = os.getenv("RESEND_API_KEY")

def send_password_reset_email(email, name, reset_token):
    sender = os.getenv("MAIL_DEFAULT_SENDER")
    
    subject = "Password Reset Request"
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
        <p>Best regards,<br>PaySync Team</p>
        <p><small>This is an automated message, please do not reply.</small></p>
    </body>
    </html>
    """

    try:
        response = resend.Emails.send({
            "from": sender,
            "to": email,
            "subject": subject,
            "html": html_content,
        })
        logger.info(f"Password reset email sent to {email}. Response: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}. Resend error: {e}")
        return False
