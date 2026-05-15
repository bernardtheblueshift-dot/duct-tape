from celery import shared_task
from email.mime.text import MIMEText
import smtplib
from app.config import settings


@shared_task
def send_verification_email(email: str, token: str):
    """
    Send email verification link to user

    Args:
        email: User's email address
        token: Verification token (expires in 24 hours)
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    subject = "Verify your email address"
    body = f"""Welcome to Duct Tape!

Click the link below to verify your email address:

{verification_url}

This link expires in 24 hours.

If you didn't create an account, you can safely ignore this email.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = email

    # Send via SMTP
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USER:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


@shared_task
def send_password_reset_email(email: str, token: str):
    """
    Send password reset link to user

    Args:
        email: User's email address
        token: Password reset token (expires in 1 hour)
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    subject = "Reset your password"
    body = f"""You requested a password reset.

Click the link below to reset your password:

{reset_url}

This link expires in 1 hour.

If you didn't request this, ignore this email. Your password will not be changed.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = email

    # Send via SMTP
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USER:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


@shared_task
def send_invitation_email(email: str, token: str, inviter_name: str, tenant_name: str):
    """
    Send invitation link to join a tenant

    Args:
        email: Invitee's email address
        token: Invitation token (expires in 7 days)
        inviter_name: Name of user who sent the invitation
        tenant_name: Name of the tenant organization
    """
    invitation_url = f"{settings.FRONTEND_URL}/accept-invitation?token={token}"

    subject = f"You've been invited to join {tenant_name} on Duct Tape"
    body = f"""{inviter_name} has invited you to join {tenant_name} on Duct Tape.

Click the link below to create your account:

{invitation_url}

This invitation expires in 7 days.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = email

    # Send via SMTP
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USER:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
