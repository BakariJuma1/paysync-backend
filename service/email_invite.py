import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def send_invitation_email(user_email, user_name, business_name, role, invite_url):
    """
    Send an invitation email to join the business
    
    :param user_email: Email of the invited user
    :param user_name: Name of the invited user
    :param business_name: Name of the business they're being invited to
    :param role: Role they're being invited as
    :param invite_url: URL to accept the invitation
    """
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender = {
        "email": os.getenv("MAIL_DEFAULT_SENDER"),
        "name": "PaySync"
    }

    to = [{
        "email": user_email,
        "name": user_name
    }]

    subject = f"Invitation to join {business_name} as {role}"

    html_content = f"""
    <html>
    <body>
        <h1>Team Invitation</h1>
        <p>Hello {user_name},</p>
        <p>You've been invited to join <strong>{business_name}</strong> as a <strong>{role}</strong>.</p>
        <p>Please click the button below to accept the invitation:</p>
        <p style="margin: 30px 0;">
            <a href="{invite_url}" style="background-color: #4CAF50; color: white; 
               padding: 12px 24px; text-align: center; text-decoration: none; 
               display: inline-block; border-radius: 4px;">
                Accept Invitation
            </a>
        </p>
        <p>This invitation link will expire in 48 hours.</p>
        <p>If you didn't request this invitation, please ignore this email.</p>
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
        logger.info(f"Invitation email sent to {user_email}. Response: {response}")
        return True
    except ApiException as e:
        logger.error(f"Failed to send invitation email to {user_email}. Brevo error: {e}")
        return False