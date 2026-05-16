# Phase 5: Coordination Layer (Messaging + Tasks + Files) - Research

**Researched:** 2026-05-16
**Domain:** Real-time messaging (WebSockets), task management, file upload/storage
**Confidence:** HIGH

## Summary

Phase 5 implements three interconnected collaboration features: job-scoped messaging with real-time WebSocket delivery, task management with state workflows, and file storage with tenant isolation. All three features share common patterns from existing phases (TenantMixin, state machines, CRUD routers) while introducing new infrastructure (WebSocket connection management, file serving endpoints, many-to-many relationships).

**Key technical challenges:**
- WebSocket connection lifecycle (authentication, subscription routing, heartbeat, cleanup)
- File upload security (tenant isolation, MIME validation, storage organization)
- Cross-feature integration (messages ↔ files, tasks ↔ messages)
- JobResponse enrichment (summary counts + recent items without N+1 queries)

**Primary recommendation:** Follow existing codebase patterns religiously. Use TenantMixin/TimestampMixin on all new models, reuse state_machine.py for task status transitions, batch queries for JobResponse summary data (Phase 3/4 pattern), and JWT authentication for WebSocket connections (matches existing auth). FastAPI's native WebSocket support is production-ready; no external libraries needed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Messaging model & WebSockets**
- Flat message list with optional reply_to_id (parent message reference) — not nested threads
- Messages stored as markdown text, frontend renders formatting
- Single multiplexed WebSocket connection per user — client subscribes to job IDs, server routes messages to matching subscriptions
- JWT token in WebSocket connection query param for authentication
- ILIKE search on message content within a job (same pattern as jobs/crew search)
- WebSocket delivers messages only (not task or file events) for v1

**Task workflow & permissions**
- Admin creates tasks and sets assignees — crew cannot create tasks
- Both admin and assigned crew can update task status
- State machine: todo → in_progress → done, with backward transitions allowed (done→in_progress to reopen, in_progress→todo to deprioritize)
- Follows existing state_machine.py pattern from Phase 2
- Optional message_id FK on task — links task to the message that prompted it (one-to-one)
- Deadline is informational TIMESTAMPTZ field — no auto-escalation, no background jobs
- Priority levels: low, medium, high, urgent (enum)

**File storage & upload**
- Local filesystem storage, organized by tenant_id/job_id/ directory structure
- 100MB per file upload limit
- Backend serves files via authenticated endpoint — frontend handles preview rendering (img tags, pdf.js)
- No server-side thumbnail generation for v1
- Hard delete — removes both DB record and file on disk
- Upload metadata tracked: uploader (user_id), upload timestamp, original filename, file size, MIME type

**Cross-feature integration**
- Messages can reference files via optional file_ids (many-to-many — a message can attach multiple files)
- Tasks reference messages via optional message_id FK (one-to-one)
- JobResponse shows summary counts + recent items: message_count, unread_count, latest 3 messages; task counts by status, overdue count; file_count, latest 3 files
- Full lists of messages/tasks/files via separate per-job endpoints

### Claude's Discretion

- WebSocket connection management (heartbeat, reconnection strategy)
- File MIME type validation (allowed types list)
- Message pagination strategy (cursor vs offset)
- Task sorting/filtering options on the list endpoint
- File directory structure details (date subdirectories, UUID filenames)
- How to handle file_ids validation when attaching files to messages

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MSG-01 | Threaded messaging per job (Slack-like channels scoped to each job) | WebSocket architecture, reply_to_id pattern, FastAPI WebSocket endpoints |
| MSG-02 | Messages support text with basic formatting | Markdown storage pattern, frontend rendering guidance |
| MSG-03 | Message history is searchable within a job | ILIKE search pattern (existing jobs/crew pattern reusable) |
| MSG-04 | Real-time message delivery via WebSockets | Connection manager pattern, subscription routing, JWT auth in query params |
| TASK-01 | Admin can create tasks linked to a job | Task model with job_id FK, admin-only creation endpoints |
| TASK-02 | Tasks have assignee, deadline, priority, and status | TaskPriority enum, TaskStatus enum, optional assignee (crew_id FK), TIMESTAMPTZ deadline |
| TASK-03 | Task status workflow: todo → in_progress → done | State machine pattern (TASK_TRANSITIONS dict), validate_transition reuse |
| TASK-04 | Crew can view and update tasks assigned to them | Permission checks (require_admin OR task.assignee_id == current_user.crew_id) |
| TASK-05 | Tasks can reference messages for context | Optional message_id FK (one-to-one), nullable for tasks created without message context |
| FILE-01 | Users can upload files to a job (briefs, runsheets, photos, videos, docs) | FastAPI File upload, filesystem storage in uploads/{tenant_id}/{job_id}/ |
| FILE-02 | File preview for images and PDFs | Serve files with correct Content-Type, frontend handles img/pdf.js rendering |
| FILE-03 | Files are organized per job with upload metadata | JobFile model with uploader_id, original_filename, file_size, mime_type, storage_path |
| FILE-04 | Secure file storage with tenant isolation | Tenant-scoped directory structure, authenticated file serving endpoint validates tenant access |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.136.1 | WebSocket endpoints, file uploads | Native WebSocket support via Starlette, multipart form handling, production-ready |
| Uvicorn | 0.47.0 | ASGI server | Already in use, handles WebSocket connections efficiently |
| SQLAlchemy | 2.0.49 | ORM for new models | Existing project standard, async support for batch queries |
| Pydantic | 2.13.4 | Schema validation | Already in use, v2 performance, file upload validation |
| python-multipart | 0.0.28 | File upload parsing | Required for FastAPI File/UploadFile, already in dependencies |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiofiles | 0.24.0+ | Async file I/O | Writing uploaded files to disk without blocking event loop |
| python-magic | 0.4.27+ | MIME type detection | Validate file type beyond client-provided header (security) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI WebSocket | Socket.IO (python-socketio) | Socket.IO adds fallback transports and rooms but increases complexity; FastAPI WebSocket sufficient for v1 |
| Local filesystem | S3/MinIO object storage | Object storage better for scale but adds deployment complexity; local storage simpler for v1, can migrate later |
| Markdown text | Rich text JSON (Slate/ProseMirror) | Structured JSON enables advanced features but increases frontend complexity; markdown sufficient for v1 |

**Installation:**
```bash
cd backend
# Add to pyproject.toml dependencies:
# aiofiles==0.24.0
# python-magic==0.4.27

uv pip install aiofiles python-magic
```

**Version verification:**
```bash
# Core libraries already installed and verified
python3 -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"  # 0.136.1
python3 -c "import pydantic; print(f'Pydantic {pydantic.__version__}')"  # 2.13.4
python3 -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}')"  # 2.0.49

# New dependencies (after installation)
python3 -c "import aiofiles; print(f'aiofiles {aiofiles.__version__}')"
python3 -c "import magic; print('python-magic installed')"
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── models/
│   ├── message.py           # Message model with reply_to_id, job_id FK
│   ├── task.py              # Task model with state machine enums
│   ├── file.py              # JobFile model with storage metadata
│   └── message_file.py      # Many-to-many link table (message_id, file_id)
├── schemas/
│   ├── message.py           # MessageCreate, MessageResponse, MessageWithReplies
│   ├── task.py              # TaskCreate, TaskUpdate, TaskResponse
│   └── file.py              # FileUploadResponse, FileResponse
├── api/v1/
│   ├── messages.py          # REST endpoints: POST, GET /jobs/{job_id}/messages
│   ├── tasks.py             # REST endpoints: CRUD + status transition
│   ├── files.py             # Upload endpoint, list endpoint, serve endpoint
│   └── websocket.py         # WebSocket endpoint + connection manager
├── core/
│   ├── websocket_manager.py # ConnectionManager class with subscription routing
│   ├── file_storage.py      # File save/delete helpers, path generation
│   └── task_state.py        # TASK_TRANSITIONS dict + validation (follows state_machine.py)
└── uploads/                  # Git-ignored, created at runtime
    └── {tenant_id}/
        └── {job_id}/
            └── {uuid}.{ext}  # UUID-named files preserve extension
```

### Pattern 1: WebSocket Connection Manager
**What:** Centralized manager tracks active connections, maps user_id → WebSocket, subscription_set (job IDs)
**When to use:** All WebSocket connection lifecycle events (connect, disconnect, send, broadcast)
**Example:**
```python
# backend/app/core/websocket_manager.py
from fastapi import WebSocket
from typing import Dict, Set
import json

class ConnectionManager:
    """Manages WebSocket connections and job subscriptions"""
    
    def __init__(self):
        # user_id → WebSocket
        self.connections: Dict[str, WebSocket] = {}
        # user_id → Set[job_id]
        self.subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept connection and initialize subscriptions"""
        await websocket.accept()
        self.connections[user_id] = websocket
        self.subscriptions[user_id] = set()
    
    def disconnect(self, user_id: str):
        """Remove connection and subscriptions"""
        self.connections.pop(user_id, None)
        self.subscriptions.pop(user_id, None)
    
    async def subscribe(self, user_id: str, job_id: str):
        """Add job to user's subscription set"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].add(job_id)
    
    async def unsubscribe(self, user_id: str, job_id: str):
        """Remove job from user's subscription set"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].discard(job_id)
    
    async def broadcast_to_job(self, job_id: str, message: dict):
        """Send message to all users subscribed to job"""
        disconnected = []
        for user_id, job_set in self.subscriptions.items():
            if job_id in job_set:
                websocket = self.connections.get(user_id)
                if websocket:
                    try:
                        await websocket.send_json(message)
                    except Exception:
                        disconnected.append(user_id)
        
        # Clean up dead connections
        for user_id in disconnected:
            self.disconnect(user_id)

# Global singleton
manager = ConnectionManager()
```

### Pattern 2: WebSocket Endpoint with JWT Authentication
**What:** WebSocket endpoint authenticates via JWT in query param, handles subscription protocol
**When to use:** Single WebSocket endpoint at /ws
**Example:**
```python
# backend/app/api/v1/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.websocket_manager import manager
from app.core.auth import decode_jwt  # Reuse existing JWT decode
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint with JWT authentication.
    
    Query param: token (JWT from existing auth flow)
    
    Client protocol:
    - Send: {"action": "subscribe", "job_id": "uuid"}
    - Send: {"action": "unsubscribe", "job_id": "uuid"}
    - Receive: {"type": "message", "data": {...}}
    """
    # Authenticate via JWT in query param
    try:
        payload = decode_jwt(token)
        user_id = payload.get("user_id")
    except Exception:
        await websocket.close(code=1008)  # Policy violation
        return
    
    # Accept connection
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            # Receive subscription commands from client
            data = await websocket.receive_json()
            action = data.get("action")
            job_id = data.get("job_id")
            
            if action == "subscribe" and job_id:
                await manager.subscribe(user_id, job_id)
            elif action == "unsubscribe" and job_id:
                await manager.unsubscribe(user_id, job_id)
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
```

### Pattern 3: Message Broadcasting After REST POST
**What:** REST endpoint creates message in DB, then broadcasts to WebSocket subscribers
**When to use:** POST /api/v1/jobs/{job_id}/messages endpoint
**Example:**
```python
# backend/app/api/v1/messages.py
from app.core.websocket_manager import manager
from app.schemas.message import MessageResponse

@router.post("/{job_id}/messages", response_model=MessageResponse)
async def create_message(
    job_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create message and broadcast to WebSocket subscribers"""
    # Create message in database
    message = Message(
        **message_data.model_dump(),
        job_id=job_id,
        user_id=current_user.id,
        tenant_id=tenant_id,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    # Broadcast to WebSocket subscribers
    await manager.broadcast_to_job(
        str(job_id),
        {
            "type": "message",
            "data": MessageResponse.model_validate(message).model_dump(),
        }
    )
    
    return message
```

### Pattern 4: File Upload with Tenant Isolation
**What:** Multipart upload saves to tenant/job directory, validates MIME type, stores metadata
**When to use:** POST /api/v1/jobs/{job_id}/files endpoint
**Example:**
```python
# backend/app/core/file_storage.py
from pathlib import Path
import aiofiles
import uuid
import magic

UPLOAD_DIR = Path("uploads")
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "video/mp4", "video/quicktime",
}

def get_upload_path(tenant_id: str, job_id: str, file_id: str, extension: str) -> Path:
    """Generate filesystem path for uploaded file"""
    return UPLOAD_DIR / tenant_id / job_id / f"{file_id}{extension}"

async def save_upload(
    tenant_id: str,
    job_id: str,
    file: UploadFile,
    max_size: int = 100 * 1024 * 1024  # 100MB
) -> tuple[Path, str, int]:
    """
    Save uploaded file to tenant/job directory.
    
    Returns: (storage_path, mime_type, file_size)
    Raises: ValueError if MIME type invalid or file too large
    """
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > max_size:
        raise ValueError(f"File exceeds {max_size} byte limit")
    
    # Detect MIME type from content (security: don't trust client)
    mime = magic.from_buffer(content, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"File type {mime} not allowed")
    
    # Generate storage path
    file_id = str(uuid.uuid4())
    extension = Path(file.filename).suffix if file.filename else ""
    storage_path = get_upload_path(tenant_id, job_id, file_id, extension)
    
    # Create directory if needed
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    async with aiofiles.open(storage_path, 'wb') as f:
        await f.write(content)
    
    return storage_path, mime, file_size

async def delete_file(storage_path: Path):
    """Delete file from filesystem"""
    if storage_path.exists():
        storage_path.unlink()
```

### Pattern 5: Authenticated File Serving
**What:** Endpoint serves files after validating tenant access via RLS
**When to use:** GET /api/v1/files/{file_id} endpoint
**Example:**
```python
# backend/app/api/v1/files.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.models.file import JobFile

@router.get("/{file_id}")
async def serve_file(
    file_id: UUID,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Serve file with tenant access validation"""
    # Query file metadata (RLS ensures tenant match)
    result = await db.execute(
        select(JobFile).where(JobFile.id == file_id)
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Serve file with correct MIME type
    return FileResponse(
        path=file_record.storage_path,
        media_type=file_record.mime_type,
        filename=file_record.original_filename,
    )
```

### Pattern 6: Task State Machine (Reuses state_machine.py Pattern)
**What:** Enum-based state transitions with validation, backward transitions allowed
**When to use:** Task status updates via PATCH /api/v1/tasks/{task_id}/status
**Example:**
```python
# backend/app/core/task_state.py
from app.models.task import TaskStatus

TASK_TRANSITIONS = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.DONE],
    TaskStatus.IN_PROGRESS: [TaskStatus.TODO, TaskStatus.DONE],
    TaskStatus.DONE: [TaskStatus.IN_PROGRESS],  # Reopen
}

def can_transition(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    """Check if status transition is allowed"""
    allowed = TASK_TRANSITIONS.get(from_status, [])
    return to_status in allowed

def validate_transition(from_status: TaskStatus, to_status: TaskStatus) -> None:
    """Validate transition and raise ValueError if invalid"""
    if not can_transition(from_status, to_status):
        raise ValueError(f"Invalid transition: {from_status.value} -> {to_status.value}")
```

### Pattern 7: JobResponse Summary Enrichment (Batch Query Pattern)
**What:** Single query joins messages/tasks/files with jobs, aggregates counts + recent items
**When to use:** GET /api/v1/jobs and GET /api/v1/jobs/{id} endpoints
**Example:**
```python
# backend/app/api/v1/jobs.py (updated list_jobs)
from sqlalchemy import func, select
from app.models import Message, Task, JobFile

async def enrich_job_response(job: Job, db: AsyncSession) -> JobResponse:
    """Add message/task/file summary data to job"""
    # Message counts + recent 3
    msg_result = await db.execute(
        select(Message)
        .where(Message.job_id == job.id)
        .order_by(Message.created_at.desc())
        .limit(3)
    )
    recent_messages = msg_result.scalars().all()
    
    msg_count_result = await db.execute(
        select(func.count(Message.id))
        .where(Message.job_id == job.id)
    )
    message_count = msg_count_result.scalar()
    
    # Task counts by status
    task_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.job_id == job.id)
        .group_by(Task.status)
    )
    task_counts = dict(task_result.all())
    
    # File count + recent 3
    file_result = await db.execute(
        select(JobFile)
        .where(JobFile.job_id == job.id)
        .order_by(JobFile.created_at.desc())
        .limit(3)
    )
    recent_files = file_result.scalars().all()
    
    # Build response
    return JobResponse(
        **job.__dict__,
        messages=recent_messages,
        message_count=message_count,
        task_counts=task_counts,
        files=recent_files,
    )
```

### Anti-Patterns to Avoid

- **N+1 queries in JobResponse**: Don't load messages/tasks/files per-job in loop; use batch queries with joins or subqueries
- **Storing file content in PostgreSQL**: BYTEA columns waste database resources; use filesystem with metadata in DB
- **Trusting client MIME type**: Always validate file type via python-magic content inspection (client headers are spoofable)
- **Nested WebSocket broadcasts**: Don't await broadcasts in synchronous code; use fire-and-forget pattern
- **Exposing filesystem paths in API responses**: Return file_id and serve via authenticated endpoint, never expose /uploads/... paths

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MIME type detection | Parse file headers manually | python-magic (libmagic wrapper) | Handles 1000+ file types, security-tested, deals with malformed headers |
| WebSocket connection pooling | Custom connection tracker with locks | FastAPI WebSocket + dict-based manager | Built-in lifecycle hooks, no threading issues |
| File upload progress | Custom chunked upload protocol | FastAPI File/UploadFile | Handles multipart/form-data, memory-efficient streaming |
| Message threading UI | Recursive comment tree | Flat list with reply_to_id + frontend grouping | Simpler queries, avoids deep recursion, faster rendering |
| Real-time presence | Custom heartbeat protocol | Rely on WebSocket disconnect events | Browser handles connection state, no need to reinvent |

**Key insight:** FastAPI's WebSocket support is production-ready and battle-tested. The temptation to reach for Socket.IO or custom protocols adds deployment complexity (need Redis for Socket.IO rooms) without meaningful benefit at this scale. File uploads similarly don't need custom chunking — FastAPI's multipart handling is memory-efficient via streaming.

## Common Pitfalls

### Pitfall 1: WebSocket Authentication Timing
**What goes wrong:** Attempting to read JWT from WebSocket message after connection accepted
**Why it happens:** WebSocket handshake happens before any messages exchanged; can't authenticate mid-stream
**How to avoid:** Authenticate via query parameter during initial handshake (token passed in URL)
**Warning signs:** Client connects successfully but server rejects first message with auth error

### Pitfall 2: File Path Traversal
**What goes wrong:** User-provided filename contains ../ and writes outside upload directory
**Why it happens:** Trusting client-provided filename without sanitization
**How to avoid:** Generate UUID-based filenames server-side, only preserve extension from client filename
**Warning signs:** Files appearing in unexpected directories, security scanner warnings

### Pitfall 3: Orphaned Files After Database Failure
**What goes wrong:** File saved to disk, then database commit fails → file exists with no DB record
**Why it happens:** File I/O happens before transaction commit
**How to avoid:** Save file after database commit succeeds, OR implement cleanup job to remove orphaned files
**Warning signs:** Disk usage grows faster than database file count

### Pitfall 4: CORS Preflight Blocking WebSocket
**What goes wrong:** Browser blocks WebSocket connection from frontend to backend
**Why it happens:** WebSocket handshake is HTTP upgrade, subject to CORS policy
**How to avoid:** Ensure CORSMiddleware includes WebSocket origin in allow_origins
**Warning signs:** WebSocket connection fails in browser but curl works

### Pitfall 5: Forgetting Tenant Isolation on File Serving
**What goes wrong:** User from Tenant A requests file_id from Tenant B and receives it
**Why it happens:** File serving endpoint only checks file existence, not tenant match
**How to avoid:** Use RLS (SET LOCAL current_tenant_id) when querying JobFile metadata
**Warning signs:** Security audit finds cross-tenant file access

### Pitfall 6: Message Search Case Sensitivity
**What goes wrong:** Search for "Camera" doesn't find "camera" in message content
**Why it happens:** Using LIKE instead of ILIKE in PostgreSQL
**How to avoid:** Use ILIKE (case-insensitive) consistently, matching jobs/crew search pattern
**Warning signs:** User reports can't find messages they know exist

### Pitfall 7: Task Permission Edge Case
**What goes wrong:** Crew member can update tasks they're not assigned to
**Why it happens:** Permission check only validates "is admin OR is crew", not "is assigned crew"
**How to avoid:** Permission check must be: `require_admin OR (require_active AND task.assignee_id == current_user.crew_id)`
**Warning signs:** Crew members seeing "Update" buttons on all tasks

### Pitfall 8: WebSocket Memory Leak on Disconnect
**What goes wrong:** Disconnected WebSocket objects accumulate in memory
**Why it happens:** Not removing from ConnectionManager.connections on disconnect
**How to avoid:** Always call manager.disconnect() in except WebSocketDisconnect block
**Warning signs:** Memory usage grows over time, performance degrades

## Code Examples

Verified patterns from existing codebase and FastAPI documentation:

### WebSocket Client Protocol (Frontend)
```typescript
// Frontend WebSocket connection with JWT
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = () => {
  // Subscribe to job channel
  ws.send(JSON.stringify({
    action: 'subscribe',
    job_id: 'job-uuid-here'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'message') {
    // Handle new message
    console.log('New message:', data.data);
  }
};

// Heartbeat to detect dead connections
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'ping' }));
  }
}, 30000);  // Every 30 seconds
```

### Many-to-Many Message ↔ Files Association Table
```python
# backend/app/models/message_file.py
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

# Association table for message-file many-to-many
message_files = Table(
    'message_files',
    Base.metadata,
    Column('message_id', UUID(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE'), primary_key=True),
    Column('file_id', UUID(as_uuid=True), ForeignKey('job_files.id', ondelete='CASCADE'), primary_key=True),
)
```

### Message Model with Reply Threading
```python
# backend/app/models/message.py
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid

class Message(Base, TenantMixin, TimestampMixin):
    """Job-scoped message with optional threading via reply_to"""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)  # Markdown text
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    
    # Relationships
    files = relationship("JobFile", secondary="message_files", back_populates="messages")
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
```

### Task Model with State Machine
```python
# backend/app/models/task.py
from sqlalchemy import Column, String, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid
import enum

class TaskStatus(str, enum.Enum):
    """Task lifecycle states"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskPriority(str, enum.Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(Base, TenantMixin, TimestampMixin):
    """Job-scoped task with assignee and deadline"""
    
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("crew_profiles.id"), nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    deadline = Column(DateTime(timezone=True), nullable=True)  # Informational only
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
```

### File Upload Endpoint
```python
# backend/app/api/v1/files.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.core.file_storage import save_upload, delete_file
from app.models.file import JobFile
from app.schemas.file import FileUploadResponse

router = APIRouter(prefix="/api/v1/jobs/{job_id}/files", tags=["files"])

@router.post("/", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    job_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Upload file to job with tenant isolation"""
    try:
        # Save file to disk
        storage_path, mime_type, file_size = await save_upload(
            str(tenant_id), str(job_id), file
        )
        
        # Create database record
        file_record = JobFile(
            job_id=job_id,
            uploader_id=current_user.id,
            original_filename=file.filename,
            storage_path=str(storage_path),
            mime_type=mime_type,
            file_size=file_size,
            tenant_id=tenant_id,
        )
        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)
        
        return file_record
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Socket.IO for WebSockets | Native FastAPI WebSocket | FastAPI 0.70+ (2021) | Simpler deployment, no Redis dependency for basic pub/sub |
| Storing files in database BYTEA | Filesystem storage with metadata in DB | Always preferred | Better performance, easier backups, simpler scaling |
| Nested comment threads | Flat list with reply_to_id | Modern UIs (2020+) | Faster queries, simpler pagination, better mobile UX |
| Synchronous file I/O | aiofiles async I/O | Python 3.7+ asyncio maturity | Non-blocking uploads, better concurrency |
| Client-side MIME validation | Server-side python-magic | Security best practice | Prevents malicious uploads, reliable type detection |

**Deprecated/outdated:**
- **passlib.hash**: Project already migrated to direct bcrypt usage (Phase 1 P02) due to passlib 1.7.4 incompatibility
- **python-socketio**: Adds unnecessary complexity for v1 single-server deployment; FastAPI native WebSocket sufficient

## Open Questions

1. **Message pagination strategy**
   - What we know: Phases 2-4 use offset-based pagination (implicit via LIMIT without offset param)
   - What's unclear: Cursor-based pagination might be better for real-time message streams (new messages arrive while user scrolls)
   - Recommendation: Start with offset-based for consistency with existing endpoints; can migrate to cursor if performance issues arise

2. **WebSocket heartbeat interval**
   - What we know: Browsers timeout idle WebSocket connections (typically 60-120 seconds)
   - What's unclear: Optimal ping interval to balance connection stability vs network traffic
   - Recommendation: 30-second client-side ping (standard Socket.IO default), server closes connection after 90s of inactivity

3. **File MIME type whitelist scope**
   - What we know: Need images, PDFs, documents, videos (from requirements)
   - What's unclear: Specific formats for "documents" (Word, Excel, PowerPoint? Google Docs exports?)
   - Recommendation: Start with common formats (JPEG, PNG, GIF, WebP, PDF, DOCX, XLSX, MP4, MOV); admin can request additions

4. **Unread message tracking**
   - What we know: JobResponse should show unread_count (from CONTEXT.md)
   - What's unclear: How to track "read" status — per-user read receipts? Last-seen timestamp?
   - Recommendation: Last-seen timestamp per user-job pair; unread = messages created_at > last_seen. Simple, no per-message overhead.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 0.24.0 |
| Config file | pyproject.toml (tool.pytest.ini_options) |
| Quick run command | `pytest tests/test_messages.py tests/test_tasks.py tests/test_files.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MSG-01 | Threaded messaging per job | integration | `pytest tests/test_messages.py::test_create_message_with_reply -x` | ❌ Wave 0 |
| MSG-02 | Markdown text storage | unit | `pytest tests/test_messages.py::test_message_markdown_content -x` | ❌ Wave 0 |
| MSG-03 | Searchable message history | integration | `pytest tests/test_messages.py::test_search_messages -x` | ❌ Wave 0 |
| MSG-04 | Real-time WebSocket delivery | integration | `pytest tests/test_websocket.py::test_message_broadcast -x` | ❌ Wave 0 |
| TASK-01 | Admin creates tasks | integration | `pytest tests/test_tasks.py::test_admin_create_task -x` | ❌ Wave 0 |
| TASK-02 | Task fields (assignee, deadline, priority) | unit | `pytest tests/test_tasks.py::test_task_model_fields -x` | ❌ Wave 0 |
| TASK-03 | Status workflow validation | unit | `pytest tests/test_task_state.py::test_task_transitions -x` | ❌ Wave 0 |
| TASK-04 | Crew updates own tasks | integration | `pytest tests/test_tasks.py::test_crew_update_assigned_task -x` | ❌ Wave 0 |
| TASK-05 | Task references message | integration | `pytest tests/test_tasks.py::test_task_message_link -x` | ❌ Wave 0 |
| FILE-01 | File upload to job | integration | `pytest tests/test_files.py::test_upload_file -x` | ❌ Wave 0 |
| FILE-02 | File preview (serve with MIME) | integration | `pytest tests/test_files.py::test_serve_file_with_mime -x` | ❌ Wave 0 |
| FILE-03 | Upload metadata tracking | unit | `pytest tests/test_files.py::test_file_metadata -x` | ❌ Wave 0 |
| FILE-04 | Tenant-isolated storage | integration | `pytest tests/test_files.py::test_file_tenant_isolation -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_{module}.py -x` (stop on first failure for fast feedback)
- **Per wave merge:** Full suite for affected modules (e.g., `pytest tests/test_messages.py tests/test_websocket.py`)
- **Phase gate:** `pytest` (full suite green before `/gsd:verify-work`)

### Wave 0 Gaps
- [ ] `tests/test_messages.py` — covers MSG-01, MSG-02, MSG-03 (CRUD + search + threading)
- [ ] `tests/test_websocket.py` — covers MSG-04 (connection, subscription, broadcast)
- [ ] `tests/test_tasks.py` — covers TASK-01, TASK-02, TASK-04, TASK-05 (CRUD + permissions + message link)
- [ ] `tests/test_task_state.py` — covers TASK-03 (state machine validation, unit tests)
- [ ] `tests/test_files.py` — covers FILE-01, FILE-02, FILE-03, FILE-04 (upload, serve, metadata, isolation)
- [ ] `tests/conftest.py` updates — WebSocket test client fixture, file upload fixtures
- [ ] Framework already installed (pytest 9.0.2, pytest-asyncio 0.24.0)

**WebSocket testing note:** httpx AsyncClient supports WebSocket testing via `async with client.websocket_connect(url)` — no additional dependencies needed.

## Sources

### Primary (HIGH confidence)
- FastAPI documentation (WebSocket support, File uploads) — https://fastapi.tiangolo.com/advanced/websockets/ and /tutorial/request-files/
- Existing codebase patterns:
  - `.planning/phases/05-coordination-layer/05-CONTEXT.md` — locked decisions
  - `backend/app/models/base.py` — TenantMixin, TimestampMixin patterns
  - `backend/app/core/state_machine.py` — state transition validation pattern
  - `backend/app/models/assignment.py` — AssignmentState enum and ASSIGNMENT_TRANSITIONS reference
  - `backend/app/api/v1/jobs.py` — CRUD router pattern, batch query optimization
  - `backend/app/schemas/job.py` — JobResponse with placeholder messages/tasks/files
  - `backend/pyproject.toml` — current dependency versions (FastAPI 0.136.1, Pydantic 2.13.4, SQLAlchemy 2.0.49)

### Secondary (MEDIUM confidence)
- Python library versions verified via `python3 -c "import X; print(X.__version__)"` on 2026-05-16
- SQLAlchemy 2.0 documentation — async patterns, relationship definitions
- Pydantic v2 documentation — schema validation, File/UploadFile handling

### Tertiary (LOW confidence)
- aiofiles usage patterns (not yet installed, recommended based on async I/O best practices)
- python-magic MIME detection (standard library in security contexts, not yet verified for this project)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All core libraries already in use, versions verified, patterns established in codebase
- Architecture: HIGH - Patterns directly derived from existing Phase 1-4 code, WebSocket built into FastAPI
- Pitfalls: MEDIUM - Based on FastAPI/WebSocket common issues and existing project decisions, not project-specific history

**Research date:** 2026-05-16
**Valid until:** 2026-06-15 (30 days - stable libraries, established patterns)
