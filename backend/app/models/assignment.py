"""Assignment models for crew and equipment with state machine"""

from sqlalchemy import Column, String, ForeignKey, Integer, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid
import enum


class AssignmentState(str, enum.Enum):
    """Assignment lifecycle states"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"


# State transition rules following state_machine.py pattern
ASSIGNMENT_TRANSITIONS = {
    AssignmentState.PENDING: [AssignmentState.CONFIRMED, AssignmentState.DECLINED],
    AssignmentState.CONFIRMED: [AssignmentState.DECLINED],
    AssignmentState.DECLINED: [],  # Terminal state
}


class CrewAssignment(Base, TenantMixin, TimestampMixin):
    """Crew assignment to job with confirmation workflow"""

    __tablename__ = "crew_assignments"
    __table_args__ = (UniqueConstraint("crew_id", "job_id", name="uq_crew_job"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crew_id = Column(
        UUID(as_uuid=True), ForeignKey("crew_profiles.id"), nullable=False
    )
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    role = Column(
        String, nullable=True
    )  # Position on this job (e.g., "Camera Operator")
    status = Column(
        Enum(AssignmentState), nullable=False, default=AssignmentState.PENDING
    )
    override_reason = Column(
        String, nullable=True
    )  # When admin force-assigns despite conflict
    declined_reason = Column(String, nullable=True)  # When crew declines
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin


class EquipmentAssignment(Base, TenantMixin, TimestampMixin):
    """Equipment assignment to job with quantity tracking"""

    __tablename__ = "equipment_assignments"
    __table_args__ = (
        UniqueConstraint("equipment_id", "job_id", name="uq_equipment_job"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(
        UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False
    )
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    quantity_assigned = Column(Integer, nullable=False, default=1)
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
