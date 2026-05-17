"""create message_last_seen table for notification tracking

Revision ID: 007
Revises: 006
Create Date: 2026-05-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create message_last_seen table
    op.create_table(
        "message_last_seen",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("user_id", "job_id", name="uq_user_job_last_seen"),
    )

    # Create indexes
    op.create_index("ix_message_last_seen_tenant_id", "message_last_seen", ["tenant_id"])
    op.create_index("ix_message_last_seen_user_id", "message_last_seen", ["user_id"])
    op.create_index("ix_message_last_seen_job_id", "message_last_seen", ["job_id"])

    # Enable Row Level Security
    op.execute("ALTER TABLE message_last_seen ENABLE ROW LEVEL SECURITY")

    # Create RLS policy using tenant context
    op.execute(
        """
        CREATE POLICY tenant_isolation ON message_last_seen
        USING (tenant_id = COALESCE(
            NULLIF(current_setting('app.current_tenant_id', true), '')::uuid,
            '00000000-0000-0000-0000-000000000000'::uuid
        ))
        """
    )


def downgrade() -> None:
    # Drop RLS policy
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON message_last_seen")

    # Drop indexes
    op.drop_index("ix_message_last_seen_job_id", "message_last_seen")
    op.drop_index("ix_message_last_seen_user_id", "message_last_seen")
    op.drop_index("ix_message_last_seen_tenant_id", "message_last_seen")

    # Drop table
    op.drop_table("message_last_seen")
