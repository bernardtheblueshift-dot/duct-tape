"""iCal feed generation for crew assignment calendars"""

from icalendar import Calendar, Event
from datetime import datetime, timezone
from uuid import UUID
from app.models.assignment import CrewAssignment, AssignmentState
from app.models.job import Job


def build_ical_feed(
    assignments: list[CrewAssignment],
    jobs: dict[UUID, Job],
) -> bytes:
    """Generate RFC 5545 compliant iCal feed from crew assignments.

    Only includes CONFIRMED assignments with scheduled jobs.
    Returns bytes (raw .ics content).

    Args:
        assignments: List of crew assignments (all statuses)
        jobs: Dict mapping job_id to Job objects

    Returns:
        iCal feed as bytes
    """
    cal = Calendar()
    cal.add('prodid', '-//Duct Tape Crew Management//NONSGML v1.0//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', 'My Jobs - Duct Tape')
    cal.add('x-wr-timezone', 'UTC')

    for assignment in assignments:
        if assignment.status != AssignmentState.CONFIRMED:
            continue

        job = jobs.get(assignment.job_id)
        if not job or not job.scheduled_start or not job.scheduled_end:
            continue

        event = Event()
        event.add('uid', f'assignment-{assignment.id}@ducttape')
        event.add('dtstamp', datetime.now(timezone.utc))
        event.add('dtstart', job.scheduled_start)
        event.add('dtend', job.scheduled_end)

        # SUMMARY format: "Role - Job Title" when role exists, else just Job Title
        summary = f"{assignment.role} - {job.title}" if assignment.role else job.title
        event.add('summary', summary)

        if job.venue:
            event.add('location', job.venue)
        if job.description:
            event.add('description', job.description)

        event.add('status', 'CONFIRMED')
        event.add('transp', 'OPAQUE')  # Shows as "busy"

        cal.add_component(event)

    return cal.to_ical()
