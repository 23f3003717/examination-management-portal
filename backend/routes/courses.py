from flask import Blueprint, request, jsonify
from database import db_session
from auth import require_roles
from cache import invalidate
bp=Blueprint("courses",__name__,url_prefix="/api/courses")

@bp.get("")
def list_courses():
    with db_session() as c:
        rows=c.execute("SELECT * FROM courses ORDER BY course_name").fetchall()
    return jsonify(items=[dict(r) for r in rows])

@bp.post("")
@require_roles("admin")
def create_course():
    d=request.get_json(silent=True) or {}
    if not d.get("course_code") or not d.get("course_name"): return jsonify(error="course_code and course_name are required"),400
    try:
        with db_session() as c:
            cur=c.execute("INSERT INTO courses(course_code,course_name,description,status) VALUES(?,?,?,?)",
                (d["course_code"].strip().upper(),d["course_name"].strip(),d.get("description",""),d.get("status","active")))
    except Exception as e:
        if "UNIQUE" in str(e): return jsonify(error="Course code already exists"),409
        raise
    return jsonify(id=cur.lastrowid,message="Course created"),201

@bp.route("/<int:course_id>",methods=["PUT","DELETE"])
@require_roles("admin")
def modify_course(course_id):
    with db_session() as c:
        if request.method == "PUT":
            d = request.get_json(silent=True) or {}
            cur = c.execute(
                "UPDATE courses SET course_code=?,course_name=?,description=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (d.get("course_code"), d.get("course_name"), d.get("description", ""), d.get("status", "active"), course_id),
            )
            if not cur.rowcount:
                return jsonify(error="Course not found"), 404
        else:
            exam_ids = [
                row["id"]
                for row in c.execute("SELECT id FROM examinations WHERE course_id=?", (course_id,)).fetchall()
            ]

            for exam_id in exam_ids:
                c.execute("DELETE FROM evaluation_criteria WHERE rubric_id IN (SELECT id FROM rubrics WHERE examination_id=?)", (exam_id,))
                c.execute("DELETE FROM evaluations WHERE booking_id IN (SELECT id FROM bookings WHERE slot_id IN (SELECT id FROM slots WHERE examination_id=?))", (exam_id,))
                c.execute("DELETE FROM bookings WHERE slot_id IN (SELECT id FROM slots WHERE examination_id=?)", (exam_id,))
                c.execute("DELETE FROM slots WHERE examination_id=?", (exam_id,))
                c.execute("DELETE FROM examination_assignments WHERE examination_id=?", (exam_id,))
                c.execute("DELETE FROM rubrics WHERE examination_id=?", (exam_id,))
                c.execute("DELETE FROM examinations WHERE id=?", (exam_id,))

            cur = c.execute("DELETE FROM courses WHERE id=?", (course_id,))
            if not cur.rowcount:
                return jsonify(error="Course not found"), 404

    invalidate()
    return jsonify(message="Course updated" if request.method == "PUT" else "Course deleted successfully")
