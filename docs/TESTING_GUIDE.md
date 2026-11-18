# Testing guide

From the `backend` directory, with dependencies installed:

```bash
python -m pytest -q
```

The test suite uses a temporary SQLite database and verifies default Admin creation/login, student registration, basic course creation, role access, and health response. Expand integration testing when configuring a live Redis/Celery environment.
