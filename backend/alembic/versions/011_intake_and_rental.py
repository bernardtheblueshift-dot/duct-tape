"""Add job intake metadata and equipment rental fields

Revision ID: 011
Revises: 010
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Job source enum and intake fields
    op.execute("CREATE TYPE jobsource AS ENUM ('direct', 'email', 'phone', 'referral', 'website', 'other')")
    op.add_column("jobs", sa.Column("source", sa.Enum('direct', 'email', 'phone', 'referral', 'website', 'other', name='jobsource'), nullable=True))
    op.add_column("jobs", sa.Column("contact_name", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("contact_email", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("contact_phone", sa.String(), nullable=True))

    # Equipment ownership enum and rental fields
    op.execute("CREATE TYPE ownershiptype AS ENUM ('owned', 'rented')")
    op.add_column("equipment", sa.Column("ownership", sa.Enum('owned', 'rented', name='ownershiptype'), nullable=False, server_default='owned'))
    op.add_column("equipment", sa.Column("rental_vendor", sa.String(), nullable=True))
    op.add_column("equipment", sa.Column("rental_cost_per_day", sa.Float(), nullable=True))
    op.add_column("equipment", sa.Column("rental_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column("equipment", sa.Column("rental_end", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("equipment", "rental_end")
    op.drop_column("equipment", "rental_start")
    op.drop_column("equipment", "rental_cost_per_day")
    op.drop_column("equipment", "rental_vendor")
    op.drop_column("equipment", "ownership")
    op.execute("DROP TYPE ownershiptype")
    op.drop_column("jobs", "contact_phone")
    op.drop_column("jobs", "contact_email")
    op.drop_column("jobs", "contact_name")
    op.drop_column("jobs", "source")
    op.execute("DROP TYPE jobsource")
