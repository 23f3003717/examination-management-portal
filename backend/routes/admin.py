from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from database import db_session
from auth import require_roles
from cache import invalidate

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@bp.get("/dashboard")
@require_roles("admin")
def dashboard():
    with db_session() as c:
        counts = {}
        for key, table in [("courses","courses"),("examinations","examinations"),("students","users"),("examiners","users"),("slots","slots"),("bookings","bookings")]:
            if key in ("students","examiners"):
                role = "student" if key == "students" else "examiner"
                counts[key] = c.execute("SELECT COUNT(*) n FROM users WHERE role=?", (role,)).fetchone()["n"]
            else:
                counts[key] = c.execute(f"SELECT COUNT(*) n FROM {table}").fetchone()["n"]
        counts["pending_evaluations"] = c.execute("SELECT COUNT(*) n FROM bookings b LEFT JOIN evaluations e ON e.booking_id=b.id WHERE b.status='Booked' AND e.id IS NULL").fetchone()["n"]
        counts["published_results"] = c.execute("SELECT COUNT(*) n FROM examinations WHERE results_published=1").fetchone()["n"]
    return jsonify(counts=counts)

@bp.get("/examination-controls")
@require_roles("admin")
def examination_controls():
    with db_session() as c:
        c.execute(
            "INSERT OR IGNORE INTO examination_controls (id, slot_creation_open, student_booking_open) VALUES (1, 1, 1)"
        )
        row = c.execute(
            "SELECT slot_creation_open, student_booking_open FROM examination_controls WHERE id = 1"
        ).fetchone()
    return jsonify(
        slot_creation_open=bool(row["slot_creation_open"]),
        student_booking_open=bool(row["student_booking_open"]),
    )

@bp.put("/examination-controls/slot-creation")
@require_roles("admin")
def update_slot_creation_control():
    d = request.get_json(silent=True) or {}
    enabled = d.get("enabled")
    if not isinstance(enabled, bool):
        return jsonify(error="enabled must be a boolean"), 400

    with db_session() as c:
        c.execute(
            "INSERT OR IGNORE INTO examination_controls (id, slot_creation_open, student_booking_open) VALUES (1, 1, 1)"
        )
        c.execute(
            "UPDATE examination_controls SET slot_creation_open = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (1 if enabled else 0,),
        )
        row = c.execute(
            "SELECT slot_creation_open, student_booking_open FROM examination_controls WHERE id = 1"
        ).fetchone()

    return jsonify(
        slot_creation_open=bool(row["slot_creation_open"]),
        student_booking_open=bool(row["student_booking_open"]),
    )

@bp.put("/examination-controls/student-booking")
@require_roles("admin")
def update_student_booking_control():
    d = request.get_json(silent=True) or {}
    enabled = d.get("enabled")
    if not isinstance(enabled, bool):
        return jsonify(error="enabled must be a boolean"), 400

    with db_session() as c:
        c.execute(
            "INSERT OR IGNORE INTO examination_controls (id, slot_creation_open, student_booking_open) VALUES (1, 1, 1)"
        )
        c.execute(
            "UPDATE examination_controls SET student_booking_open = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (1 if enabled else 0,),
        )
        row = c.execute(
            "SELECT slot_creation_open, student_booking_open FROM examination_controls WHERE id = 1"
        ).fetchone()

    return jsonify(
        slot_creation_open=bool(row["slot_creation_open"]),
        student_booking_open=bool(row["student_booking_open"]),
    )

@bp.get("/users")
@require_roles("admin")
def users():
    role = request.args.get("role")
    with db_session() as c:
        if role in ("student","examiner","admin"):
            rows = c.execute("SELECT id,name,email,role,account_status,department,created_at FROM users WHERE role=? ORDER BY id DESC", (role,)).fetchall()
        else:
            rows = c.execute("SELECT id,name,email,role,account_status,department,created_at FROM users ORDER BY id DESC").fetchall()
    return jsonify(items=[dict(r) for r in rows])

@bp.post("/examiners")
@require_roles("admin")
def create_examiner():
    d = request.get_json(silent=True) or {}
    if not d.get("name") or not d.get("email") or len(d.get("password","")) < 8:
        return jsonify(error="Name, email and password (at least 8 characters) are required"), 400
    try:
        with db_session() as c:
            cur = c.execute("INSERT INTO users(name,email,password_hash,role,department,contact_details) VALUES(?,?,?,'examiner',?,?)",
                (d["name"].strip(),d["email"].lower().strip(),generate_password_hash(d["password"]),d.get("department",""),d.get("contact_details","")))
            uid = cur.lastrowid
    except Exception as exc:
        if "UNIQUE" in str(exc): return jsonify(error="Email already exists"), 409
        raise
    return jsonify(id=uid,message="Examiner created"), 201

@bp.get("/bookings")
@require_roles("admin")
def all_bookings():
    with db_session() as c:
        rows = c.execute("""SELECT b.*,u.name student_name,e.id AS examination_id,e.examination_name,
        s.exam_date,s.start_time,s.status AS slot_status,ex.name examiner_name
        FROM bookings b JOIN users u ON u.id=b.student_id JOIN slots s ON s.id=b.slot_id
        JOIN examinations e ON e.id=s.examination_id JOIN users ex ON ex.id=s.examiner_id ORDER BY s.exam_date DESC""").fetchall()
    return jsonify(items=[dict(r) for r in rows])

@bp.post("/bookings/<int:booking_id>/reschedule")
@require_roles("admin")
def reschedule(booking_id):
    d = request.get_json(silent=True) or {}
    new_slot = d.get("slot_id")
    if not new_slot:
        return jsonify(error="slot_id is required"), 400
    with db_session() as c:
        b = c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not b:
            return jsonify(error="Booking not found"), 404
        if b["status"] != "Booked":
            return jsonify(error="Only active Booked bookings can be rescheduled"), 409

        s = c.execute("SELECT * FROM slots WHERE id=?", (new_slot,)).fetchone()
        if not s or s["status"] not in ("Available","Full") or s["available_seats"] < 1:
            return jsonify(error="Destination slot is not available"), 400

        old = c.execute("SELECT * FROM slots WHERE id=?", (b["slot_id"],)).fetchone()
        if not old or old["examination_id"] != s["examination_id"]:
            return jsonify(error="A booking can only be rescheduled to another slot of the same examination"), 400

        c.execute("UPDATE slots SET available_seats=available_seats+1,status='Available' WHERE id=?", (old["id"],))
        c.execute("UPDATE slots SET available_seats=available_seats-1,status=CASE WHEN available_seats-1=0 THEN 'Full' ELSE 'Available' END WHERE id=?", (new_slot,))
        c.execute("UPDATE bookings SET slot_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_slot,booking_id))
        c.execute("INSERT INTO audit_logs(actor_id,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                  (request.current_user["id"],"reschedule","booking",booking_id,f"slot {old['id']} -> {new_slot}"))
    return jsonify(message="Booking rescheduled")

@bp.post("/examinations/<int:exam_id>/publish")
@require_roles("admin")
def publish_results(exam_id):
    with db_session() as c:
        cur = c.execute("UPDATE examinations SET results_published=1,updated_at=CURRENT_TIMESTAMP WHERE id=?", (exam_id,))
        if cur.rowcount == 0: return jsonify(error="Examination not found"), 404
    return jsonify(message="Results published")


@bp.post("/slots/<int:slot_id>/reassign-examiner")
@require_roles("admin")
def reassign_examiner(slot_id):
    d = request.get_json(silent=True) or {}
    examiner_id = d.get("examiner_id")
    if not examiner_id:
        return jsonify(error="examiner_id is required"), 400
    with db_session() as c:
        slot = c.execute("SELECT * FROM slots WHERE id=?", (slot_id,)).fetchone()
        examiner = c.execute("SELECT id FROM users WHERE id=? AND role='examiner' AND account_status='active'", (examiner_id,)).fetchone()
        if not slot or not examiner:
            return jsonify(error="Slot or active examiner not found"), 404
        overlap = c.execute("""SELECT id FROM slots WHERE examiner_id=? AND exam_date=? AND status!='Cancelled'
        AND id!=? AND start_time < ? AND end_time > ?""",
        (examiner_id, slot["exam_date"], slot_id, slot["end_time"], slot["start_time"])).fetchone()
        if overlap:
            return jsonify(error="The selected examiner has an overlapping slot"), 409
        old_examiner = slot["examiner_id"]
        c.execute("UPDATE slots SET examiner_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (examiner_id, slot_id))
        c.execute("INSERT INTO audit_logs(actor_id,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)",
                  (request.current_user["id"],"reassign_examiner","slot",slot_id,f"examiner {old_examiner} -> {examiner_id}"))
    return jsonify(message="Examiner reassigned")


@bp.patch("/users/<int:user_id>/status")
@require_roles("admin")
def update_user_status(user_id):
    d = request.get_json(silent=True) or {}
    status = d.get("account_status")
    if status not in ("active", "disabled"):
        return jsonify(error="account_status must be active or disabled"), 400
    with db_session() as c:
        user = c.execute("SELECT id, role FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return jsonify(error="User not found"), 404
        if user["role"] == "admin":
            return jsonify(error="The pre-existing admin account cannot be disabled here"), 403
        c.execute("UPDATE users SET account_status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, user_id))
    return jsonify(message=f"Account {status}", account_status=status)
@bp.post("/examinations/<int:exam_id>/assign-examiner")
@require_roles("admin")
def assign_examiner(exam_id):
    data = request.get_json(silent=True) or {}
    examiner_id = data.get("examiner_id")

    if not examiner_id:
        return jsonify(error="examiner_id is required"), 400

    try:
        examiner_id = int(examiner_id)
    except (TypeError, ValueError):
        return jsonify(error="examiner_id must be a valid number"), 400

    with db_session() as c:
        exam = c.execute(
            "SELECT id FROM examinations WHERE id=?",
            (exam_id,)
        ).fetchone()

        if not exam:
            return jsonify(error="Examination not found"), 404

        examiner = c.execute(
            """SELECT id FROM users
               WHERE id=? AND role='examiner'
               AND account_status='active'""",
            (examiner_id,)
        ).fetchone()

        if not examiner:
            return jsonify(error="Active examiner not found"), 404

        existing = c.execute(
            """SELECT id FROM examination_assignments
               WHERE examination_id=? AND examiner_id=?""",
            (exam_id, examiner_id)
        ).fetchone()

        if existing:
            return jsonify(message="Examiner is already assigned to this examination"), 200

        c.execute(
            """INSERT INTO examination_assignments
               (examination_id, examiner_id)
               VALUES (?, ?)""",
            (exam_id, examiner_id)
        )

        c.execute(
            """INSERT INTO audit_logs
               (actor_id, action, entity_type, entity_id, details)
               VALUES (?, ?, ?, ?, ?)""",
            (
                request.current_user["id"],
                "assign_examiner",
                "examination",
                exam_id,
                f"Examiner {examiner_id} assigned"
            )
        )

    invalidate(("exams:", "schedules:"))

    return jsonify(message="Examination assigned successfully"), 201