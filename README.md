# Examination Management Portal V2

Role-based examination management application built with Flask REST APIs, Vue.js, Bootstrap, SQLite, Redis and Celery.

## Features
- Student self-registration and login; Admin and Examiner accounts are not publicly registered.
- Programmatic SQLite schema initialization and pre-created Admin.
- Admin dashboard, course/examination management, examiner creation, rubric creation and result publication.
- Examiner slot management, booked student list and rubric-based evaluation APIs.
- Student examination search, booking, cancellation, history, published results and asynchronous CSV export.
- Redis cache helper for frequently accessed data, with cache invalidation hooks.
- Celery daily reminder, monthly report and CSV export tasks.
- API and database documentation, tests, and project report template.

## Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Redis server
- Windows PowerShell, macOS Terminal, or Linux shell

## Configure environment
Copy `.env.example` to `.env`, then set a strong `FLASK_SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` before first initialization. Never use the documented development fallback outside local testing.

### Windows PowerShell
```powershell
cd examination-management-portal
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Edit `.env` before initialization. Then:
```powershell
$env:PYTHONPATH = "$PWD\backend"
python scripts\initialize_database.py
python backend\app.py
```
The API starts at `http://127.0.0.1:5000`. Health check: `http://127.0.0.1:5000/api/health`.

### macOS/Linux
```bash
cd examination-management-portal
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
set -a; source .env; set +a
PYTHONPATH=backend python scripts/initialize_database.py
PYTHONPATH=backend python backend/app.py
```

## Admin account
Configure `ADMIN_EMAIL` and `ADMIN_PASSWORD` before the first initialization. If omitted, local development initialization uses `admin@example.com` and `Admin123!ChangeMe`; change this immediately and do not use it outside a disposable local demo. Existing Admin accounts are not recreated by subsequent initialization runs. There is no Admin registration endpoint.

## Frontend
In another terminal:
```bash
cd frontend
npm install
npm run serve
```
Open `http://localhost:8080`. Configure `VUE_APP_API_URL` if the backend uses a different address. The frontend uses session cookies; backend CORS is configured for `FRONTEND_ORIGIN`.

## Redis and Celery
Start Redis using your OS's Redis installation. Verify with `redis-cli ping` (expected `PONG`). Ensure `REDIS_URL` is configured in `.env`.

In a terminal from the project root:
```powershell
$env:PYTHONPATH = "$PWD\backend"
celery -A celery_app.celery worker --loglevel=INFO
```
In another terminal:
```powershell
$env:PYTHONPATH = "$PWD\backend"
celery -A celery_app.celery beat --loglevel=INFO
```
On macOS/Linux, prefix commands with `PYTHONPATH=backend` or export `PYTHONPATH=backend`. The daily reminder task looks for booked exams scheduled for tomorrow. The monthly report task is scheduled for 08:00 on the first day of each month and computes the previous calendar month's statistics. SMTP is optional for local tests; actual email delivery requires valid SMTP settings.

## Tests
```bash
cd backend
python -m pytest -q
```

## Important limitations to verify before submission
- Redis must be running for live caching and asynchronous exports; `/api/health` reports Redis availability.
- SMTP delivery requires configuration and was not verified without real credentials.
- Celery workers/Beat must run separately from Flask.
- Frontend build requires npm dependency installation.
- This is a locally demonstrable academic project baseline; review all workflows and test the full end-to-end path before final submission/viva.

## Directory structure
- `backend/`: Flask app, routes, services, SQLite schema, Celery tasks and tests
- `frontend/`: Vue.js application and Bootstrap styling
- `scripts/`: database initialization and environment checks
- `docs/`: API, ER diagram, testing, demo and report template

## ZIP packaging
The delivered ZIP contains this root directory. To recreate it after changes:
```python
import shutil
shutil.make_archive("examination-management-portal", "zip", root_dir=".", base_dir="examination-management-portal")
```

## Admin control centre

The admin route (`/admin`) now includes:

- Overview cards for courses, examinations, students, examiners, slots and bookings.
- Course create/update/delete (courses with history are deactivated rather than hard-deleted).
- Examination create/update/close, slot-creation and booking window controls, and result publication.
- Per-examination rubric criterion creation and deletion.
- Student/examiner search, examiner creation, and account activate/disable controls.
- All-slot listing and examiner reassignment.
- All-booking search, cancellation, and rescheduling to another available slot of the same examination.
- Report summary by examination status/type and examiner workload.

These controls use the Flask API and SQLite database. Sign in with the existing admin account; do not register a second admin. Keep the local `.env` out of shared ZIPs and do not commit real credentials.
