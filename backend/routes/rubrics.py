from flask import Blueprint,request,jsonify
from database import db_session
from auth import require_roles
from cache import invalidate, get_client
bp=Blueprint("rubrics",__name__,url_prefix="/api/examinations")

@bp.get("/<int:exam_id>/rubrics")
def list_rubrics(exam_id):
    import json
    key=f"rubrics:exam:{exam_id}"
    client=get_client()
    if client:
        try:
            value=client.get(key)
            if value:return jsonify(items=json.loads(value))
        except Exception:
            pass
    with db_session() as c:
        rows=c.execute("SELECT * FROM rubrics WHERE examination_id=? ORDER BY id",(exam_id,)).fetchall()
    items=[dict(r) for r in rows]
    if client:
        try:client.setex(key,120,json.dumps(items))
        except Exception:pass
    return jsonify(items=items)

@bp.post("/<int:exam_id>/rubrics")
@require_roles("admin")
def add_rubric(exam_id):
    d=request.get_json(silent=True) or {}
    if not d.get("criterion_name") or d.get("maximum_marks") is None:return jsonify(error="criterion_name and maximum_marks are required"),400
    if float(d["maximum_marks"])<0 or float(d.get("weightage",1))<0:return jsonify(error="Marks and weightage must be non-negative"),400
    with db_session() as c:
        exam=c.execute("SELECT maximum_marks FROM examinations WHERE id=?",(exam_id,)).fetchone()
        if not exam:return jsonify(error="Examination not found"),404
        total=c.execute("SELECT COALESCE(SUM(maximum_marks),0) n FROM rubrics WHERE examination_id=?",(exam_id,)).fetchone()["n"]
        if total+float(d["maximum_marks"])>exam["maximum_marks"]:return jsonify(error="Rubric criteria exceed examination maximum marks"),400
        cur=c.execute("INSERT INTO rubrics(examination_id,criterion_name,maximum_marks,weightage,description) VALUES(?,?,?,?,?)",
            (exam_id,d["criterion_name"],float(d["maximum_marks"]),float(d.get("weightage",1)),d.get("description","")))
    invalidate(("rubrics:","exams:"))
    return jsonify(id=cur.lastrowid,message="Rubric created"),201

@bp.route("/rubrics/<int:rubric_id>",methods=["PUT","DELETE"])
@require_roles("admin")
def modify_rubric(rubric_id):
    d=request.get_json(silent=True) or {}
    with db_session() as c:
        r=c.execute("SELECT * FROM rubrics WHERE id=?",(rubric_id,)).fetchone()
        if not r:return jsonify(error="Rubric not found"),404
        if c.execute("SELECT 1 FROM evaluation_criteria WHERE rubric_id=?",(rubric_id,)).fetchone():return jsonify(error="Rubric has historical evaluations and cannot be changed"),409
        if request.method=="DELETE":c.execute("DELETE FROM rubrics WHERE id=?",(rubric_id,))
        else:c.execute("UPDATE rubrics SET criterion_name=?,maximum_marks=?,weightage=?,description=? WHERE id=?",
            (d.get("criterion_name",r["criterion_name"]),d.get("maximum_marks",r["maximum_marks"]),d.get("weightage",r["weightage"]),d.get("description",r["description"]),rubric_id))
    invalidate(("rubrics:","exams:"))
    return jsonify(message="Rubric updated/deleted")
