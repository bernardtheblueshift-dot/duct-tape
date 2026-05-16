"""create resource management tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums first
    equipmentcondition_enum = postgresql.ENUM(
        "good", "fair", "poor", "maintenance", name="equipmentcondition", create_type=False
    )
    equipmentcondition_enum.create(op.get_bind(), checkfirst=True)

    assignmentstate_enum = postgresql.ENUM(
        "pending", "confirmed", "declined", name="assignmentstate", create_type=False
    )
    assignmentstate_enum.create(op.get_bind(), checkfirst=True)

    # 1. crew_profiles table
    op.create_table(
        "crew_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("bio", sa.String(), nullable=True),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "skills",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rating_average", sa.Numeric(3, 2), nullable=True),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_crew_profiles_tenant_id", "crew_profiles", ["tenant_id"])
    op.create_index("ix_crew_profiles_user_id", "crew_profiles", ["user_id"])

    # 2. equipment table
    op.create_table(
        "equipment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "condition",
            postgresql.ENUM(
                "good", "fair", "poor", "maintenance", name="equipmentcondition", create_type=False
            ),
            nullable=False,
            server_default="good",
        ),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("serial_number", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_equipment_tenant_id", "equipment", ["tenant_id"])
    op.create_index("ix_equipment_category", "equipment", ["category"])

    # 3. crew_assignments table
    op.create_table(
        "crew_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "crew_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crew_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending", "confirmed", "declined", name="assignmentstate", create_type=False
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("override_reason", sa.String(), nullable=True),
        sa.Column("declined_reason", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("crew_id", "job_id", name="uq_crew_job"),
    )
    op.create_index("ix_crew_assignments_tenant_id", "crew_assignments", ["tenant_id"])
    op.create_index("ix_crew_assignments_crew_id", "crew_assignments", ["crew_id"])
    op.create_index("ix_crew_assignments_job_id", "crew_assignments", ["job_id"])
    op.create_index("ix_crew_assignments_status", "crew_assignments", ["status"])

    # 4. equipment_assignments table
    op.create_table(
        "equipment_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "equipment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("equipment.id"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "quantity_assigned", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("equipment_id", "job_id", name="uq_equipment_job"),
    )
    op.create_index(
        "ix_equipment_assignments_tenant_id", "equipment_assignments", ["tenant_id"]
    )
    op.create_index(
        "ix_equipment_assignments_equipment_id",
        "equipment_assignments",
        ["equipment_id"],
    )
    op.create_index(
        "ix_equipment_assignments_job_id", "equipment_assignments", ["job_id"]
    )

    # 5. availability_patterns table
    op.create_table(
        "availability_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "crew_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crew_profiles.id"),
            nullable=False,
        ),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("crew_id", "day_of_week", name="uq_crew_day"),
    )
    op.create_index(
        "ix_availability_patterns_crew_id", "availability_patterns", ["crew_id"]
    )

    # 6. crew_ratings table
    op.create_table(
        "crew_ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "crew_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crew_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "rated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("crew_id", "job_id", name="uq_crew_job_rating"),
    )
    op.create_index("ix_crew_ratings_crew_id", "crew_ratings", ["crew_id"])
    op.create_index("ix_crew_ratings_job_id", "crew_ratings", ["job_id"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index("ix_crew_ratings_job_id", "crew_ratings")
    op.drop_index("ix_crew_ratings_crew_id", "crew_ratings")
    op.drop_table("crew_ratings")

    op.drop_index("ix_availability_patterns_crew_id", "availability_patterns")
    op.drop_table("availability_patterns")

    op.drop_index("ix_equipment_assignments_job_id", "equipment_assignments")
    op.drop_index("ix_equipment_assignments_equipment_id", "equipment_assignments")
    op.drop_index("ix_equipment_assignments_tenant_id", "equipment_assignments")
    op.drop_table("equipment_assignments")

    op.drop_index("ix_crew_assignments_status", "crew_assignments")
    op.drop_index("ix_crew_assignments_job_id", "crew_assignments")
    op.drop_index("ix_crew_assignments_crew_id", "crew_assignments")
    op.drop_index("ix_crew_assignments_tenant_id", "crew_assignments")
    op.drop_table("crew_assignments")

    op.drop_index("ix_equipment_category", "equipment")
    op.drop_index("ix_equipment_tenant_id", "equipment")
    op.drop_table("equipment")

    op.drop_index("ix_crew_profiles_user_id", "crew_profiles")
    op.drop_index("ix_crew_profiles_tenant_id", "crew_profiles")
    op.drop_table("crew_profiles")

    # Drop enums
    op.execute("DROP TYPE assignmentstate")
    op.execute("DROP TYPE equipmentcondition")
