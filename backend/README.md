# Newtonite Operations API

## Setup (Windows PowerShell)
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## Demo accounts
- admin / admin123 — Admin, Operations
- lead / lead123 — Lead, Operations
- member / member123 — Member, Operations
- viewer / viewer123 — Viewer, Operations
- other / other123 — Member, Finance

This is a placement-challenge demo. Authentication uses demo bearer tokens and plain-text seeded passwords; do not use this setup in production.

## Tests
From `backend` run:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
