from flask import Blueprint,request,jsonify
from database import db_session
from auth import require_roles
bp=Blueprint("evaluations",__name__,url_prefix="/api")

@bp.get("/examiner/examinations")
@require_roles("examiner")
def assigned_exams():
    with db_session() as c:
        rows=c.execute("""SELECT DISTINCT e.*,c.course_name FROM examinations e
        JOIN courses c ON c.id=e.course_id
        WHERE e.examination_status='Slot Creation' OR e.id IN
          (SELECT examination_id FROM slots WHERE examiner_id=?)
        ORDER BY e.created_at DESC""",(request.current_user["id"],)).fetchall()
    return jsonify(items=[dict(r) for r in rows])


@bp.get("/examiner/slots")
@require_roles("examiner")
def examiner_slots():
    with db_session() as c:
        rows=c.execute("""SELECT s.*,e.examination_name,e.maximum_marks,e.examination_status,
        (SELECT COUNT(*) FROM bookings b WHERE b.slot_id=s.id AND b.status='Booked') booked_students,
        (SELECT COUNT(*) FROM bookings b LEFT JOIN evaluations ev ON ev.booking_id=b.id
         WHERE b.slot_id=s.id AND b.status IN ('Booked','Completed') AND ev.id IS NULL) pending_evaluations
        FROM slots s JOIN examinations e ON e.id=s.examination_id
        WHERE s.examiner_id=? ORDER BY s.exam_date,s.start_time""",(request.current_user["id"],)).fetchall()
    return jsonify(items=[dict(r) for r in rows])

@bp.post("/examiner/examinations/<int:exam_id>/complete")
@require_roles("examiner")
def complete_examination(exam_id):
    with db_session() as c:
        assigned=c.execute("SELECT 1 FROM slots WHERE examination_id=? AND examiner_id=? LIMIT 1",(exam_id,request.current_user["id"])).fetchone()
        if not assigned:return jsonify(error="This examination is not assigned to you"),403
        c.execute("UPDATE examinations SET examination_status='Completed',updated_at=CURRENT_TIMESTAMP WHERE id=?",(exam_id,))
        c.execute("UPDATE slots SET status='Completed',updated_at=CURRENT_TIMESTAMP WHERE examination_id=? AND examiner_id=? AND status!='Cancelled'",(exam_id,request.current_user["id"]))
    return jsonify(message="Examination marked as completed")

@bp.get("/examiner/slots/<int:slot_id>/students")
@require_roles("examiner")
def slot_students(slot_id):
    with db_session() as c:
        s=c.execute("SELECT * FROM slots WHERE id=?",(slot_id,)).fetchone()
        if not s:return jsonify(error="Slot not found"),404
        if s["examiner_id"]!=request.current_user["id"]:return jsonify(error="Not your slot"),403
        rows=c.execute("""SELECT b.id booking_id,b.status booking_status,u.id student_id,u.name student_name,u.email,
        ev.id evaluation_id,ev.total_marks,ev.remarks,ev.evaluation_status FROM bookings b JOIN users u ON u.id=b.student_id
        LEFT JOIN evaluations ev ON ev.booking_id=b.id WHERE b.slot_id=? ORDER BY u.name""",(slot_id,)).fetchall()
    return jsonify(items=[dict(r) for r in rows])

@bp.post("/bookings/<int:booking_id>/evaluation")
@require_roles("examiner")
def evaluate(booking_id):
    d=request.get_json(silent=True) or {}
    marks=d.get("criteria",[])
    with db_session() as c:
        b=c.execute("""SELECT b.*,s.examiner_id,s.examination_id FROM bookings b JOIN slots s ON s.id=b.slot_id WHERE b.id=?""",(booking_id,)).fetchone()
        if not b:return jsonify(error="Booking not found"),404
        if b["examiner_id"]!=request.current_user["id"]:return jsonify(error="You cannot evaluate this booking"),403
        if b["status"] not in ("Booked","Completed"):return jsonify(error="Booking is not eligible for evaluation"),409
        if c.execute("SELECT id FROM evaluations WHERE booking_id=?",(booking_id,)).fetchone():return jsonify(error="Evaluation already submitted"),409
        exam=c.execute("SELECT maximum_marks FROM examinations WHERE id=?",(b["examination_id"],)).fetchone()
        rubrics=c.execute("SELECT * FROM rubrics WHERE examination_id=?",(b["examination_id"],)).fetchall()
        rubric_map={r["id"]:r for r in rubrics}
        total=0
        for item in marks:
            rid=int(item.get("rubric_id",0)); val=float(item.get("marks",-1))
            if rid not in rubric_map or val<0 or val>rubric_map[rid]["maximum_marks"]:return jsonify(error="Invalid rubric marks"),400
            total+=val
        if total>exam["maximum_marks"] or total<0:return jsonify(error="Total marks exceed examination maximum"),400
        if rubrics and {int(x.get("rubric_id",0)) for x in marks}!={r["id"] for r in rubrics}:
            return jsonify(error="Submit marks for every rubric criterion"),400
        cur=c.execute("INSERT INTO evaluations(booking_id,student_id,examiner_id,total_marks,remarks) VALUES(?,?,?,?,?)",
            (booking_id,b["student_id"],request.current_user["id"],total,d.get("remarks","")))
        for item in marks:c.execute("INSERT INTO evaluation_criteria(evaluation_id,rubric_id,marks) VALUES(?,?,?)",(cur.lastrowid,int(item["rubric_id"]),float(item["marks"])))
        c.execute("UPDATE bookings SET status='Completed',updated_at=CURRENT_TIMESTAMP WHERE id=?",(booking_id,))
    return jsonify(message="Evaluation submitted",total_marks=total),201

@bp.get("/student/results")
@require_roles("student","examiner")
def student_results():
    with db_session() as c:
        rows=c.execute("""SELECT e.examination_name,c.course_name,ev.total_marks,e.maximum_marks,ev.remarks,ev.evaluated_at,
        ex.name examiner_name,b.status booking_status FROM evaluations ev JOIN bookings b ON b.id=ev.booking_id
        JOIN slots s ON s.id=b.slot_id JOIN examinations e ON e.id=s.examination_id JOIN courses c ON c.id=e.course_id
        JOIN users ex ON ex.id=ev.examiner_id WHERE ev.student_id=? AND e.results_published=1 ORDER BY ev.evaluated_at DESC""",(request.current_user["id"],)).fetchall()
    return jsonify(items=[dict(r) for r in rows])
