import resend
import os
import logging

logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY")

def send_invitation_email(user_email, user_name, business_name, role, invite_url):
    sender_email = os.getenv("MAIL_DEFAULT_SENDER")

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

    try:
        response = resend.Emails.send({
            "from": f"PaySync <{sender_email}>",
            "to": [user_email],
            "subject": f"Invitation to join {business_name} as {role}",
            "html": html_content
        })
        logger.info(f"Invitation email sent to {user_email}. Response: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send invitation email to {user_email}. Resend error: {e}")
        return False
