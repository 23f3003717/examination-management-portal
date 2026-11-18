from datetime import date, timedelta

from app import create_app
from celery_app import make_celery
from database import db_session
from tasks import daily_exam_reminders


def _register_student(client, email="reminder@student.test", password="StrongPass123!"):
    res = client.post(
        "/api/auth/register",
        json={"name": "Reminder Student", "email": email, "password": password},
    )
    assert res.status_code == 201
    return res.json


def _create_exam_and_booking(client, exam_name="Reminder Exam"):
    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "TestAdmin123!"},
    )
    assert admin_login.status_code == 200

    course = client.post(
        "/api/courses",
        json={"course_code": "REM1", "course_name": "Reminder Course"},
    )
    assert course.status_code == 201
    course_id = course.json["id"]

    exam = client.post(
        "/api/examinations",
        json={
            "course_id": course_id,
            "examination_name": exam_name,
            "examination_type": "Assessment",
            "duration": 60,
            "maximum_marks": 100,
            "examination_status": "Slot Creation",
            "slot_creation_start": "2000-01-01T00:00:00",
            "slot_creation_end": "2100-01-01T00:00:00",
            "slot_booking_start": "2000-01-01T00:00:00",
            "slot_booking_end": "2100-01-01T00:00:00",
        },
    )
    assert exam.status_code == 201
    exam_id = exam.json["id"]

    examiner = client.post(
        "/api/admin/examiners",
        json={"name": "Reminder Examiner", "email": "examiner.reminder@test.local", "password": "Password123!"},
    )
    assert examiner.status_code == 201
    examiner_id = examiner.json["id"]

    assignment = client.post(f"/api/admin/examinations/{exam_id}/assign-examiner", json={"examiner_id": examiner_id})
    assert assignment.status_code in (200, 201)

    examiner_login = client.post(
        "/api/auth/login",
        json={"email": "examiner.reminder@test.local", "password": "Password123!"},
    )
    assert examiner_login.status_code == 200

    slot = client.post(
        "/api/slots",
        json={
            "examination_id": exam_id,
            "exam_date": (date.today() + timedelta(days=1)).isoformat(),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "maximum_capacity": 20,
        },
    )
    assert slot.status_code == 201
    slot_id = slot.json["id"]

    _register_student(client)
    student_login = client.post(
        "/api/auth/login",
        json={"email": "reminder@student.test", "password": "StrongPass123!"},
    )
    assert student_login.status_code == 200
    student_id = student_login.json["user"]["id"]

    with db_session() as conn:
        conn.execute(
            "UPDATE examinations SET examination_status = 'Booking Open', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (exam_id,),
        )

    booking = client.post(f"/api/slots/{slot_id}/book")
    assert booking.status_code == 201
    return student_id


def test_daily_exam_reminders_are_not_duplicated(client, monkeypatch):
    _create_exam_and_booking(client)

    sent_calls = []

    def fake_send_email(to_email, subject, html_body):
        sent_calls.append((to_email, subject))
        return {"sent": True}

    monkeypatch.setattr("tasks.send_email", fake_send_email)

    with client.application.app_context():
        first = daily_exam_reminders()
        second = daily_exam_reminders()

    assert first["sent"] == 1
    assert second["sent"] == 0
    assert len(sent_calls) == 1


def test_daily_reminder_schedule_uses_configured_time(monkeypatch):
    monkeypatch.setenv("DAILY_REMINDER_HOUR", "9")
    monkeypatch.setenv("DAILY_REMINDER_MINUTE", "30")

    celery_app = make_celery()
    schedule = celery_app.conf.beat_schedule["daily-exam-reminders"]

    assert 9 in schedule["schedule"].hour
    assert 30 in schedule["schedule"].minute
