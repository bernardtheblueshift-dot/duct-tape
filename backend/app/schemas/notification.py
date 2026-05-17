from pydantic import BaseModel


class NotificationCounts(BaseModel):
    """Badge count data for in-app notifications"""
    unread_messages: int = 0
    pending_assignments: int = 0
