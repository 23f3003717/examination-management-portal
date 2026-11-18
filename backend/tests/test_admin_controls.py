import os
import tempfile
import uuid

from tests.conftest import login


def _make_exam(client, exam_name="Control Test Exam", status="Slot Creation"):
    admin = login(client, "admin@test.local", "TestAdmin123!")
    assert admin.status_code == 200

    course_code = f"CTRL{uuid.uuid4().hex[:5].upper()}"
    course = client.post(
        "/api/courses",
        json={
            "course_code": course_code,
            "course_name": "Control Course",
            "description": "Control test",
            "status": "active",
        },
    )
    assert course.status_code == 201, course.get_data(as_text=True)

    exam = client.post(
        "/api/examinations",
        json={
            "course_id": course.json["id"],
            "examination_name": exam_name,
            "examination_type": "Assessment",
            "duration": 60,
            "maximum_marks": 100,
            "examination_status": status,
        },
    )
    assert exam.status_code == 201, exam.get_data(as_text=True)
    return exam.json["id"]


def test_admin_can_view_and_update_controls(client):
    admin = login(client, "admin@test.local", "TestAdmin123!")
    assert admin.status_code == 200

    view = client.get("/api/admin/examination-controls")
    assert view.status_code == 200
    assert "slot_creation_open" in view.json
    assert "student_booking_open" in view.json

    close_slot = client.put(
        "/api/admin/examination-controls/slot-creation",
        json={"enabled": False},
    )
    assert close_slot.status_code == 200
    assert close_slot.json["slot_creation_open"] is False

    close_booking = client.put(
        "/api/admin/examination-controls/student-booking",
        json={"enabled": False},
    )
    assert close_booking.status_code == 200
    assert close_booking.json["student_booking_open"] is False


def test_non_admin_cannot_update_controls(client):
    # create a normal student account via registration
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "Test Student",
            "email": "student@test.local",
            "password": "Password123",
        },
    )
    assert reg.status_code == 201, reg.get_data(as_text=True)

    student = login(client, "student@test.local", "Password123")
    assert student.status_code == 200

    update = client.put(
        "/api/admin/examination-controls/slot-creation",
        json={"enabled": False},
    )
    assert update.status_code == 403


def test_admin_exam_publish_and_close_actions(client):
    login(client, "admin@test.local", "TestAdmin123!")

    course = client.post(
        "/api/courses",
        json={
            "course_code": "PUB1",
            "course_name": "Publishing Course",
            "description": "Publish action test",
            "status": "active",
        },
    )
    assert course.status_code == 201, course.get_data(as_text=True)

    exam = client.post(
        "/api/examinations",
        json={
            "course_id": course.json["id"],
            "examination_name": "Pub Test Exam",
            "examination_type": "Assessment",
            "duration": 60,
            "maximum_marks": 100,
            "examination_status": "Completed",
        },
    )
    assert exam.status_code == 201, exam.get_data(as_text=True)

    publish = client.post(f"/api/admin/examinations/{exam.json['id']}/publish")
    assert publish.status_code == 200, publish.get_data(as_text=True)

    detail = client.get(f"/api/examinations/{exam.json['id']}")
    assert detail.status_code == 200
    assert detail.json["examination"]["results_published"] == 1

    delete = client.delete(f"/api/examinations/{exam.json['id']}")
    assert delete.status_code == 200, delete.get_data(as_text=True)


def test_admin_can_delete_course_with_related_exam_records(client):
    login(client, "admin@test.local", "TestAdmin123!")

    course = client.post(
        "/api/courses",
        json={
            "course_code": "DEL1",
            "course_name": "Delete Course",
            "description": "Delete test",
            "status": "active",
        },
    )
    assert course.status_code == 201, course.get_data(as_text=True)

    exam = client.post(
        "/api/examinations",
        json={
            "course_id": course.json["id"],
            "examination_name": "Delete Exam",
            "examination_type": "Assessment",
            "duration": 60,
            "maximum_marks": 100,
            "examination_status": "Draft",
        },
    )
    assert exam.status_code == 201, exam.get_data(as_text=True)

    delete = client.delete(f"/api/courses/{course.json['id']}")
    assert delete.status_code == 200, delete.get_data(as_text=True)

    course_check = client.get("/api/courses")
    ids = [item["id"] for item in course_check.json["items"]]
    assert course.json["id"] not in ids


def test_slot_creation_and_booking_are_enforced(client):
    # admin set controls closed
    admin = login(client, "admin@test.local", "TestAdmin123!")
    assert admin.status_code == 200

    control = client.put(
        "/api/admin/examination-controls/slot-creation",
        json={"enabled": False},
    )
    assert control.status_code == 200

    # create examiner and login
    examiner = client.post(
        "/api/admin/examiners",
        json={
            "name": "Jane Examiner",
            "email": "examiner@test.local",
            "password": "Password123",
            "department": "CS",
        },
    )
    assert examiner.status_code == 201, examiner.get_data(as_text=True)

    examiner_login = login(client, "examiner@test.local", "Password123")
    assert examiner_login.status_code == 200

    admin_login = login(client, "admin@test.local", "TestAdmin123!")
    assert admin_login.status_code == 200

    exam_id = _make_exam(client, "Closed Slot Creation")
    assignment = client.post(
        f"/api/examinations/{exam_id}/assign-examiner",
        json={"examiner_id": examiner_login.json["user"]["id"]},
    )
    assert assignment.status_code == 201, assignment.get_data(as_text=True)

    examiner_session = login(client, "examiner@test.local", "Password123")
    assert examiner_session.status_code == 200

    create_slot = client.post(
        "/api/slots",
        json={
            "examination_id": exam_id,
            "exam_date": "2035-06-10",
            "start_time": "09:00",
            "end_time": "10:00",
            "maximum_capacity": 10,
        },
    )
    assert create_slot.status_code == 403
    assert "slot creation is closed" in create_slot.json["error"].lower()

    admin_login_again = login(client, "admin@test.local", "TestAdmin123!")
    assert admin_login_again.status_code == 200

    booking_open = client.put(
        "/api/admin/examination-controls/student-booking",
        json={"enabled": False},
    )
    assert booking_open.status_code == 200

    # create a student and attempt booking
    student_reg = client.post(
        "/api/auth/register",
        json={
            "name": "Test Student",
            "email": "booking@test.local",
            "password": "Password123",
        },
    )
    assert student_reg.status_code == 201, student_reg.get_data(as_text=True)

    student_login = login(client, "booking@test.local", "Password123")
    assert student_login.status_code == 200

    # create an exam in Booking Open status and a slot used for booking
    admin_login_after_student = login(client, "admin@test.local", "TestAdmin123!")
    assert admin_login_after_student.status_code == 200
    admin_exam = _make_exam(client, "Closed Booking Exam", status="Slot Creation")

    admin_assign = client.post(
        f"/api/examinations/{admin_exam}/assign-examiner",
        json={"examiner_id": examiner_login.json["user"]["id"]},
    )
    assert admin_assign.status_code == 201, admin_assign.get_data(as_text=True)

    reopen_slot = client.put(
        "/api/admin/examination-controls/slot-creation",
        json={"enabled": True},
    )
    assert reopen_slot.status_code == 200

    examiner_login_again = login(client, "examiner@test.local", "Password123")
    assert examiner_login_again.status_code == 200

    examiner_slot = client.post(
        "/api/slots",
        json={
            "examination_id": admin_exam,
            "exam_date": "2035-06-11",
            "start_time": "09:00",
            "end_time": "10:00",
            "maximum_capacity": 10,
        },
    )
    assert examiner_slot.status_code == 201, examiner_slot.get_data(as_text=True)

    admin_login_open_booking = login(client, "admin@test.local", "TestAdmin123!")
    assert admin_login_open_booking.status_code == 200
    exam_list = client.get("/api/examinations")
    assert exam_list.status_code == 200
    exam_meta = next(item for item in exam_list.json["items"] if item["id"] == admin_exam)
    exam_open = client.put(
        f"/api/examinations/{admin_exam}",
        json={
            "course_id": exam_meta["course_id"],
            "examination_name": "Closed Booking Exam",
            "examination_type": "Assessment",
            "duration": 60,
            "maximum_marks": 100,
            "examination_status": "Booking Open",
        },
    )
    assert exam_open.status_code == 200, exam_open.get_data(as_text=True)

    student_login_again = login(client, "booking@test.local", "Password123")
    assert student_login_again.status_code == 200

    booking = client.post(f"/api/slots/{examiner_slot.json['id']}/book")
    assert booking.status_code == 403
    assert "booking is closed" in booking.json["error"].lower()
