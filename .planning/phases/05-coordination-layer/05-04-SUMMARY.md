---
phase: 05-coordination-layer
plan: 04
subsystem: coordination-layer
tags: [files, upload, storage, mime-validation, rest-api]
dependency_graph:
  requires: [05-01-file-models]
  provides: [file-upload-api, file-serve-api, file-management]
  affects: [job-coordination]
tech_stack:
  added: []
  patterns: [dual-router-pattern, file-streaming, mime-validation]
key_files:
  created:
    - backend/app/api/v1/files.py
    - backend/tests/test_files.py
  modified:
    - backend/app/main.py
decisions:
  - "Dual router pattern: job-scoped for upload/list, file-scoped for serve/delete"
  - "require_active for read/upload operations (crew can upload), require_admin for delete"
  - "Mock save_upload in tests to avoid filesystem dependencies"
  - "FastAPI FileResponse for file serving with Content-Type header"
  - "Delete DB record first, then disk file to avoid orphaned records"
metrics:
  duration: 143s
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 1
  tests_added: 14
  completed_date: "2026-05-16"
requirements_completed: [FILE-01, FILE-02, FILE-03, FILE-04]
---

# Phase 05 Plan 04: File Upload and Management API Summary

**One-liner:** Dual-router file API with tenant-isolated upload/serve/delete, server-side MIME validation via python-magic, and 100MB limit enforcement

## What Was Built

Implemented complete file upload, serving, and management API with two routers:

**Job-scoped router** (`/api/v1/jobs/{job_id}/files`):
- POST / - Upload file to job with MIME validation
- GET / - List files for job ordered by created_at desc

**File-scoped router** (`/api/v1/files`):
- GET /{file_id} - Get file metadata
- GET /{file_id}/download - Serve file with correct Content-Type
- DELETE /{file_id} - Remove DB record and disk file (admin only)

**Storage:** Files saved to `uploads/{tenant_id}/{job_id}/{file_id}.ext` with UUID filenames preserving original extension.

**Security:** Server-side MIME validation via python-magic (not trusting client headers), 100MB file size limit, RLS tenant isolation on reads.

**Permissions:** Authenticated users (crew + admin) can upload and view files. Admin-only deletion.

## Key Implementation Details

### Dual Router Pattern
Separate routers for different access patterns:
- Job-scoped operations use job_id path parameter (upload, list)
- File-scoped operations use file_id path parameter (serve, delete, metadata)

This prevents awkward URLs like `/api/v1/jobs/{job_id}/files/{file_id}/download` where job_id is redundant.

### File Serving
Uses FastAPI's `FileResponse` with:
- `media_type` set from DB record's `mime_type` field
- `filename` set from DB record's `original_filename` (triggers browser download)
- Path existence check before serving (404 if disk file missing)

### MIME Validation
Delegates to `save_upload()` from `app.core.file_storage`:
- Reads file content into memory
- Uses python-magic to detect MIME type from file content (not client header)
- Validates against ALLOWED_MIME_TYPES whitelist
- Raises ValueError on invalid MIME or size limit exceeded
- ValueError caught and converted to 400 HTTPException

### Delete Flow
1. Delete DB record first (`await db.delete()`, `await db.commit()`)
2. Then delete disk file (`await delete_file(storage_path)`)

This order prevents orphaned DB records. If disk deletion fails, record is already gone so no stale metadata.

### Test Mocking Strategy
All tests mock `save_upload()` to return `(Path, mime_type, file_size)` tuple without touching filesystem. Avoids:
- Needing python-magic installed in test environment
- Disk I/O in tests
- Temp file cleanup

One test (`test_serve_file_with_mime`) uses pytest's `tmp_path` fixture to create a real temp file for serving verification.

## Requirements Coverage

**FILE-01: Upload files to job**
- POST /api/v1/jobs/{job_id}/files with multipart upload
- Returns FileResponse with id, original_filename, mime_type, file_size, uploader_id
- Tests: test_upload_file, test_upload_file_as_crew

**FILE-02: Serve files with correct Content-Type**
- GET /api/v1/files/{file_id}/download returns FastAPI FileResponse
- Content-Type header set from mime_type field
- Content-Disposition: attachment with original_filename
- Tests: test_serve_file_with_mime, test_serve_file_missing_from_disk

**FILE-03: Upload metadata (uploader, timestamp, size)**
- JobFile model captures uploader_id, created_at, file_size, mime_type
- FileResponse schema exposes all metadata fields
- Tests: test_file_metadata

**FILE-04: Tenant isolation via RLS**
- get_current_tenant dependency sets RLS context
- Cross-tenant file access returns 404
- Tests: test_file_tenant_isolation

## Deviations from Plan

None - plan executed exactly as written.

## Testing

Created 14 integration tests:

**Upload tests (5):**
- test_upload_file - admin upload success
- test_upload_file_as_crew - crew upload success
- test_upload_file_invalid_mime - reject disallowed MIME
- test_upload_file_too_large - reject >100MB
- test_upload_file_nonexistent_job - 404 on invalid job

**List/metadata tests (3):**
- test_list_files - returns files ordered by created_at desc
- test_get_file_metadata - returns complete metadata
- test_get_file_not_found - 404 on invalid file_id

**Serve tests (2):**
- test_serve_file_with_mime - correct Content-Type header
- test_serve_file_missing_from_disk - 404 if disk file missing

**Delete tests (2):**
- test_admin_delete_file - admin can delete DB + disk
- test_crew_cannot_delete_file - crew blocked with 403

**Integration tests (2):**
- test_file_metadata - all fields present in response
- test_file_tenant_isolation - RLS prevents cross-tenant access

All tests mock filesystem operations except serve test which uses tmp_path.

## Files Modified

**Created:**
- `backend/app/api/v1/files.py` (209 lines) - Dual router file API
- `backend/tests/test_files.py` (350 lines) - 14 integration tests

**Modified:**
- `backend/app/main.py` - Added files import and registered both routers

## Commits

- `8b8a8f8`: feat(05-04): implement files REST API with upload, serve, and delete
- `90472d7`: test(05-04): add file upload and management integration tests

## Next Steps

Wave 2 coordination layer complete. File upload/serving API fully functional with:
- Server-side MIME validation via python-magic
- Tenant-isolated storage with UUID filenames
- 100MB size limit enforcement
- Admin-only deletion
- 14 integration tests covering all requirements

Ready for Phase 06 (Notifications) or remaining Phase 05 plans if any.

## Self-Check: PASSED

**Created files exist:**
- FOUND: backend/app/api/v1/files.py
- FOUND: backend/tests/test_files.py

**Modified files exist:**
- FOUND: backend/app/main.py

**Commits exist:**
- FOUND: 8b8a8f8
- FOUND: 90472d7

All deliverables verified on disk and in git history.
