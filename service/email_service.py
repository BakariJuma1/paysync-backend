import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os
import logging

logger = logging.getLogger(__name__)

def send_verification_email(user, otp_code):
    """
    Send a verification email with the given OTP code to the user.
    
    :param user: User model instance
    :param otp_code: str, 6-digit OTP code generated externally (e.g. via pyotp)
    """
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender = {
        "email": os.getenv("MAIL_DEFAULT_SENDER"),
        "name": "PaySync"
    }

    to = [{
        "email": user.email,
        "name": user.name
    }]

    subject = "Verify your email"

    html_content = f"""
    <html>
    <body>
        <h1>Email Verification</h1>
        <p>Hello {user.name},</p>
        <p>Please verify your email using this 6-digit code:</p>
        <h2 style="font-size: 24px; letter-spacing: 3px; margin: 20px 0;">
            {otp_code}
        </h2>
        <p>This code is valid for 30 seconds.</p>
        <p>If you did not request this, please ignore this email.</p>
        <p>Thank you!</p>
        <p>Best regards,<br>PaySync Team</p>
        <p><small>This is an automated message, please do not reply.</small></p>
    </body>
    </html>
    """

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
    )

    try:
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Verification email sent to {user.email}. Response: {response}")
    except ApiException as e:
        logger.error(f"Failed to send verification email to {user.email}. Brevo error: {e}")
