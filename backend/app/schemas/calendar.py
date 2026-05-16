"""Pydantic schemas for calendar API requests and responses"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from uuid import UUID
from app.models.job import JobState

# Color scheme for job states on calendar
JOB_STATE_COLORS = {
    "intake": "#3B82F6",  # blue
    "simmer": "#EAB308",  # yellow
    "active": "#10B981",  # green
    "complete": "#6B7280",  # grey
}


class CalendarEvent(BaseModel):
    """Unified calendar event for jobs and assignments"""

    id: UUID
    event_type: str  # 'job', 'crew_assignment', 'equipment_assignment'
    title: str
    start: datetime
    end: datetime
    color: str  # hex code from JOB_STATE_COLORS
    status: str  # job state or assignment status string
    job_id: UUID | None = None  # populated for assignment events
    resource_id: UUID | None = None  # crew_id or equipment_id
    resource_name: str | None = None  # crew user email or equipment name
    job_title: str | None = None  # job title (for assignment events)
    role: str | None = None  # crew assignment role

    model_config = ConfigDict(from_attributes=True)


class CalendarEventsResponse(BaseModel):
    """Response wrapper for calendar events list"""

    events: list[CalendarEvent]
    count: int


class AvailabilityDay(BaseModel):
    """Single day availability status"""

    date: date
    status: str  # 'free' | 'booked' | 'unavailable'


class CrewAvailabilitySummary(BaseModel):
    """Crew member availability summary across date range"""

    crew_id: UUID
    crew_name: str
    days: list[AvailabilityDay]


class ICalTokenCreate(BaseModel):
    """Request schema for creating iCal feed token"""

    crew_id: UUID


class ICalTokenResponse(BaseModel):
    """Response schema for iCal token with feed URL"""

    id: UUID
    crew_id: UUID
    token: str
    feed_url: str  # Computed: /ical/{token}.ics
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
