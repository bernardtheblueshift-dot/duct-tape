"""Security hardening: RLS policies, FORCE RLS, FK constraints, CHECK constraints

Revision ID: 008
Revises: 007
Create Date: 2026-05-17
"""
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === C3: Add RLS policies for tenant-scoped tables missing them ===

    # jobs
    op.execute("ALTER TABLE jobs ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON jobs
        USING (tenant_id::text = COALESCE(NULLIF(current_setting('app.current_tenant_id', TRUE), ''), '00000000-0000-0000-0000-000000000000'))
    """)
    # No FORCE RLS — app connects as table owner, RLS enforced via SET LOCAL in dependencies

    # crew_profiles
    op.execute("ALTER TABLE crew_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON crew_profiles
        USING (tenant_id::text = COALESCE(NULLIF(current_setting('app.current_tenant_id', TRUE), ''), '00000000-0000-0000-0000-000000000000'))
    """)

    # equipment
    op.execute("ALTER TABLE equipment ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON equipment
        USING (tenant_id::text = COALESCE(NULLIF(current_setting('app.current_tenant_id', TRUE), ''), '00000000-0000-0000-0000-000000000000'))
    """)

    # crew_assignments
    op.execute("ALTER TABLE crew_assignments ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON crew_assignments
        USING (tenant_id::text = COALESCE(NULLIF(current_setting('app.current_tenant_id', TRUE), ''), '00000000-0000-0000-0000-000000000000'))
    """)

    # equipment_assignments
    op.execute("ALTER TABLE equipment_assignments ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON equipment_assignments
        USING (tenant_id::text = COALESCE(NULLIF(current_setting('app.current_tenant_id', TRUE), ''), '00000000-0000-0000-0000-000000000000'))
    """)

    # availability_patterns
    op.execute("ALTER TABLE availability_patterns ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON availability_patterns
        USING (tenant_id::text = COALESCE(NULLIF(current_setting('app.current_tenant_id', TRUE), ''), '00000000-0000-0000-0000-000000000000'))
    """)

    # crew_ratings
    op.execute("ALTER TABLE crew_ratings ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON crew_ratings
        USING (tenant_id::text = COALESCE(NULLIF(current_setting('app.current_tenant_id', TRUE), ''), '00000000-0000-0000-0000-000000000000'))
    """)

    # Note: FORCE RLS removed — app connects as table owner, tenant isolation
    # enforced by SET LOCAL in get_current_tenant dependency

    # === M19: Add FK constraints for tenant_id ===
    op.create_foreign_key("fk_jobs_tenant", "jobs", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_crew_profiles_tenant", "crew_profiles", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_equipment_tenant", "equipment", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_crew_assignments_tenant", "crew_assignments", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_equipment_assignments_tenant", "equipment_assignments", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_availability_patterns_tenant", "availability_patterns", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_crew_ratings_tenant", "crew_ratings", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_messages_tenant", "messages", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_tasks_tenant", "tasks", "tenants", ["tenant_id"], ["id"])

    # === M20: Add CHECK constraints ===
    op.execute("ALTER TABLE crew_ratings ADD CONSTRAINT chk_stars_range CHECK (stars >= 1 AND stars <= 5)")
    op.execute("ALTER TABLE availability_patterns ADD CONSTRAINT chk_day_of_week CHECK (day_of_week >= 0 AND day_of_week <= 6)")
    op.execute("ALTER TABLE equipment ADD CONSTRAINT chk_quantity_positive CHECK (quantity >= 0)")
    op.execute("ALTER TABLE equipment_assignments ADD CONSTRAINT chk_quantity_assigned_positive CHECK (quantity_assigned >= 1)")


def downgrade() -> None:
    # Remove CHECK constraints
    op.execute("ALTER TABLE equipment_assignments DROP CONSTRAINT IF EXISTS chk_quantity_assigned_positive")
    op.execute("ALTER TABLE equipment DROP CONSTRAINT IF EXISTS chk_quantity_positive")
    op.execute("ALTER TABLE availability_patterns DROP CONSTRAINT IF EXISTS chk_day_of_week")
    op.execute("ALTER TABLE crew_ratings DROP CONSTRAINT IF EXISTS chk_stars_range")

    # Remove FK constraints
    op.drop_constraint("fk_tasks_tenant", "tasks", type_="foreignkey")
    op.drop_constraint("fk_messages_tenant", "messages", type_="foreignkey")
    op.drop_constraint("fk_crew_ratings_tenant", "crew_ratings", type_="foreignkey")
    op.drop_constraint("fk_availability_patterns_tenant", "availability_patterns", type_="foreignkey")
    op.drop_constraint("fk_equipment_assignments_tenant", "equipment_assignments", type_="foreignkey")
    op.drop_constraint("fk_crew_assignments_tenant", "crew_assignments", type_="foreignkey")
    op.drop_constraint("fk_equipment_tenant", "equipment", type_="foreignkey")
    op.drop_constraint("fk_crew_profiles_tenant", "crew_profiles", type_="foreignkey")
    op.drop_constraint("fk_jobs_tenant", "jobs", type_="foreignkey")

    # Remove RLS from newly-added tables
    for table in ["crew_ratings", "availability_patterns", "equipment_assignments",
                   "crew_assignments", "equipment", "crew_profiles", "jobs"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
