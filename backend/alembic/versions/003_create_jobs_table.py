"""create jobs table

Revision ID: 003
Revises: 002
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    jobstate_enum = postgresql.ENUM("intake", "simmer", "active", "complete", name="jobstate", create_type=False)
    jobstate_enum.create(op.get_bind(), checkfirst=True)

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("venue", sa.String(), nullable=True),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "state",
            postgresql.ENUM("intake", "simmer", "active", "complete", name="jobstate", create_type=False),
            nullable=False,
            server_default="intake",
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
    )

    # Create indexes
    op.create_index("ix_jobs_tenant_id", "jobs", ["tenant_id"])
    op.create_index("ix_jobs_state", "jobs", ["state"])
    op.create_index("ix_jobs_scheduled_start", "jobs", ["scheduled_start"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_jobs_scheduled_start", "jobs")
    op.drop_index("ix_jobs_state", "jobs")
    op.drop_index("ix_jobs_tenant_id", "jobs")

    # Drop table
    op.drop_table("jobs")

    # Drop enum type
    op.execute("DROP TYPE jobstate")
