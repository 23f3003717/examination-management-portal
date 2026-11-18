
from flask import Blueprint, jsonify
from database import db_session
from auth import require_roles

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.get("/summary")
@require_roles("admin")
def summary():
    with db_session() as c:
        # Examination status summary
        status = c.execute("""
            SELECT
                examination_status,
                COUNT(*) AS count
            FROM examinations
            GROUP BY examination_status
            ORDER BY examination_status
        """).fetchall()

        # Examination type summary
        types = c.execute("""
            SELECT
                examination_type,
                COUNT(*) AS count
            FROM examinations
            GROUP BY examination_type
            ORDER BY examination_type
        """).fetchall()

        # Examiner workload:
        # Count assignments from examination_assignments
        # and slots from the slots table separately.
        workload = c.execute("""
            SELECT
                u.id AS examiner_id,
                u.name AS name,
                COUNT(DISTINCT a.examination_id) AS examinations,
                COUNT(DISTINCT s.id) AS slots
            FROM users u
            LEFT JOIN examination_assignments a
                ON a.examiner_id = u.id
            LEFT JOIN slots s
                ON s.examiner_id = u.id
            WHERE u.role = 'examiner'
            GROUP BY u.id, u.name
            ORDER BY examinations DESC, slots DESC, u.name
        """).fetchall()

    return jsonify(
        status=[dict(row) for row in status],
        types=[dict(row) for row in types],
        examiner_workload=[dict(row) for row in workload]
    )
