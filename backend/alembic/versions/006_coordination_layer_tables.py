"""create coordination layer tables (messages, tasks, job_files, message_files)

Revision ID: 006
Revises: 005
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create taskstatus enum
    op.execute(
        """
        CREATE TYPE taskstatus AS ENUM ('todo', 'in_progress', 'done')
        """
    )

    # Create taskpriority enum
    op.execute(
        """
        CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high', 'urgent')
        """
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "reply_to_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id"),
            nullable=True,
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

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "assignee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crew_profiles.id"),
            nullable=True,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("todo", "in_progress", "done", name="taskstatus"),
            nullable=False,
            server_default="todo",
        ),
        sa.Column(
            "priority",
            postgresql.ENUM("low", "medium", "high", "urgent", name="taskpriority"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id"),
            nullable=True,
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

    # Create job_files table
    op.create_table(
        "job_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "uploader_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
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

    # Create message_files association table
    op.create_table(
        "message_files",
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_files.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # Create indexes
    op.create_index("ix_messages_tenant_id", "messages", ["tenant_id"])
    op.create_index("ix_messages_job_id", "messages", ["job_id"])
    op.create_index("ix_tasks_tenant_id", "tasks", ["tenant_id"])
    op.create_index("ix_tasks_job_id", "tasks", ["job_id"])
    op.create_index("ix_job_files_tenant_id", "job_files", ["tenant_id"])
    op.create_index("ix_job_files_job_id", "job_files", ["job_id"])

    # Enable Row Level Security on all tables
    op.execute("ALTER TABLE messages ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tasks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE job_files ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE message_files ENABLE ROW LEVEL SECURITY")

    # Create RLS policies using tenant context
    op.execute(
        """
        CREATE POLICY tenant_isolation ON messages
        USING (tenant_id = COALESCE(
            NULLIF(current_setting('app.current_tenant_id', true), '')::uuid,
            '00000000-0000-0000-0000-000000000000'::uuid
        ))
        """
    )

    op.execute(
        """
        CREATE POLICY tenant_isolation ON tasks
        USING (tenant_id = COALESCE(
            NULLIF(current_setting('app.current_tenant_id', true), '')::uuid,
            '00000000-0000-0000-0000-000000000000'::uuid
        ))
        """
    )

    op.execute(
        """
        CREATE POLICY tenant_isolation ON job_files
        USING (tenant_id = COALESCE(
            NULLIF(current_setting('app.current_tenant_id', true), '')::uuid,
            '00000000-0000-0000-0000-000000000000'::uuid
        ))
        """
    )

    # message_files has no tenant_id column - rely on FK to tenant-isolated tables
    # No RLS policy needed as access is controlled via messages and job_files


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON messages")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON tasks")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON job_files")

    # Drop indexes
    op.drop_index("ix_job_files_job_id", "job_files")
    op.drop_index("ix_job_files_tenant_id", "job_files")
    op.drop_index("ix_tasks_job_id", "tasks")
    op.drop_index("ix_tasks_tenant_id", "tasks")
    op.drop_index("ix_messages_job_id", "messages")
    op.drop_index("ix_messages_tenant_id", "messages")

    # Drop tables
    op.drop_table("message_files")
    op.drop_table("job_files")
    op.drop_table("tasks")
    op.drop_table("messages")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS taskpriority")
    op.execute("DROP TYPE IF EXISTS taskstatus")
