from pathlib import Path

from tests.conftest import login


def test_admin_created_and_can_login(client):
    r=login(client,"admin@test.local","TestAdmin123!")
    assert r.status_code==200
    assert r.json["user"]["role"]=="admin"


def test_demo_student_and_examiner_accounts_are_seeded(client):
    student = login(client, "student@example.com", "Student123!")
    examiner = login(client, "examiner@example.com", "Examiner123!")

    assert student.status_code == 200
    assert student.json["user"]["role"] == "student"
    assert examiner.status_code == 200
    assert examiner.json["user"]["role"] == "examiner"


def test_admin_registration_not_available(client):
    r=client.post("/api/auth/register",json={"name":"Bad","email":"bad@test.local","password":"Password123"})
    assert r.status_code==201
    # Registration is always student-only; no public admin role field is accepted.
    login(client,"admin@test.local","TestAdmin123!")
    assert client.get("/api/admin/dashboard").status_code==200


def test_relative_database_path_resolves_to_backend_instance(monkeypatch):
    project_root = Path(__file__).resolve().parents[2]
    backend_dir = project_root / "backend"
    monkeypatch.chdir(backend_dir)

    from app import create_app

    app = create_app({
        "TESTING": True,
        "DATABASE_PATH": "backend/instance/examination_portal.sqlite",
        "SECRET_KEY": "test-secret",
        "ADMIN_EMAIL": "admin@test.local",
        "ADMIN_PASSWORD": "TestAdmin123!",
    })

    database_path = Path(app.config["DATABASE_PATH"])
    assert database_path.is_absolute()
    assert database_path.parent == backend_dir / "instance"
