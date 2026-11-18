from flask import Flask, jsonify
from flask_cors import CORS

from config import Config, resolve_database_path
from database import init_db
from routes.auth_routes import bp as auth_bp
from routes.admin import bp as admin_bp
from routes.courses import bp as courses_bp
from routes.examinations import bp as exams_bp
from routes.rubrics import bp as rubrics_bp
from routes.slots import bp as slots_bp
from routes.bookings import bp as bookings_bp
from routes.evaluations import bp as evaluations_bp
from routes.reports import bp as reports_bp
from routes.exports import bp as exports_bp
from routes.notifications import bp as notifications_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["DATABASE_PATH"] = resolve_database_path(app.config.get("DATABASE_PATH"))

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False  # Set True behind HTTPS in production

    if test_config:
        app.config.update(test_config)
        app.config["DATABASE_PATH"] = resolve_database_path(app.config.get("DATABASE_PATH") or Config.DATABASE_PATH)

    # Allow the local Vue frontend to call the Flask API, including session cookies.
    # Keep the allowed origins explicit; do not use "*" with credentials.
    allowed_origins = [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    # Also include the configured frontend origin, if it is set.
    configured_origin = app.config.get("FRONTEND_ORIGIN")
    if configured_origin and configured_origin not in allowed_origins:
        allowed_origins.append(configured_origin.rstrip("/"))

    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    with app.app_context():
        init_db(
            app.config.get("DATABASE_PATH"),
            app.config.get("ADMIN_NAME"),
            app.config.get("ADMIN_EMAIL"),
            app.config.get("ADMIN_PASSWORD"),
        )

    for bp in [
        auth_bp,
        admin_bp,
        courses_bp,
        exams_bp,
        rubrics_bp,
        slots_bp,
        bookings_bp,
        evaluations_bp,
        reports_bp,
        exports_bp,
        notifications_bp,
    ]:
        app.register_blueprint(bp)

    @app.get("/api/health")
    def health():
        from cache import get_client

        redis_ok = bool(get_client())
        return jsonify(
            status="ok",
            database="configured",
            redis="available" if redis_ok else "unavailable",
            celery="configured; worker status requires separate check",
        )

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Resource not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error="Internal server error"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
