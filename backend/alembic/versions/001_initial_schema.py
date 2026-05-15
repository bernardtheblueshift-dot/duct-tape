"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
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

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "role",
            sa.Enum("admin", "crew", name="userrole"),
            nullable=False,
            server_default="crew",
        ),
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
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
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_foreign_key(
        "fk_users_tenant_id", "users", "tenants", ["tenant_id"], ["id"]
    )

    # Create verification_tokens table
    op.create_table(
        "verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
    op.create_index(
        "ix_verification_tokens_token", "verification_tokens", ["token"], unique=True
    )
    op.create_foreign_key(
        "fk_verification_tokens_user_id",
        "verification_tokens",
        "users",
        ["user_id"],
        ["id"],
    )

    # Create password_reset_tokens table
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
    op.create_index(
        "ix_password_reset_tokens_token",
        "password_reset_tokens",
        ["token"],
        unique=True,
    )
    op.create_foreign_key(
        "fk_password_reset_tokens_user_id",
        "password_reset_tokens",
        "users",
        ["user_id"],
        ["id"],
    )

    # Create invitation_tokens table
    op.create_table(
        "invitation_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "crew", name="userrole"),
            nullable=False,
            server_default="crew",
        ),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=False),
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
    op.create_index("ix_invitation_tokens_email", "invitation_tokens", ["email"])
    op.create_index(
        "ix_invitation_tokens_tenant_id", "invitation_tokens", ["tenant_id"]
    )
    op.create_index(
        "ix_invitation_tokens_token", "invitation_tokens", ["token"], unique=True
    )
    op.create_foreign_key(
        "fk_invitation_tokens_tenant_id",
        "invitation_tokens",
        "tenants",
        ["tenant_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_invitation_tokens_invited_by",
        "invitation_tokens",
        "users",
        ["invited_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_table("invitation_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("verification_tokens")
    op.drop_table("users")
    op.drop_table("tenants")
    op.execute("DROP TYPE userrole")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
