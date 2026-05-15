"""Enable Row-Level Security

Revision ID: 002
Revises: 001
Create Date: 2026-05-16
"""

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable RLS on users table
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")

    # Create RLS policy: only show rows where tenant_id matches session variable
    op.execute(
        """
        CREATE POLICY tenant_isolation ON users
        USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE))
    """
    )

    # Force RLS even for table owner (required for superuser protection)
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")

    # Enable RLS on invitation_tokens (also tenant-scoped)
    op.execute("ALTER TABLE invitation_tokens ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON invitation_tokens
        USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE))
    """
    )
    op.execute("ALTER TABLE invitation_tokens FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON users")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON invitation_tokens")
    op.execute("ALTER TABLE invitation_tokens DISABLE ROW LEVEL SECURITY")
