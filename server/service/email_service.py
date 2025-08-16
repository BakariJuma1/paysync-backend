import resend
import os
import logging

logger = logging.getLogger(__name__)

# Set API key once
resend.api_key = os.getenv("RESEND_API_KEY")

def send_verification_email(user, otp_code):
    sender_email = os.getenv("MAIL_DEFAULT_SENDER")  # e.g. no-reply@yourdomain.com

    html_content = f"""
    <html>
    <body>
        <h1>Email Verification</h1>
        <p>Hello {user.name},</p>
        <p>Please verify your email using this 6-digit code:</p>
        <h2 style="font-size: 24px; letter-spacing: 3px; margin: 20px 0;">
            {otp_code}
        </h2>
        <p>This code is valid for 4 minutes.</p>
        <p>If you did not request this, please ignore this email.</p>
        <p>Thank you!</p>
        <p>Best regards,<br>PaySync Team</p>
        <p><small>This is an automated message, please do not reply.</small></p>
    </body>
    </html>
    """

    try:
        response = resend.Emails.send({
            "from": f"PaySync <{sender_email}>",
            "to": [user.email],
            "subject": "Verify your email",
            "html": html_content
        })
        logger.info(f"Verification email sent to {user.email}. Response: {response}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}. Resend error: {e}")
