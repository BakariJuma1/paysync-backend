import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os
import logging

logger = logging.getLogger(__name__)

def send_password_reset_email(email, name, reset_token):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender = {
        "email": os.getenv("MAIL_DEFAULT_SENDER"),
        "name": "PaySync"
    }

    to = [{
        "email": email,
        "name": name
    }]

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
        logger.info(f"Password reset email sent to {email}. Response: {response}")
    except ApiException as e:
        logger.error(f"Failed to send password reset email to {email}. Brevo error: {e}")
