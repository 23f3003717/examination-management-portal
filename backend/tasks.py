
import csv
from datetime import date, timedelta
from pathlib import Path

from celery_app import celery
from config import Config
from database import db_session
from utils.email_utils import send_email


# ============================================================
# 1. DAILY EXAMINATION REMINDER
# ============================================================

@celery.task(name="tasks.daily_exam_reminders")
def daily_exam_reminders():

    reminder_date = (date.today() + timedelta(days=1)).isoformat()

    processed = 0
    sent = 0

    with db_session() as conn:

        rows = conn.execute(
            """
            SELECT DISTINCT
                u.id AS student_id,
                u.email,
                u.name,
                s.id AS slot_id,
                e.id AS examination_id,
                e.examination_name,
                e.instructions,
                s.exam_date,
                s.start_time,
                ex.name AS examiner_name

            FROM bookings b

            JOIN users u ON u.id = b.student_id
            JOIN slots s ON s.id = b.slot_id
            JOIN examinations e ON e.id = s.examination_id
            JOIN users ex ON ex.id = s.examiner_id

            WHERE b.status = 'Booked'
              AND s.exam_date = ?
              AND u.account_status = 'active'

            ORDER BY u.id, e.id
            """,
            (reminder_date,),
        ).fetchall()

        for row in rows:

            processed += 1

            existing = conn.execute(
                """
                SELECT 1
                FROM reminder_logs
                WHERE student_id = ?
                  AND examination_id = ?
                  AND exam_date = ?
                """,
                (
                    row["student_id"],
                    row["examination_id"],
                    reminder_date,
                ),
            ).fetchone()

            if existing:
                continue

            # Professional HTML Email Template

            body = f"""
            <!DOCTYPE html>
            <html>
            <body style="
                margin:0;
                padding:25px;
                background-color:#f4f6f9;
                font-family:Arial,sans-serif;
            ">

                <div style="
                    max-width:600px;
                    margin:auto;
                    background:white;
                    border-radius:12px;
                    overflow:hidden;
                ">

                    <div style="
                        background:#173568;
                        color:white;
                        padding:25px;
                        text-align:center;
                    ">

                        <h2>Examination Management Portal</h2>

                        <p>Official Examination Reminder</p>

                    </div>

                    <div style="padding:25px;">

                        <h3>Hello {row['name']},</h3>

                        <p>
                            This is a reminder that your examination
                            is scheduled for tomorrow.
                        </p>

                        <div style="
                            background:#f0f4ff;
                            padding:20px;
                            border-radius:8px;
                        ">

                            <h3 style="color:#173568;">
                                Examination Details
                            </h3>

                            <p>
                                <b>Student Name:</b>
                                {row['name']}
                            </p>

                            <p>
                                <b>Examination:</b>
                                {row['examination_name']}
                            </p>

                            <p>
                                <b>Exam Date:</b>
                                {row['exam_date']}
                            </p>

                            <p>
                                <b>Exam Time:</b>
                                {row['start_time']}
                            </p>

                            <p>
                                <b>Assigned Examiner:</b>
                                {row['examiner_name']}
                            </p>

                            <p>
                                <b>Instructions:</b>
                                {row['instructions'] or 'Please arrive on time and bring the required materials.'}
                            </p>

                        </div>

                        <p style="margin-top:25px;">
                            Please be prepared and join your
                            examination on time.
                        </p>

                        <p>
                            Best Regards,<br>
                            <b>Examination Management Portal Team</b>
                        </p>

                    </div>

                    <div style="
                        background:#f4f6f9;
                        padding:15px;
                        text-align:center;
                        color:#777;
                    ">

                        Examination Management Portal

                    </div>

                </div>

            </body>
            </html>
            """

            result = send_email(
                row["email"],
                "Upcoming Examination Reminder",
                body,
            )

            if result.get("sent"):

                conn.execute(
                    """
                    INSERT OR IGNORE INTO reminder_logs
                    (student_id, examination_id, slot_id, exam_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        row["student_id"],
                        row["examination_id"],
                        row["slot_id"],
                        reminder_date,
                    ),
                )

                conn.execute(
                    """
                    INSERT INTO notifications
                    (user_id, title, message, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        row["student_id"],
                        "Upcoming examination reminder",
                        f"{row['examination_name']} on {row['exam_date']} at {row['start_time']}",
                        "Sent",
                    ),
                )

                sent += 1

            else:

                conn.execute(
                    """
                    INSERT INTO notifications
                    (user_id, title, message, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        row["student_id"],
                        "Upcoming examination reminder",
                        f"{row['examination_name']} on {row['exam_date']} at {row['start_time']} could not be delivered.",
                        "Failed",
                    ),
                )

    return {
        "processed": processed,
        "sent": sent,
        "date": reminder_date,
    }


# ============================================================
# 2. MONTHLY ADMIN EXAMINATION REPORT
# ============================================================

@celery.task(name="tasks.monthly_exam_report")
def monthly_exam_report():

    today = date.today()

    first_this_month = today.replace(day=1)

    last_month_end = first_this_month - timedelta(days=1)

    period_start = last_month_end.replace(day=1).isoformat()
    period_end = last_month_end.isoformat()

    with db_session() as conn:

        conducted = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM examinations
            WHERE examination_status = 'Completed'
              AND date(updated_at) BETWEEN ? AND ?
            """,
            (period_start, period_end),
        ).fetchone()["n"] or 0

        evaluated = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM evaluations
            WHERE date(evaluated_at) BETWEEN ? AND ?
            """,
            (period_start, period_end),
        ).fetchone()["n"] or 0

        completed = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM bookings
            WHERE status = 'Completed'
              AND date(updated_at) BETWEEN ? AND ?
            """,
            (period_start, period_end),
        ).fetchone()["n"] or 0

        pending = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM bookings b
            LEFT JOIN evaluations v ON v.booking_id = b.id
            WHERE b.status IN ('Booked', 'Completed')
              AND v.id IS NULL
            """
        ).fetchone()["n"] or 0

        active = conn.execute(
            """
            SELECT
                u.name,
                COUNT(DISTINCT v.id) AS total

            FROM users u

            LEFT JOIN evaluations v
                ON v.examiner_id = u.id

            WHERE u.role = 'examiner'

            GROUP BY u.id, u.name

            ORDER BY total DESC, u.name ASC

            LIMIT 5
            """
        ).fetchall()

    active_html = "".join(
        f"<li>{row['name'] or 'Unknown'}: {row['total'] or 0}</li>"
        for row in active
    ) or "<li>No examiner activity recorded.</li>"

    html = (
        "<html><body>"
        "<h1>Monthly Examination Report</h1>"
        f"<p>Period: {period_start} to {period_end}</p>"
        "<ul>"
        f"<li>Examinations conducted: {conducted}</li>"
        f"<li>Students evaluated: {evaluated}</li>"
        f"<li>Completed bookings: {completed}</li>"
        f"<li>Pending evaluations: {pending}</li>"
        "</ul>"
        "<h2>Most active examiners</h2>"
        f"<ul>{active_html}</ul>"
        "</body></html>"
    )

    result = send_email(
        Config.ADMIN_EMAIL,
        "Monthly Examination Report",
        html,
    )

    return {
        "period_start": period_start,
        "period_end": period_end,
        "email_sent": bool(result.get("sent")),
        "details": {
            "conducted": conducted,
            "evaluated": evaluated,
            "completed": completed,
            "pending": pending,
            "active_examiners": [
                dict(row) for row in active
            ],
        },
        "email_result": result,
    }


# ============================================================
# 3. STUDENT EXAMINATION HISTORY CSV EXPORT
# ============================================================

@celery.task(name="tasks.export_history_csv")
def export_history_csv(job_id, student_id):

    export_dir = Path(Config.EXPORT_DIR).resolve()

    export_dir.mkdir(parents=True, exist_ok=True)

    export_path = (
        export_dir /
        f"student_{student_id}_export_{job_id}.csv"
    ).resolve()

    if export_dir not in export_path.parents and export_path != export_dir:
        raise ValueError("Invalid export path")

    try:

        with db_session() as conn:

            conn.execute(
                """
                UPDATE export_jobs
                SET status='Processing',
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND student_id=?
                """,
                (job_id, student_id),
            )

            rows = conn.execute(
                """
                SELECT
                    u.id AS student_id,
                    e.examination_name,
                    c.course_name AS course,
                    s.exam_date AS examination_date,
                    ex.name AS examiner,
                    ev.total_marks AS marks_obtained,
                    b.status AS booking_status

                FROM bookings b

                JOIN users u ON u.id = b.student_id
                JOIN slots s ON s.id = b.slot_id
                JOIN examinations e ON e.id = s.examination_id
                JOIN courses c ON c.id = e.course_id
                JOIN users ex ON ex.id = s.examiner_id

                LEFT JOIN evaluations ev
                    ON ev.booking_id = b.id

                WHERE b.student_id = ?

                ORDER BY s.exam_date DESC
                """,
                (student_id,),
            ).fetchall()

            with export_path.open(
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as csv_file:

                writer = csv.writer(csv_file)

                writer.writerow([
                    "Student ID",
                    "Examination Name",
                    "Course",
                    "Examination Date",
                    "Examiner",
                    "Marks Obtained",
                    "Booking Status",
                ])

                for row in rows:

                    writer.writerow([
                        row["student_id"],
                        row["examination_name"],
                        row["course"],
                        row["examination_date"],
                        row["examiner"],
                        row["marks_obtained"],
                        row["booking_status"],
                    ])

            conn.execute(
                """
                UPDATE export_jobs
                SET status='Completed',
                    file_path=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND student_id=?
                """,
                (str(export_path), job_id, student_id),
            )

            conn.execute(
                """
                INSERT INTO notifications
                (user_id, title, message, status)
                VALUES (?, ?, ?, ?)
                """,
                (
                    student_id,
                    "CSV export completed",
                    f"Your export job #{job_id} is ready.",
                    "Sent",
                ),
            )

    except Exception as exc:

        with db_session() as conn:

            conn.execute(
                """
                UPDATE export_jobs
                SET status='Failed',
                    error_message=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND student_id=?
                """,
                (str(exc), job_id, student_id),
            )

            conn.execute(
                """
                INSERT INTO notifications
                (user_id, title, message, status)
                VALUES (?, ?, ?, ?)
                """,
                (
                    student_id,
                    "CSV export failed",
                    f"Your export job #{job_id} could not be generated.",
                    "Failed",
                ),
            )

        raise

    return {
        "job_id": job_id,
        "status": "Completed",
        "rows": len(rows),
    }
