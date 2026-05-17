"""Tests for email notification tasks"""

import unittest.mock
from app.tasks.email import send_assignment_email, send_job_update_email
from app.config import settings


def test_send_assignment_email_content():
    """Test assignment email with role produces correct subject and body"""
    with unittest.mock.patch("smtplib.SMTP") as mock_smtp:
        # Call task synchronously
        send_assignment_email(
            email="crew@example.com",
            job_title="Summer Festival",
            job_id="abc-123",
            role="Camera Operator",
            venue="Central Park",
            scheduled_start="2026-06-01 09:00:00",
            scheduled_end="2026-06-01 17:00:00",
        )

        # Verify SMTP was called
        mock_smtp.assert_called_once_with(settings.SMTP_HOST, settings.SMTP_PORT)
        smtp_instance = mock_smtp.return_value.__enter__.return_value
        smtp_instance.send_message.assert_called_once()

        # Extract the sent message
        sent_msg = smtp_instance.send_message.call_args[0][0]

        # Verify headers
        assert sent_msg["Subject"] == "New assignment: Camera Operator - Summer Festival"
        assert sent_msg["From"] == settings.SMTP_FROM
        assert sent_msg["To"] == "crew@example.com"

        # Verify body content
        body = sent_msg.get_payload()
        assert "Summer Festival" in body
        assert "Camera Operator" in body
        assert "Central Park" in body
        assert "2026-06-01 09:00:00" in body
        assert "2026-06-01 17:00:00" in body
        assert f"{settings.FRONTEND_URL}/jobs/abc-123" in body


def test_send_assignment_email_no_role():
    """Test assignment email without role omits role from subject"""
    with unittest.mock.patch("smtplib.SMTP") as mock_smtp:
        send_assignment_email(
            email="crew@example.com",
            job_title="Summer Festival",
            job_id="abc-123",
            role=None,
            venue="Central Park",
            scheduled_start="2026-06-01 09:00:00",
            scheduled_end="2026-06-01 17:00:00",
        )

        smtp_instance = mock_smtp.return_value.__enter__.return_value
        sent_msg = smtp_instance.send_message.call_args[0][0]

        # Subject should not include role prefix
        assert sent_msg["Subject"] == "New assignment: Summer Festival"

        # Body should say "Not specified"
        body = sent_msg.get_payload()
        assert "Not specified" in body


def test_send_job_update_email_state_change():
    """Test job update email for state change"""
    with unittest.mock.patch("smtplib.SMTP") as mock_smtp:
        send_job_update_email(
            email="crew@example.com",
            job_title="Summer Festival",
            job_id="abc-123",
            event_type="state_change",
            old_state="intake",
            new_state="active",
        )

        smtp_instance = mock_smtp.return_value.__enter__.return_value
        sent_msg = smtp_instance.send_message.call_args[0][0]

        # Verify subject
        assert sent_msg["Subject"] == "Job update: Summer Festival"

        # Verify body contains state change info
        body = sent_msg.get_payload()
        assert "intake" in body
        assert "active" in body
        assert f"{settings.FRONTEND_URL}/jobs/abc-123" in body


def test_send_job_update_email_cancelled():
    """Test job update email for cancellation"""
    with unittest.mock.patch("smtplib.SMTP") as mock_smtp:
        send_job_update_email(
            email="crew@example.com",
            job_title="Summer Festival",
            job_id="abc-123",
            event_type="cancelled",
        )

        smtp_instance = mock_smtp.return_value.__enter__.return_value
        sent_msg = smtp_instance.send_message.call_args[0][0]

        # Verify subject
        assert sent_msg["Subject"] == "Job cancelled: Summer Festival"

        # Verify body mentions cancellation
        body = sent_msg.get_payload()
        assert "cancelled" in body.lower()
        assert f"{settings.FRONTEND_URL}/jobs/abc-123" in body


def test_email_uses_smtp_settings():
    """Test both tasks use settings.SMTP_FROM, SMTP_HOST, SMTP_PORT"""
    with unittest.mock.patch("smtplib.SMTP") as mock_smtp:
        # Test assignment email
        send_assignment_email(
            email="crew@example.com",
            job_title="Test",
            job_id="123",
            role="Crew",
            venue=None,
            scheduled_start=None,
            scheduled_end=None,
        )

        # Verify SMTP connection uses settings
        mock_smtp.assert_called_with(settings.SMTP_HOST, settings.SMTP_PORT)
        smtp_instance = mock_smtp.return_value.__enter__.return_value
        sent_msg = smtp_instance.send_message.call_args[0][0]
        assert sent_msg["From"] == settings.SMTP_FROM

        # Reset mock
        mock_smtp.reset_mock()

        # Test job update email
        send_job_update_email(
            email="crew@example.com",
            job_title="Test",
            job_id="123",
            event_type="cancelled",
        )

        # Verify SMTP connection uses settings
        mock_smtp.assert_called_with(settings.SMTP_HOST, settings.SMTP_PORT)
        smtp_instance = mock_smtp.return_value.__enter__.return_value
        sent_msg = smtp_instance.send_message.call_args[0][0]
        assert sent_msg["From"] == settings.SMTP_FROM
