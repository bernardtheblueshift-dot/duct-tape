"""Seed database with realistic event production data for testing."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from app.database import engine, AsyncSessionLocal as async_session
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.job import Job, JobState, JobSource
from app.models.crew_profile import CrewProfile
from app.models.equipment import Equipment, EquipmentCondition, OwnershipType
from app.models.assignment import CrewAssignment, EquipmentAssignment, AssignmentState
from app.models.availability import AvailabilityPattern
from app.models.rating import CrewRating
from app.models.message import Message
from app.models.task import Task, TaskStatus, TaskPriority
from app.core.security import hash_password


async def seed():
    # Reset DB
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(timezone.utc)

    async with async_session() as db:
        # === TENANT ===
        tenant = Tenant(id=uuid4(), name="Blue Shift Productions")
        db.add(tenant)
        await db.flush()
        tid = tenant.id

        # === USERS ===
        admin = User(
            id=uuid4(), email="admin@gt.dev", name="Admin",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN, is_active=True, tenant_id=tid,
        )
        crew_users = []
        crew_data = [
            ("kenji@gt.dev", "Kenji Tanaka"),
            ("yuki@gt.dev", "Yuki Sato"),
            ("mari@gt.dev", "Mari Yamamoto"),
            ("takeshi@gt.dev", "Takeshi Nakamura"),
            ("aya@gt.dev", "Aya Watanabe"),
            ("ryo@gt.dev", "Ryo Suzuki"),
            ("hana@gt.dev", "Hana Kobayashi"),
        ]
        for email, name in crew_data:
            u = User(
                id=uuid4(), email=email, name=name,
                hashed_password=hash_password("crew123"),
                role=UserRole.CREW, is_active=True, tenant_id=tid,
            )
            crew_users.append(u)

        db.add(admin)
        for u in crew_users:
            db.add(u)
        await db.flush()

        # === CREW PROFILES ===
        profiles_data = [
            (crew_users[0], "+81-90-1234-5678", "Camera operator, 8 years experience", 450, ["Camera Op", "Steadicam", "Drone"], 4.8, 12),
            (crew_users[1], "+81-90-2345-6789", "Sound engineer, specializes in live events", 400, ["Sound", "Live Mix", "RF Tech"], 4.5, 9),
            (crew_users[2], "+81-90-3456-7890", "Lighting designer and operator", 420, ["Lighting", "Programming", "Rigging"], 4.9, 15),
            (crew_users[3], "+81-80-4567-8901", "Stage manager and floor director", 380, ["Stage Manager", "Floor Director", "Cueing"], 4.2, 7),
            (crew_users[4], "+81-80-5678-9012", "Graphics operator and VJ", 350, ["Graphics", "Resolume", "vMix"], 4.6, 11),
            (crew_users[5], "+81-90-6789-0123", "Video engineer and streaming tech", 430, ["Video Engineer", "Streaming", "Camera Op"], 4.7, 8),
            (crew_users[6], "+81-80-7890-1234", "Production assistant, versatile", 300, ["PA", "Runner", "Setup"], 4.0, 5),
        ]
        profiles = []
        for user, phone, bio, rate, skills, rating, count in profiles_data:
            p = CrewProfile(
                id=uuid4(), user_id=user.id, phone=phone, bio=bio,
                hourly_rate=rate, skills=skills, rating_average=rating, rating_count=count,
                tenant_id=tid,
            )
            profiles.append(p)
            db.add(p)
        await db.flush()

        # === AVAILABILITY (some crew unavailable certain days) ===
        # Kenji: unavailable Sundays
        db.add(AvailabilityPattern(id=uuid4(), crew_id=profiles[0].id, day_of_week=6, is_available=False, tenant_id=tid))
        # Mari: unavailable Mon+Tue
        db.add(AvailabilityPattern(id=uuid4(), crew_id=profiles[2].id, day_of_week=0, is_available=False, tenant_id=tid))
        db.add(AvailabilityPattern(id=uuid4(), crew_id=profiles[2].id, day_of_week=1, is_available=False, tenant_id=tid))
        # Hana: unavailable weekends
        db.add(AvailabilityPattern(id=uuid4(), crew_id=profiles[6].id, day_of_week=5, is_available=False, tenant_id=tid))
        db.add(AvailabilityPattern(id=uuid4(), crew_id=profiles[6].id, day_of_week=6, is_available=False, tenant_id=tid))

        # === EQUIPMENT ===
        # owned = (name, cat, qty, cond, notes, ownership, vendor, cost/day, rental_start, rental_end)
        equip_data = [
            ("Sony FX6", "Camera", 3, EquipmentCondition.GOOD, "S/N: FX6-001/002/003", OwnershipType.OWNED, None, None, None, None),
            ("Sennheiser EW-D", "Audio", 8, EquipmentCondition.GOOD, "Digital wireless mic kit", OwnershipType.OWNED, None, None, None, None),
            ("Yamaha CL3", "Audio", 1, EquipmentCondition.GOOD, "64-channel digital console", OwnershipType.OWNED, None, None, None, None),
            ("ETC Ion Xe", "Lighting", 2, EquipmentCondition.GOOD, "Lighting console", OwnershipType.OWNED, None, None, None, None),
            ("Barco UDX-4K32", "Video", 2, EquipmentCondition.GOOD, "32K lumen projector", OwnershipType.RENTED, "Hibino AV", 85000, now + timedelta(days=5), now + timedelta(days=8)),
            ("Blackmagic ATEM 4 M/E", "Video", 1, EquipmentCondition.GOOD, "Production switcher", OwnershipType.OWNED, None, None, None, None),
            ("Generic LED Wash", "Lighting", 24, EquipmentCondition.GOOD, "RGBW wash fixtures", OwnershipType.OWNED, None, None, None, None),
            ("Shure ULXD4Q", "Audio", 3, EquipmentCondition.GOOD, "Quad wireless receiver", OwnershipType.OWNED, None, None, None, None),
            ("Ross Carbonite Black+", "Video", 1, EquipmentCondition.FAIR, "2 M/E switcher - needs firmware update", OwnershipType.OWNED, None, None, None, None),
            ("Cable Trunk A", "Rigging", 4, EquipmentCondition.GOOD, "SDI/Power/DMX cable sets", OwnershipType.OWNED, None, None, None, None),
            ("Truss Section 3m", "Rigging", 12, EquipmentCondition.GOOD, "290mm box truss", OwnershipType.RENTED, "Stage Gear Tokyo", 12000, now + timedelta(days=19), now + timedelta(days=23)),
            ("Martin MAC Aura", "Lighting", 8, EquipmentCondition.POOR, "2 units need lamp replacement", OwnershipType.OWNED, None, None, None, None),
            ("Christie D4K40-RGB", "Video", 1, EquipmentCondition.GOOD, "40K lumen laser projector - rented for Nova launch", OwnershipType.RENTED, "Visual Solutions Inc", 150000, now + timedelta(days=6), now + timedelta(days=8)),
            ("L-Acoustics K2", "Audio", 12, EquipmentCondition.GOOD, "Line array for summer festival", OwnershipType.RENTED, "Sound Pro Rentals", 45000, now + timedelta(days=20), now + timedelta(days=23)),
        ]
        equips = []
        for name, cat, qty, cond, notes, ownership, vendor, cost, r_start, r_end in equip_data:
            e = Equipment(
                id=uuid4(), name=name, category=cat, quantity=qty,
                condition=cond, notes=notes, ownership=ownership,
                rental_vendor=vendor, rental_cost_per_day=cost,
                rental_start=r_start, rental_end=r_end, tenant_id=tid,
            )
            equips.append(e)
            db.add(e)
        await db.flush()

        # === JOBS ===
        jobs_data = [
            # Active jobs
            ("Q2 All-Hands", "Company quarterly meeting with keynote and breakout sessions",
             "Tokyo Midtown Hall", JobState.ACTIVE,
             now + timedelta(days=3, hours=9), now + timedelta(days=3, hours=17),
             JobSource.DIRECT, "Tanaka Hiroshi", "tanaka@acmecorp.jp", None),
            ("Product Launch: Project Nova", "New product unveiling with live demo and press conference",
             "Roppongi Hills Arena", JobState.ACTIVE,
             now + timedelta(days=7, hours=10), now + timedelta(days=7, hours=16),
             JobSource.EMAIL, "Sarah Chen", "sarah@novainc.com", "+81-3-1234-5678"),
            # Simmering
            ("Summer Festival Stage", "Main stage production for annual summer festival",
             "Odaiba Marine Park", JobState.SIMMER,
             now + timedelta(days=21, hours=11), now + timedelta(days=22, hours=22),
             JobSource.REFERRAL, "Yamada Productions", "info@yamada-prod.co.jp", None),
            ("Board Meeting Webcast", "Quarterly board meeting with remote attendees via stream",
             "Main Conference Room", JobState.SIMMER,
             now + timedelta(days=14, hours=14), now + timedelta(days=14, hours=16),
             JobSource.DIRECT, None, None, None),
            # Intake
            ("Client Dinner: Acme Corp", "Intimate dinner event with ambient AV",
             "Palace Hotel Tokyo", JobState.INTAKE,
             now + timedelta(days=30, hours=18), now + timedelta(days=30, hours=22),
             JobSource.PHONE, "Suzuki Mika", None, "+81-90-8765-4321"),
            ("Training Video Shoot", "3-day corporate training video production",
             "Studio A, Shibuya", JobState.INTAKE,
             now + timedelta(days=28, hours=9), now + timedelta(days=30, hours=18),
             JobSource.WEBSITE, "Mike Johnson", "mike.j@globalcorp.com", None),
            # Completed
            ("FY26 Kickoff", "Annual company kickoff with live performances",
             "Tokyo International Forum", JobState.COMPLETE,
             now - timedelta(days=5, hours=8), now - timedelta(days=5),
             JobSource.DIRECT, None, None, None),
            ("Press Conference: Q1 Results", "Financial results announcement with Q&A",
             "HQ Press Room", JobState.COMPLETE,
             now - timedelta(days=12, hours=6), now - timedelta(days=12, hours=2),
             JobSource.EMAIL, "PR Team", "pr@client.co.jp", None),
        ]
        jobs = []
        for title, desc, venue, state, start, end, source, c_name, c_email, c_phone in jobs_data:
            j = Job(
                id=uuid4(), title=title, description=desc, venue=venue,
                state=state, scheduled_start=start, scheduled_end=end,
                source=source, contact_name=c_name, contact_email=c_email,
                contact_phone=c_phone, tenant_id=tid,
            )
            jobs.append(j)
            db.add(j)
        await db.flush()

        # === CREW ASSIGNMENTS ===
        assignments = [
            # Q2 All-Hands (active) - full crew
            (profiles[0], jobs[0], "Lead Camera", AssignmentState.CONFIRMED),
            (profiles[1], jobs[0], "Sound Engineer", AssignmentState.CONFIRMED),
            (profiles[2], jobs[0], "Lighting Op", AssignmentState.CONFIRMED),
            (profiles[3], jobs[0], "Stage Manager", AssignmentState.CONFIRMED),
            (profiles[4], jobs[0], "Graphics Op", AssignmentState.PENDING),
            # Product Launch (active)
            (profiles[0], jobs[1], "Camera Op", AssignmentState.CONFIRMED),
            (profiles[5], jobs[1], "Video Engineer", AssignmentState.CONFIRMED),
            (profiles[2], jobs[1], "Lighting Designer", AssignmentState.CONFIRMED),
            (profiles[6], jobs[1], "PA", AssignmentState.DECLINED),
            # Summer Festival (simmer)
            (profiles[3], jobs[2], "Stage Manager", AssignmentState.PENDING),
            (profiles[1], jobs[2], "FOH Sound", AssignmentState.PENDING),
            # Board Meeting (simmer)
            (profiles[5], jobs[3], "Streaming Tech", AssignmentState.CONFIRMED),
            # FY26 Kickoff (complete)
            (profiles[0], jobs[6], "Lead Camera", AssignmentState.CONFIRMED),
            (profiles[1], jobs[6], "Sound", AssignmentState.CONFIRMED),
            (profiles[2], jobs[6], "Lighting", AssignmentState.CONFIRMED),
            (profiles[3], jobs[6], "Stage Manager", AssignmentState.CONFIRMED),
            (profiles[4], jobs[6], "Graphics", AssignmentState.CONFIRMED),
            (profiles[5], jobs[6], "Video Engineer", AssignmentState.CONFIRMED),
        ]
        for profile, job, role, status in assignments:
            db.add(CrewAssignment(
                id=uuid4(), crew_id=profile.id, job_id=job.id,
                role=role, status=status, tenant_id=tid,
            ))

        # === EQUIPMENT ASSIGNMENTS ===
        eq_assignments = [
            (equips[0], jobs[0], 2),   # 2x Sony FX6 for All-Hands
            (equips[1], jobs[0], 4),   # 4x wireless mics
            (equips[2], jobs[0], 1),   # CL3 console
            (equips[6], jobs[0], 12),  # 12x LED wash
            (equips[0], jobs[1], 1),   # 1x FX6 for launch
            (equips[4], jobs[1], 2),   # 2x projectors
            (equips[5], jobs[1], 1),   # ATEM switcher
            (equips[1], jobs[1], 3),   # 3x wireless
            (equips[3], jobs[3], 1),   # Ion Xe for board meeting
        ]
        for equip, job, qty in eq_assignments:
            db.add(EquipmentAssignment(
                id=uuid4(), equipment_id=equip.id, job_id=job.id,
                quantity_assigned=qty, tenant_id=tid,
            ))

        # === MESSAGES ===
        msg_data = [
            # Q2 All-Hands thread
            (admin, jobs[0], "Team - confirming the AV setup call for Monday. Please review the floor plan I shared.", None),
            (crew_users[3], jobs[0], "Floor plan looks good. Can we add a second confidence monitor for the breakout room?", None),
            (admin, jobs[0], "Good call. Adding it to the equipment list. @Kenji - can you bring the extra FX6?", None),
            (crew_users[0], jobs[0], "Yep, I'll bring it. Do we have the wide-angle lens adapter?", None),
            (crew_users[1], jobs[0], "Sound check needs to happen by 8am. The venue has a hard noise curfew at 6pm.", None),
            (admin, jobs[0], "Noted. Let's push call time to 7:30am then.", None),
            # Product Launch thread
            (admin, jobs[1], "This is a high-profile launch. Client wants cinema-quality opening sequence.", None),
            (crew_users[5], jobs[1], "I've prepared a streaming test plan. Can we get access to the venue Thursday for a dry run?", None),
            (admin, jobs[1], "Confirmed - venue access Thursday 2pm-6pm for tech check.", None),
            (crew_users[2], jobs[1], "Lighting rig design is ready. Going with a blend of front wash and dynamic side lighting for the demo moments.", None),
        ]
        messages = []
        for user, job, content, reply_to in msg_data:
            m = Message(
                id=uuid4(), job_id=job.id, user_id=user.id,
                content=content, reply_to_id=reply_to, tenant_id=tid,
            )
            messages.append(m)
            db.add(m)
        await db.flush()

        # === TASKS ===
        tasks_data = [
            # Q2 All-Hands
            (jobs[0], "Prepare floor plan PDF", profiles[3], TaskStatus.DONE, TaskPriority.HIGH, now - timedelta(days=2), None),
            (jobs[0], "Configure CL3 scene file", profiles[1], TaskStatus.IN_PROGRESS, TaskPriority.HIGH, now + timedelta(days=2), None),
            (jobs[0], "Test projector signal chain", profiles[4], TaskStatus.TODO, TaskPriority.MEDIUM, now + timedelta(days=2), None),
            (jobs[0], "Print crew call sheets", None, TaskStatus.TODO, TaskPriority.LOW, now + timedelta(days=2), None),
            (jobs[0], "Book parking for load-in truck", None, TaskStatus.DONE, TaskPriority.URGENT, now - timedelta(days=1), None),
            # Product Launch
            (jobs[1], "Design opening sequence graphics", profiles[4], TaskStatus.IN_PROGRESS, TaskPriority.URGENT, now + timedelta(days=5), None),
            (jobs[1], "Prepare streaming encoder config", profiles[5], TaskStatus.TODO, TaskPriority.HIGH, now + timedelta(days=6), None),
            (jobs[1], "Create rehearsal schedule", profiles[3], TaskStatus.TODO, TaskPriority.MEDIUM, now + timedelta(days=4), None),
            (jobs[1], "Coordinate with venue AV team", None, TaskStatus.IN_PROGRESS, TaskPriority.HIGH, now + timedelta(days=3), messages[7]),
        ]
        for job, title, assignee, status, priority, deadline, msg in tasks_data:
            db.add(Task(
                id=uuid4(), job_id=job.id, title=title,
                assignee_id=assignee.id if assignee else None,
                status=status, priority=priority, deadline=deadline,
                message_id=msg.id if msg else None, tenant_id=tid,
            ))

        # === CREW RATINGS (for completed job) ===
        for i, profile in enumerate(profiles[:6]):
            db.add(CrewRating(
                id=uuid4(), crew_id=profile.id, job_id=jobs[6].id,
                rated_by=admin.id, stars=4 + (i % 2), notes=None, tenant_id=tid,
            ))

        await db.commit()

    # Re-apply RLS policies (create_all doesn't include these)
    async with engine.begin() as conn:
        policy_tables = [
            'jobs', 'crew_profiles', 'equipment', 'crew_assignments',
            'equipment_assignments', 'availability_patterns', 'crew_ratings',
            'users', 'invitation_tokens', 'ical_tokens', 'messages', 'tasks',
            'job_files', 'message_last_seen',
        ]
        for t in policy_tables:
            await conn.execute(text(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY"))
            await conn.execute(text(f"DROP POLICY IF EXISTS tenant_isolation ON {t}"))
            await conn.execute(text(f"""
                CREATE POLICY tenant_isolation ON {t}
                USING (tenant_id::text = COALESCE(NULLIF(current_setting('app.current_tenant_id', TRUE), ''), '00000000-0000-0000-0000-000000000000'))
            """))
        print("RLS policies applied.")

    print("Seed complete!")
    print()
    print("Login credentials:")
    print("  Admin: admin@gt.dev / admin123")
    print("  Crew:  kenji@gt.dev / crew123  (or any crew email)")
    print()
    print(f"  Tenant: Blue Shift Productions")
    print(f"  Jobs: {len(jobs_data)} (2 active, 2 simmer, 2 intake, 2 complete)")
    print(f"  Crew: {len(crew_data)}")
    rented = sum(1 for *_, o, _, _, _, _ in equip_data if o == OwnershipType.RENTED)
    print(f"  Equipment: {len(equip_data)} items ({rented} rented)")
    print(f"  Assignments: {len(assignments)} crew + {len(eq_assignments)} equipment")
    print(f"  Messages: {len(msg_data)}")
    print(f"  Tasks: {len(tasks_data)}")


asyncio.run(seed())
