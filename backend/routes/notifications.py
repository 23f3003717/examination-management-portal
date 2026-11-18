from flask import Blueprint,jsonify,request
from database import db_session
from auth import require_roles
bp=Blueprint("notifications",__name__,url_prefix="/api/notifications")
@bp.get("")
@require_roles("admin","examiner","student")
def notifications():
    with db_session() as c:
        rows=c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 100",(request.current_user["id"],)).fetchall()
    return jsonify(items=[dict(r) for r in rows])
