"""create ical_tokens table

Revision ID: 005
Revises: 004
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ical_tokens table
    op.create_table(
        "ical_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "crew_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crew_profiles.id"),
            nullable=False,
        ),
        sa.Column("token", sa.String(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_ical_tokens_tenant_id", "ical_tokens", ["tenant_id"])
    op.create_index("ix_ical_tokens_token", "ical_tokens", ["token"], unique=True)

    # Enable Row Level Security
    op.execute("ALTER TABLE ical_tokens ENABLE ROW LEVEL SECURITY")

    # Create RLS policy using tenant context
    op.execute(
        """
        CREATE POLICY tenant_isolation ON ical_tokens
        USING (tenant_id = COALESCE(
            NULLIF(current_setting('app.current_tenant_id', true), '')::uuid,
            '00000000-0000-0000-0000-000000000000'::uuid
        ))
        """
    )


def downgrade() -> None:
    # Drop RLS policy
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON ical_tokens")

    # Drop indexes
    op.drop_index("ix_ical_tokens_token", "ical_tokens")
    op.drop_index("ix_ical_tokens_tenant_id", "ical_tokens")

    # Drop table
    op.drop_table("ical_tokens")
