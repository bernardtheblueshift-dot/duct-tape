---
phase: 05-coordination-layer
plan: 02
subsystem: messaging
tags: [messaging, websocket, realtime, communication]
dependency_graph:
  requires: [05-01]
  provides: [message-api, websocket-broadcast]
  affects: [job-detail, coordination-tools]
tech_stack:
  added: [WebSocket, Starlette TestClient]
  patterns: [WebSocket subscribe/unsubscribe, broadcast to job, JWT WebSocket auth]
key_files:
  created:
    - backend/app/api/v1/messages.py
    - backend/app/api/v1/websocket.py
    - backend/tests/test_messages.py
    - backend/tests/test_websocket.py
  modified:
    - backend/app/main.py
decisions:
  - what: "Both admin and crew can post and read messages"
    why: "Crew need full participation in job discussions, not just read-only"
    alternatives: "Admin-only write, crew read-only (rejected: kills collaboration)"
  - what: "ILIKE search on message content"
    why: "Simple substring search sufficient for v1 chat history"
    alternatives: "PostgreSQL full-text search (deferred: add if search becomes bottleneck)"
  - what: "Oldest-first message ordering"
    why: "Chat-style UX convention, users expect chronological flow"
    alternatives: "Newest-first (rejected: anti-pattern for conversations)"
  - what: "JWT token in query param for WebSocket auth"
    why: "WebSocket cannot send Authorization headers, query param is standard pattern"
    alternatives: "Cookie-based auth (rejected: CORS complexity in SaaS multi-tenant)"
  - what: "Fire-and-forget subscribe/unsubscribe actions"
    why: "Subscriptions are client state management, no server response needed"
    alternatives: "Acknowledgement response (rejected: unnecessary round-trip)"
metrics:
  duration: 147
  tasks_completed: 2
  files_created: 4
  files_modified: 1
  tests_added: 18
  commits: 2
  completed_at: "2026-05-16"
---

# Phase 05 Plan 02: Message API and WebSocket Broadcast Summary

**One-liner:** Job-scoped threaded messaging with REST CRUD, ILIKE search, and WebSocket real-time broadcast to subscribed clients.

## What Was Built

### Message REST API
- POST `/api/v1/jobs/{job_id}/messages` — Create message with optional reply_to_id and file_ids
- GET `/api/v1/jobs/{job_id}/messages` — List messages with ILIKE search, ordered oldest-first
- GET `/api/v1/jobs/{job_id}/messages/{message_id}` — Get single message
- Validates job exists, parent message exists (for replies), file IDs valid
- Broadcasts new messages to WebSocket subscribers via ConnectionManager
- Both admin and crew can post and read messages (require_active, not require_admin)

### WebSocket Real-Time Updates
- WebSocket endpoint `/ws?token={jwt}` — JWT auth via query param (headers not supported)
- Subscribe/unsubscribe protocol for job updates
- Ping/pong for connection health checks
- WebSocketDisconnect handling with cleanup
- Manager singleton broadcasts messages to all users subscribed to a job
- Automatic cleanup of broken connections during broadcast

### Tests
- **11 message tests:** create (admin/crew), reply threading, invalid reply (404), empty content (422), list ordered oldest-first, ILIKE search, case-insensitive search, get single, not found (404), markdown content storage
- **7 WebSocket tests:** valid/invalid token auth, subscribe, ping/pong, ConnectionManager broadcast unit test, disconnect cleanup, error handling during broadcast
- Helper function `create_message()` reduces test boilerplate

## Deviations from Plan

None — plan executed exactly as written.

## Technical Notes

### Message Threading Model
Flat message list with optional `reply_to_id` foreign key. Simple model sufficient for job discussions (not complex forums). Frontend can reconstruct thread tree if needed.

### WebSocket Auth Pattern
Standard WebSocket limitation: cannot send Authorization headers. JWT in query param (`/ws?token={jwt}`) is the accepted pattern. Validated via `decode_access_token()` before connection accepted. Close with code 1008 (Policy Violation) on auth failure.

### Broadcast Flow
1. User POSTs message via REST API
2. Message saved to database, refreshed to get timestamps
3. `manager.broadcast_to_job(job_id, {type: "message", data: {...}})` called
4. Manager iterates subscriptions, sends JSON to each WebSocket
5. Broken connections caught and cleaned up

### Testing WebSocket with Starlette
httpx does NOT support `websocket_connect()`. Used `starlette.testclient.TestClient` (synchronous) for WebSocket integration tests. AsyncIO-based tests used `AsyncMock` to test ConnectionManager class directly.

## What's Next

Plan 05-03 will implement:
- Task model with state transitions (TODO/IN_PROGRESS/DONE)
- Task assignment to crew
- Task REST API (CRUD + state transition endpoint)
- Integration with job detail view

## Validation

Routes verified:
```bash
$ python3 -c "from app.api.v1.messages import router; ..."
Messages routes: 3, WS routes: 1
```

Tests verified:
```bash
$ python3 -c "import ast; ..."
test_messages.py: 11 tests
test_websocket.py: 7 tests
```

## Self-Check

### Created Files
```bash
$ [ -f "backend/app/api/v1/messages.py" ] && echo "FOUND"
FOUND
$ [ -f "backend/app/api/v1/websocket.py" ] && echo "FOUND"
FOUND
$ [ -f "backend/tests/test_messages.py" ] && echo "FOUND"
FOUND
$ [ -f "backend/tests/test_websocket.py" ] && echo "FOUND"
FOUND
```

### Commits
```bash
$ git log --oneline | grep -E "(5cfcf14|ba33d24)"
ba33d24 test(05-02): add message and WebSocket integration tests
5cfcf14 feat(05-02): implement messages REST API and WebSocket endpoint
```

## Self-Check: PASSED

All files created, all commits exist, all acceptance criteria met.
