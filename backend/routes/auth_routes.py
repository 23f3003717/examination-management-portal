from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from database import db_session
from auth import login_user, current_user, require_roles

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name, email, password = (data.get("name") or "").strip(), (data.get("email") or "").strip().lower(), data.get("password") or ""
    if not name or "@" not in email or len(password) < 8:
        return jsonify(error="Name, valid email and password of at least 8 characters are required"), 400
    try:
        with db_session() as conn:
            conn.execute("INSERT INTO users(name,email,password_hash,role,contact_details) VALUES(?,?,?,'student',?)",
                         (name,email,generate_password_hash(password),data.get("contact_details","")))
    except Exception as exc:
        if "UNIQUE" in str(exc):
            return jsonify(error="An account with this email already exists"), 409
        raise
    return jsonify(message="Student account created"), 201

@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = login_user(data.get("email",""), data.get("password",""))
    if not user:
        return jsonify(error="Invalid credentials or inactive account"), 401
    return jsonify(user=user)

@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out")

@bp.get("/me")
def me():
    user = current_user()
    return (jsonify(user=user), 200) if user else (jsonify(error="Authentication required"), 401)


@bp.get("/profile")
@require_roles("student")
def get_profile():
    user = request.current_user
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, name, email, role, account_status, contact_details, department, created_at FROM users WHERE id=?",
            (user["id"],),
        ).fetchone()
    return jsonify(user=dict(row))


@bp.put("/profile")
@require_roles("student")
def update_profile():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    department = (data.get("department") or "").strip()
    contact_details = (data.get("contact_details") or "").strip()
    if not name:
        return jsonify(error="Name is required"), 400
    if len(name) > 120 or len(department) > 120 or len(contact_details) > 500:
        return jsonify(error="Profile fields exceed their allowed length"), 400
    with db_session() as conn:
        conn.execute(
            "UPDATE users SET name=?, department=?, contact_details=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (name, department, contact_details, request.current_user["id"]),
        )
        row = conn.execute(
            "SELECT id, name, email, role, account_status, contact_details, department, created_at FROM users WHERE id=?",
            (request.current_user["id"],),
        ).fetchone()
    return jsonify(message="Profile updated", user=dict(row))
