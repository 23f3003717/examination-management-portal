
from flask import Blueprint, request, jsonify
from database import db_session
from cache import get_client, invalidate
from auth import require_roles
from datetime import datetime, date, time
import json

bp = Blueprint("slots", __name__, url_prefix="/api/slots")


def in_window(start, end):
    """Check whether the current local time is inside a configured window."""
    now = datetime.now()

    try:
        start_dt = datetime.fromisoformat(start) if start else None
        end_dt = datetime.fromisoformat(end) if end else None

        return (
            (start_dt is None or now >= start_dt)
            and (end_dt is None or now <= end_dt)
        )
    except (ValueError, TypeError):
        return False


def valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def valid_time(value):
    try:
        time.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def invalidate_slot_cache():
    invalidate(("schedules:", "exams:"))


@bp.get("")
def list_slots():
    args = request.args
    where = []
    params = []

    if args.get("examination_id"):
        where.append("s.examination_id = ?")
        params.append(args["examination_id"])

    if args.get("date"):
        where.append("s.exam_date = ?")
        params.append(args["date"])

    if args.get("available") == "1":
        where.append(
            "s.status = 'Available' AND s.available_seats > 0"
        )

    sql = """
        SELECT
            s.*,
            e.examination_name,
            ex.name AS examiner_name
        FROM slots s
        JOIN examinations e ON e.id = s.examination_id
        JOIN users ex ON ex.id = s.examiner_id
    """

    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " ORDER BY s.exam_date, s.start_time"

    key = (
        "schedules:"
        + str(args.get("examination_id", ""))
        + ":"
        + str(args.get("date", ""))
        + ":"
        + str(args.get("available", ""))
    )

    client = get_client()

    if client:
        try:
            cached_value = client.get(key)
            if cached_value:
                return jsonify(items=json.loads(cached_value))
        except Exception:
            pass

    with db_session() as c:
        rows = c.execute(sql, params).fetchall()

    items = [dict(row) for row in rows]

    if client:
        try:
            client.setex(key, 60, json.dumps(items))
        except Exception:
            pass

    return jsonify(items=items)


@bp.post("")
@require_roles("examiner")
def create_slot():
    data = request.get_json(silent=True) or {}

    required_fields = (
        "examination_id",
        "exam_date",
        "start_time",
        "end_time",
        "maximum_capacity",
    )

    for field in required_fields:
        if data.get(field) in (None, ""):
            return jsonify(error=f"{field} is required"), 400

    examination_id = data.get("examination_id")
    capacity = data.get("maximum_capacity")

    try:
        examination_id = int(examination_id)
        capacity = int(capacity)
    except (ValueError, TypeError):
        return jsonify(
            error="examination_id and maximum_capacity must be integers"
        ), 400

    exam_date = data["exam_date"]
    start_time = data["start_time"]
    end_time = data["end_time"]

    if not valid_date(exam_date):
        return jsonify(error="exam_date must use YYYY-MM-DD format"), 400

    if not valid_time(start_time) or not valid_time(end_time):
        return jsonify(error="Times must use HH:MM or HH:MM:SS format"), 400

    if start_time >= end_time:
        return jsonify(error="end_time must be after start_time"), 400

    if capacity < 1:
        return jsonify(error="Capacity must be positive"), 400

    examiner_id = request.current_user["id"]

    with db_session() as c:
        exam = c.execute(
            "SELECT * FROM examinations WHERE id = ?",
            (examination_id,),
        ).fetchone()

        if not exam:
            return jsonify(error="Examination not found"), 404

        assignment = c.execute(
            """
            SELECT id
            FROM examination_assignments
            WHERE examination_id = ? AND examiner_id = ?
            """,
            (examination_id, examiner_id),
        ).fetchone()

        if not assignment:
            return jsonify(
                error="This examination has not been assigned to you by Admin"
            ), 403

        controls = c.execute(
            "SELECT slot_creation_open FROM examination_controls WHERE id = 1"
        ).fetchone()
        if not controls or controls["slot_creation_open"] != 1:
            return jsonify(
                error="Slot creation is closed by admin"
            ), 403

        if exam["examination_status"] != "Slot Creation":
            return jsonify(
                error=(
                    "Examination status must be 'Slot Creation' "
                    "before slots can be created"
                )
            ), 403

        if not in_window(
            exam["slot_creation_start"],
            exam["slot_creation_end"],
        ):
            return jsonify(
                error="Slot creation is outside the configured time window"
            ), 403

        overlap = c.execute(
            """
            SELECT id
            FROM slots
            WHERE examiner_id = ?
              AND exam_date = ?
              AND status != 'Cancelled'
              AND start_time < ?
              AND end_time > ?
            """,
            (examiner_id, exam_date, end_time, start_time),
        ).fetchone()

        if overlap:
            return jsonify(
                error="This slot overlaps another slot assigned to you"
            ), 409

        try:
            cur = c.execute(
                """
                INSERT INTO slots (
                    examination_id,
                    examiner_id,
                    exam_date,
                    start_time,
                    end_time,
                    maximum_capacity,
                    available_seats,
                    meeting_link
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    examination_id,
                    examiner_id,
                    exam_date,
                    start_time,
                    end_time,
                    capacity,
                    capacity,
                    data.get("meeting_link", ""),
                ),
            )
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                return jsonify(
                    error=(
                        "A slot already exists for this examiner "
                        "at that date and start time"
                    )
                ), 409
            raise

        slot_id = cur.lastrowid

    invalidate_slot_cache()

    return jsonify(
        id=slot_id,
        message="Slot created successfully",
    ), 201


@bp.route("/<int:slot_id>", methods=["PUT", "DELETE"])
@require_roles("examiner", "admin")
def modify_slot(slot_id):
    data = request.get_json(silent=True) or {}

    with db_session() as c:
        slot = c.execute(
            "SELECT * FROM slots WHERE id = ?",
            (slot_id,),
        ).fetchone()

        if not slot:
            return jsonify(error="Slot not found"), 404

        user = request.current_user

        if (
            user["role"] == "examiner"
            and slot["examiner_id"] != user["id"]
        ):
            return jsonify(error="This is not your slot"), 403

        exam = c.execute(
            "SELECT * FROM examinations WHERE id = ?",
            (slot["examination_id"],),
        ).fetchone()

        if not exam:
            return jsonify(error="Examination not found"), 404

        booked = c.execute(
            """
            SELECT COUNT(*) AS n
            FROM bookings
            WHERE slot_id = ? AND status = 'Booked'
            """,
            (slot_id,),
        ).fetchone()["n"]

        try:
            booking_started = (
                bool(exam["slot_booking_start"])
                and datetime.now()
                >= datetime.fromisoformat(exam["slot_booking_start"])
            )
        except (ValueError, TypeError):
            booking_started = True

        if booked or booking_started:
            return jsonify(
                error=(
                    "Slots cannot be changed after booking begins "
                    "or active bookings exist"
                )
            ), 409

        if slot["status"] in ("Cancelled", "Completed"):
            return jsonify(
                error="Cancelled or completed slots cannot be modified"
            ), 409

        if request.method == "DELETE":
            c.execute(
                """
                UPDATE slots
                SET status = 'Cancelled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (slot_id,),
            )
            message = "Slot cancelled successfully"

        else:
            try:
                capacity = int(
                    data.get("maximum_capacity", slot["maximum_capacity"])
                )
            except (ValueError, TypeError):
                return jsonify(error="Invalid maximum_capacity"), 400

            if capacity < 1:
                return jsonify(error="Capacity must be positive"), 400

            exam_date = data.get("exam_date", slot["exam_date"])
            start_time = data.get("start_time", slot["start_time"])
            end_time = data.get("end_time", slot["end_time"])

            if not valid_date(exam_date):
                return jsonify(error="Invalid exam_date"), 400

            if not valid_time(start_time) or not valid_time(end_time):
                return jsonify(error="Invalid start_time or end_time"), 400

            if start_time >= end_time:
                return jsonify(
                    error="end_time must be after start_time"
                ), 400

            overlap = c.execute(
                """
                SELECT id
                FROM slots
                WHERE examiner_id = ?
                  AND exam_date = ?
                  AND status != 'Cancelled'
                  AND id != ?
                  AND start_time < ?
                  AND end_time > ?
                """,
                (
                    slot["examiner_id"],
                    exam_date,
                    slot_id,
                    end_time,
                    start_time,
                ),
            ).fetchone()

            if overlap:
                return jsonify(
                    error="This slot overlaps another slot assigned to you"
                ), 409

            seats_used = (
                slot["maximum_capacity"] - slot["available_seats"]
            )

            if capacity < seats_used:
                return jsonify(
                    error=(
                        "Capacity cannot be less than the number "
                        "of already booked students"
                    )
                ), 400

            available_seats = capacity - seats_used
            status = "Full" if available_seats == 0 else "Available"

            c.execute(
                """
                UPDATE slots
                SET exam_date = ?,
                    start_time = ?,
                    end_time = ?,
                    maximum_capacity = ?,
                    available_seats = ?,
                    status = ?,
                    meeting_link = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    exam_date,
                    start_time,
                    end_time,
                    capacity,
                    available_seats,
                    status,
                    data.get("meeting_link", slot["meeting_link"]),
                    slot_id,
                ),
            )

            message = "Slot updated successfully"

    invalidate_slot_cache()

    return jsonify(message=message)
