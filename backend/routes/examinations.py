
from flask import Blueprint, request, jsonify
from database import db_session
from auth import require_roles, current_user
from cache import invalidate, get_client
from datetime import datetime
import json

bp = Blueprint("examinations", __name__, url_prefix="/api/examinations")


@bp.get("")
def list_examinations():
    d = request.args
    search_text = d.get("q", "").strip()
    q = "%" + search_text + "%"
    exam_type = d.get("type", "")

    cache_key = (
        "exams:list:"
        + search_text.lower()
        + ":"
        + exam_type
    )

    client = get_client()

    if client:
        try:
            cached_value = client.get(cache_key)
            if cached_value:
                return jsonify(items=json.loads(cached_value))
        except Exception:
            pass

    with db_session() as c:
        rows = c.execute(
            """
            SELECT e.*, c.course_code, c.course_name
            FROM examinations e
            JOIN courses c ON c.id = e.course_id
            WHERE (
                e.examination_name LIKE ?
                OR c.course_name LIKE ?
                OR c.course_code LIKE ?
            )
            AND (? = '' OR e.examination_type = ?)
            ORDER BY e.created_at DESC
            """,
            (q, q, q, exam_type, exam_type)
        ).fetchall()

    items = [dict(row) for row in rows]

    if client:
        try:
            client.setex(cache_key, 120, json.dumps(items))
        except Exception:
            pass

    return jsonify(items=items)


@bp.post("")
@require_roles("admin")
def create_exam():
    d = request.get_json(silent=True) or {}

    required = (
        "course_id",
        "examination_name",
        "examination_type",
        "duration",
        "maximum_marks"
    )

    if any(d.get(key) in (None, "") for key in required):
        return jsonify(
            error="Required fields: " + ", ".join(required)
        ), 400

    try:
        course_id = int(d["course_id"])
        duration = int(d["duration"])
        maximum_marks = float(d["maximum_marks"])
    except (TypeError, ValueError):
        return jsonify(
            error="Course ID, duration and maximum marks must be valid numbers"
        ), 400

    if duration <= 0 or maximum_marks <= 0:
        return jsonify(
            error="Duration and maximum marks must be positive"
        ), 400

    allowed_types = (
        "Viva",
        "Practical",
        "Project Demo",
        "Assessment"
    )

    if d["examination_type"] not in allowed_types:
        return jsonify(error="Invalid examination type"), 400

    allowed_statuses = (
        "Draft",
        "Slot Creation",
        "Booking Open",
        "Closed",
        "Completed"
    )

    status = d.get("examination_status", "Draft")

    if status not in allowed_statuses:
        return jsonify(error="Invalid examination status"), 400

    with db_session() as c:
        course = c.execute(
            "SELECT id FROM courses WHERE id = ?",
            (course_id,)
        ).fetchone()

        if not course:
            return jsonify(error="Course not found"), 404

        cur = c.execute(
            """
            INSERT INTO examinations (
                course_id,
                examination_name,
                examination_type,
                description,
                duration,
                maximum_marks,
                slot_creation_start,
                slot_creation_end,
                slot_booking_start,
                slot_booking_end,
                examination_status,
                instructions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                course_id,
                d["examination_name"].strip(),
                d["examination_type"],
                d.get("description", ""),
                duration,
                maximum_marks,
                d.get("slot_creation_start"),
                d.get("slot_creation_end"),
                d.get("slot_booking_start"),
                d.get("slot_booking_end"),
                status,
                d.get("instructions", "")
            )
        )

        exam_id = cur.lastrowid

    invalidate()
    return jsonify(
        id=exam_id,
        message="Examination created successfully"
    ), 201


@bp.route("/<int:exam_id>", methods=["GET", "PUT", "DELETE"])
def exam_detail(exam_id):
    user = current_user()

    if request.method in ("PUT", "DELETE"):
        if not user:
            return jsonify(error="Authentication required"), 401

        if user["role"] != "admin":
            return jsonify(error="Insufficient permissions"), 403

    with db_session() as c:

        if request.method == "GET":
            exam = c.execute(
                """
                SELECT e.*, c.course_code, c.course_name
                FROM examinations e
                JOIN courses c ON c.id = e.course_id
                WHERE e.id = ?
                """,
                (exam_id,)
            ).fetchone()

            if not exam:
                return jsonify(error="Examination not found"), 404

            return jsonify(examination=dict(exam))

        if request.method == "PUT":
            d = request.get_json(silent=True) or {}

            exam = c.execute(
                "SELECT id FROM examinations WHERE id = ?",
                (exam_id,)
            ).fetchone()

            if not exam:
                return jsonify(error="Examination not found"), 404

            fields = [
                "course_id",
                "examination_name",
                "examination_type",
                "description",
                "duration",
                "maximum_marks",
                "slot_creation_start",
                "slot_creation_end",
                "slot_booking_start",
                "slot_booking_end",
                "examination_status",
                "instructions"
            ]

            updates = {
                key: d[key]
                for key in fields
                if key in d
            }

            if not updates:
                return jsonify(error="No fields provided to update"), 400

            if "course_id" in updates:
                course = c.execute(
                    "SELECT id FROM courses WHERE id = ?",
                    (updates["course_id"],)
                ).fetchone()

                if not course:
                    return jsonify(error="Course not found"), 404

            if "examination_type" in updates:
                if updates["examination_type"] not in (
                    "Viva",
                    "Practical",
                    "Project Demo",
                    "Assessment"
                ):
                    return jsonify(error="Invalid examination type"), 400

            if "examination_status" in updates:
                if updates["examination_status"] not in (
                    "Draft",
                    "Slot Creation",
                    "Booking Open",
                    "Closed",
                    "Completed"
                ):
                    return jsonify(error="Invalid examination status"), 400

            if "duration" in updates:
                try:
                    if int(updates["duration"]) <= 0:
                        raise ValueError()
                    updates["duration"] = int(updates["duration"])
                except (ValueError, TypeError):
                    return jsonify(error="Duration must be positive"), 400

            if "maximum_marks" in updates:
                try:
                    if float(updates["maximum_marks"]) <= 0:
                        raise ValueError()
                    updates["maximum_marks"] = float(updates["maximum_marks"])
                except (ValueError, TypeError):
                    return jsonify(error="Maximum marks must be positive"), 400

            assignments = ", ".join(
                f"{key} = ?" for key in updates
            )

            values = list(updates.values()) + [exam_id]

            c.execute(
                f"""
                UPDATE examinations
                SET {assignments}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                values
            )

        else:
            has_slots = c.execute(
                "SELECT 1 FROM slots WHERE examination_id = ? LIMIT 1",
                (exam_id,)
            ).fetchone()

            if has_slots:
                c.execute(
                    """
                    UPDATE examinations
                    SET examination_status = 'Closed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (exam_id,)
                )

                invalidate()
                return jsonify(
                    message="Examination has slots/history and was closed rather than deleted"
                )

            c.execute(
                "DELETE FROM examinations WHERE id = ?",
                (exam_id,)
            )

    invalidate()
    return jsonify(
        message=(
            "Examination updated successfully"
            if request.method == "PUT"
            else "Examination deleted successfully"
        )
    )


# Admin assigns an examination to an active examiner.
@bp.post("/<int:exam_id>/assign-examiner")
@require_roles("admin")
def assign_examiner(exam_id):
    d = request.get_json(silent=True) or {}
    examiner_id = d.get("examiner_id")

    if examiner_id in (None, ""):
        return jsonify(error="examiner_id is required"), 400

    try:
        examiner_id = int(examiner_id)
    except (ValueError, TypeError):
        return jsonify(error="examiner_id must be a valid number"), 400

    with db_session() as c:
        exam = c.execute(
            "SELECT id FROM examinations WHERE id = ?",
            (exam_id,)
        ).fetchone()

        if not exam:
            return jsonify(error="Examination not found"), 404

        examiner = c.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?
              AND role = 'examiner'
              AND account_status = 'active'
            """,
            (examiner_id,)
        ).fetchone()

        if not examiner:
            return jsonify(
                error="Active examiner not found"
            ), 404

        existing = c.execute(
            """
            SELECT id
            FROM examination_assignments
            WHERE examination_id = ? AND examiner_id = ?
            """,
            (exam_id, examiner_id)
        ).fetchone()

        if existing:
            return jsonify(
                message="Examiner is already assigned to this examination"
            ), 200

        c.execute(
            """
            INSERT INTO examination_assignments (
                examination_id,
                examiner_id
            )
            VALUES (?, ?)
            """,
            (exam_id, examiner_id)
        )

    invalidate()
    return jsonify(
        message="Examiner assigned successfully",
        examination_id=exam_id,
        examiner_id=examiner_id
    ), 201


# List the examinations assigned to the logged-in examiner.
@bp.get("/assigned-to-me")
@require_roles("examiner")
def assigned_to_me():
    examiner = current_user()

    with db_session() as c:
        rows = c.execute(
            """
            SELECT e.*, c.course_code, c.course_name
            FROM examination_assignments a
            JOIN examinations e ON e.id = a.examination_id
            JOIN courses c ON c.id = e.course_id
            WHERE a.examiner_id = ?
            ORDER BY e.created_at DESC
            """,
            (examiner["id"],)
        ).fetchall()

    return jsonify(items=[dict(row) for row in rows])
@bp.get("/assigned")
@require_roles("examiner")
def assigned_examinations():
    examiner_id = request.current_user["id"]

    with db_session() as c:
        rows = c.execute("""
            SELECT
                e.*,
                co.course_code,
                co.course_name
            FROM examination_assignments AS a
            JOIN examinations AS e
                ON e.id = a.examination_id
            JOIN courses AS co
                ON co.id = e.course_id
            WHERE a.examiner_id = ?
            ORDER BY e.id DESC
        """, (examiner_id,)).fetchall()

    return jsonify(items=[dict(row) for row in rows])