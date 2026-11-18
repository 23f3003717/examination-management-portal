# API Documentation

Base URL: `http://127.0.0.1:5000/api`. JSON APIs use session cookies.

## Authentication
- `POST /auth/register` — create student account only.
- `POST /auth/login` — authenticate account.
- `POST /auth/logout` — clear session.
- `GET /auth/me` — current user.

## Courses and examinations
- `GET /courses`, `POST /courses` (Admin)
- `PUT /courses/{id}`, `DELETE /courses/{id}` (Admin)
- `GET /examinations?q=&type=`
- `POST /examinations` (Admin)
- `GET|PUT|DELETE /examinations/{id}` (GET public; mutation Admin)
- `GET /examinations/{id}/rubrics`
- `POST /examinations/{id}/rubrics` (Admin)
- `PUT|DELETE /examinations/rubrics/{rubric_id}` (Admin)

## Slots, bookings and evaluation
- `GET /slots?examination_id=&date=&available=1`
- `POST /slots` (Examiner)
- `PUT|DELETE /slots/{id}` (owner Examiner or Admin)
- `POST /slots/{id}/book` (Student)
- `GET /bookings` (role-scoped)
- `POST /bookings/{id}/cancel` (owner Student or Admin)
- `GET /examiner/examinations` (Examiner)
- `GET /examiner/slots/{id}/students` (slot's Examiner)
- `POST /bookings/{id}/evaluation` (assigned Examiner)
- `GET /student/results` (published results only)

## Administration and reports
- `GET /admin/dashboard`, `GET /admin/users?role=`, `POST /admin/examiners`, `GET /admin/bookings`
- `POST /admin/slots/{id}/reassign-examiner`
- `POST /admin/bookings/{id}/reschedule`
- `POST /admin/examinations/{id}/publish`
- `GET /reports/summary`
- `GET /notifications`
- `POST /exports`, `GET /exports/{job_id}`, `GET /exports/{job_id}/download`
- `GET /health`

Protected endpoints require a logged-in session and the documented role. Error responses use `{"error":"..."}`.
