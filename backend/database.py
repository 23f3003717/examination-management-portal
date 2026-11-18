
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

from flask import current_app, has_app_context
from werkzeug.security import generate_password_hash

from config import Config


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(
    BASE_DIR, "instance", "examination_portal.sqlite"
)


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','examiner','student')),
    account_status TEXT NOT NULL DEFAULT 'active',
    contact_details TEXT,
    department TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE,
    course_name TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS examinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    examination_name TEXT NOT NULL,
    examination_type TEXT NOT NULL
        CHECK(examination_type IN ('Viva','Practical','Project Demo','Assessment')),
    description TEXT DEFAULT '',
    duration INTEGER NOT NULL,
    maximum_marks REAL NOT NULL,
    slot_creation_start TEXT,
    slot_creation_end TEXT,
    slot_booking_start TEXT,
    slot_booking_end TEXT,
    examination_status TEXT NOT NULL DEFAULT 'Draft'
        CHECK(examination_status IN (
            'Draft','Slot Creation','Booking Open','Closed','Completed'
        )),
    instructions TEXT DEFAULT '',
    results_published INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS examination_controls (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    slot_creation_open INTEGER NOT NULL DEFAULT 1 CHECK(slot_creation_open IN (0, 1)),
    student_booking_open INTEGER NOT NULL DEFAULT 1 CHECK(student_booking_open IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Assign examinations to examiners.
CREATE TABLE IF NOT EXISTS examination_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    examination_id INTEGER NOT NULL
        REFERENCES examinations(id) ON DELETE CASCADE,
    examiner_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(examination_id, examiner_id)
);

CREATE TABLE IF NOT EXISTS rubrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    examination_id INTEGER NOT NULL
        REFERENCES examinations(id) ON DELETE CASCADE,
    criterion_name TEXT NOT NULL,
    maximum_marks REAL NOT NULL,
    weightage REAL NOT NULL DEFAULT 1,
    description TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    examination_id INTEGER NOT NULL REFERENCES examinations(id),
    examiner_id INTEGER NOT NULL REFERENCES users(id),
    exam_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    maximum_capacity INTEGER NOT NULL,
    available_seats INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Available'
        CHECK(status IN ('Available','Full','Cancelled','Completed')),
    meeting_link TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(examiner_id, exam_date, start_time)
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id),
    slot_id INTEGER NOT NULL REFERENCES slots(id),
    booking_date TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'Booked'
        CHECK(status IN ('Booked','Cancelled','Completed')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS one_active_booking_per_student_slot
ON bookings(student_id, slot_id)
WHERE status = 'Booked';

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL UNIQUE REFERENCES bookings(id),
    student_id INTEGER NOT NULL REFERENCES users(id),
    examiner_id INTEGER NOT NULL REFERENCES users(id),
    total_marks REAL NOT NULL,
    remarks TEXT DEFAULT '',
    evaluation_status TEXT NOT NULL DEFAULT 'Submitted',
    evaluated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluation_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id INTEGER NOT NULL
        REFERENCES evaluations(id) ON DELETE CASCADE,
    rubric_id INTEGER NOT NULL REFERENCES rubrics(id),
    marks REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Unread',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS export_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'Pending',
    file_path TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reminder_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id),
    examination_id INTEGER NOT NULL REFERENCES examinations(id),
    slot_id INTEGER NOT NULL REFERENCES slots(id),
    exam_date TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, examination_id, exam_date)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    details TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exams_course
ON examinations(course_id);

CREATE INDEX IF NOT EXISTS idx_assignment_examiner
ON examination_assignments(examiner_id);

CREATE INDEX IF NOT EXISTS idx_assignment_examination
ON examination_assignments(examination_id);

CREATE INDEX IF NOT EXISTS idx_slots_exam_date
ON slots(examination_id, exam_date);

CREATE INDEX IF NOT EXISTS idx_bookings_student
ON bookings(student_id, status);

CREATE INDEX IF NOT EXISTS idx_eval_student
ON evaluations(student_id);
"""


def resolve_db_path(path=None):
    if path is not None:
        db_path = path
    elif has_app_context():
        db_path = (
            current_app.config.get("DATABASE_PATH")
            or Config.DATABASE_PATH
        )
    else:
        db_path = Config.DATABASE_PATH

    if not Path(str(db_path)).is_absolute():
        project_root = Path(__file__).resolve().parent.parent

        if str(db_path).startswith("backend/"):
            db_path = (project_root / db_path).resolve()
        else:
            db_path = (
                Path(__file__).resolve().parent / db_path
            ).resolve()

    return str(db_path)


def connect_db(path=None):
    db_path = resolve_db_path(path)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")

    return conn


def get_db_connection():
    connection = sqlite3.connect(resolve_db_path(), timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 15000")
    return connection


@contextmanager
def db_session(path=None):
    conn = connect_db(path)

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _seed_demo_account(conn, name, email, password, role, department=""):
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return

    existing = conn.execute(
        "SELECT id, role, account_status FROM users WHERE email = ?",
        (normalized_email,),
    ).fetchone()

    if existing:
        if existing["role"] != role:
            conn.execute(
                "UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (role, existing["id"]),
            )
        if existing["account_status"] != "active":
            conn.execute(
                "UPDATE users SET account_status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (existing["id"],),
            )
        return

    conn.execute(
        """
        INSERT INTO users (name, email, password_hash, role, account_status, department)
        VALUES (?, ?, ?, ?, 'active', ?)
        """,
        (name, normalized_email, generate_password_hash(password), role, department),
    )


def init_db(
    path=None,
    admin_name=None,
    admin_email=None,
    admin_password=None
):
    with db_session(path) as conn:
        conn.executescript(SCHEMA)

        email = admin_email or Config.ADMIN_EMAIL
        password = (
            admin_password
            if admin_password is not None
            else Config.ADMIN_PASSWORD
        )

        if not password:
            password = "Admin123!ChangeMe"

        existing = conn.execute(
            """
            SELECT id FROM users
            WHERE role = 'admin'
            ORDER BY id
            LIMIT 1
            """
        ).fetchone()

        if not existing:
            conn.execute(
                """
                INSERT INTO users (
                    name, email, password_hash, role
                )
                VALUES (?, ?, ?, 'admin')
                """,
                (
                    admin_name or Config.ADMIN_NAME,
                    email.lower(),
                    generate_password_hash(password)
                )
            )

        _seed_demo_account(
            conn,
            "Demo Student",
            "student@example.com",
            "Student123!",
            "student",
            department="Demo",
        )
        _seed_demo_account(
            conn,
            "Demo Examiner",
            "examiner@example.com",
            "Examiner123!",
            "examiner",
            department="Demo",
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO examination_controls (id, slot_creation_open, student_booking_open)
            VALUES (1, 1, 1)
            """
        )

        # Preserve the first admin and disable duplicate admin accounts.
        admins = conn.execute(
            """
            SELECT id FROM users
            WHERE role = 'admin'
            ORDER BY id
            """
        ).fetchall()

        for row in admins[1:]:
            conn.execute(
                """
                UPDATE users
                SET account_status = 'disabled'
                WHERE id = ?
                """,
                (row["id"],)
            )

    return True
