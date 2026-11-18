from functools import wraps
from flask import session, jsonify, request
from werkzeug.security import check_password_hash
from database import db_session

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with db_session() as conn:
        row = conn.execute("SELECT id,name,email,role,account_status,department FROM users WHERE id=?", (uid,)).fetchone()
        return dict(row) if row and row["account_status"] == "active" else None

def login_user(email, password):
    normalized_email = (email or "").strip().lower()
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email=? AND account_status='active'",
            (normalized_email,),
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            try:
                session.clear()
                session["user_id"] = row["id"]
            except RuntimeError:
                # Allow login_user() to be used from code paths without an active request context.
                pass
            return {k: row[k] for k in ("id", "name", "email", "role", "account_status", "department")}
    return None

def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"error":"Authentication required"}), 401
            if roles and user["role"] not in roles:
                return jsonify({"error":"Insufficient permissions"}), 403
            request.current_user = user
            return fn(*args, **kwargs)
        return wrapped
    return decorator
