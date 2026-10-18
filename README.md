# Newtonite Operations Under Pressure

A full-stack demo for creating, assigning, tracking and resolving operational work items across teams. It includes a React dashboard, a FastAPI backend, a SQLite database, team-scoped access checks, workflow transitions, activity history, duplicate-request protection, stale-version checks and API tests.

## Requirements
- Python 3.10+
- Node.js and npm

## Run on Windows PowerShell
Terminal 1:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
Terminal 2:
```powershell
cd frontend
npm install
npm run dev
```
Open the local URL printed by Vite, normally http://localhost:5173. API docs: http://127.0.0.1:8000/docs.

## Demo logins
| Username | Password | Role / team |
|---|---|---|
| admin | admin123 | Admin / Operations |
| lead | lead123 | Lead / Operations |
| member | member123 | Member / Operations |
| viewer | viewer123 | Viewer / Operations |
| other | other123 | Member / Finance |

## Tests
From `backend`: ` .\.venv\Scripts\python.exe -m pytest -q `

## Implemented behaviors
- Team-scoped item list and item detail checks
- Server-side filtering and pagination parameters
- Workflow transition validation and Lead/Admin approval check
- Version check rejects stale edits with HTTP 409
- Idempotency key prevents duplicate creation on retry
- Activity events for create, update, claim, status change and comments
- Tests for health, duplicate request, team authorization, claim permissions, stale update and invalid transition

## Known limitations
- SQLite is used for easy local setup; it is not a substitute for validating PostgreSQL row-lock/transaction behavior under concurrent load.
- Demo login returns a username bearer token and seeded passwords are plain text. Replace with hashed passwords and signed expiring tokens before production.
- Seeded demo users belong to one team each. The Admin role can access all teams; other users are team-scoped.
- The UI shows the first 50 matching items; API pagination uses page/page_size rather than cursor pagination.
- Background job/outbox processing, production deployment, rate limiting, and comprehensive concurrent-claim stress tests are not included in this first version.
- Comments are recorded as activity events rather than stored in a separate comments table.

## Architecture
Browser (React) → FastAPI REST API → SQLAlchemy → SQLite. Tests call the API using FastAPI TestClient.
