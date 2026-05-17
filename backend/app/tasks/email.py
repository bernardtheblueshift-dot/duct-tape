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
    body = f"""Welcome to GT!

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

    subject = f"You've been invited to join {tenant_name} on GT"
    body = f"""{inviter_name} has invited you to join {tenant_name} on GT.

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


@shared_task
def send_assignment_email(
    email: str,
    job_title: str,
    job_id: str,
    role: str | None,
    venue: str | None,
    scheduled_start: str | None,
    scheduled_end: str | None,
):
    """
    Send crew assignment notification email

    Args:
        email: Crew member's email address
        job_title: Title of the job
        job_id: Job UUID (for link)
        role: Assigned role (e.g., "Camera Operator"), or None
        venue: Job venue, or None
        scheduled_start: Job start datetime as string, or None
        scheduled_end: Job end datetime as string, or None
    """
    # Build subject based on whether role is specified
    if role:
        subject = f"New assignment: {role} - {job_title}"
    else:
        subject = f"New assignment: {job_title}"

    # Format dates for display
    if scheduled_start and scheduled_end:
        schedule_text = f"{scheduled_start} - {scheduled_end}"
    else:
        schedule_text = "TBD"

    job_url = f"{settings.FRONTEND_URL}/jobs/{job_id}"

    body = f"""You've been assigned to a job on GT.

Job: {job_title}
Role: {role or "Not specified"}
Venue: {venue or "TBD"}
Scheduled: {schedule_text}

View job details:
{job_url}
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
def send_job_update_email(
    email: str,
    job_title: str,
    job_id: str,
    event_type: str,
    old_state: str | None = None,
    new_state: str | None = None,
):
    """
    Send job update notification email

    Args:
        email: Crew member's email address
        job_title: Title of the job
        job_id: Job UUID (for link)
        event_type: Either "state_change" or "cancelled"
        old_state: Previous state (for state_change events)
        new_state: New state (for state_change events)
    """
    job_url = f"{settings.FRONTEND_URL}/jobs/{job_id}"

    if event_type == "cancelled":
        subject = f"Job cancelled: {job_title}"
        body = f"""This job has been cancelled.

Job: {job_title}

View job details:
{job_url}
"""
    else:  # state_change
        subject = f"Job update: {job_title}"
        body = f"""A job you're assigned to has been updated.

Job: {job_title}
Status changed: {old_state} → {new_state}

View job details:
{job_url}
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
