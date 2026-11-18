from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
from database import db_session
from auth import require_roles
from config import Config
from tasks import export_history_csv

bp = Blueprint("exports", __name__, url_prefix="/api/exports")


@bp.post("")
@require_roles("student")
def request_export():
    sid = request.current_user["id"]
    with db_session() as c:
        cur = c.execute("INSERT INTO export_jobs(student_id,status) VALUES(?,'Pending')", (sid,))
        jid = cur.lastrowid
    try:
        task = export_history_csv.delay(jid, sid)
        return jsonify(job_id=jid, task_id=task.id, status="Pending"), 202
    except Exception:
        with db_session() as c:
            c.execute(
                "UPDATE export_jobs SET status='Failed',error_message='Celery worker/broker unavailable',updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (jid,),
            )
        return jsonify(
            error="Could not queue export. Ensure Redis and Celery worker are running.",
            job_id=jid,
        ), 503


@bp.get("/<int:job_id>")
@require_roles("student")
def export_status(job_id):
    with db_session() as c:
        row = c.execute(
            "SELECT id,status,error_message,created_at,updated_at FROM export_jobs WHERE id=? AND student_id=?",
            (job_id, request.current_user["id"]),
        ).fetchone()
    return (jsonify(job=dict(row)), 200) if row else (jsonify(error="Export job not found"), 404)


@bp.get("/<int:job_id>/download")
@require_roles("student")
def download(job_id):
    with db_session() as c:
        row = c.execute(
            "SELECT * FROM export_jobs WHERE id=? AND student_id=?",
            (job_id, request.current_user["id"]),
        ).fetchone()
    if not row:
        return jsonify(error="Export job not found"), 404

    file_path = row["file_path"]
    if row["status"] != "Completed" or not file_path:
        return jsonify(error="Export is not ready"), 409

    target = Path(file_path).resolve()
    export_root = Path(Config.EXPORT_DIR).resolve()
    if target != export_root and export_root not in target.parents:
        return jsonify(error="Export file is not accessible"), 403

    if not target.is_file():
        return jsonify(error="Export file is missing"), 404

    return send_file(target, as_attachment=True, download_name=f"examination-history-{job_id}.csv")
