from flask import Blueprint,request,jsonify
from database import db_session
from auth import require_roles
from cache import invalidate
from datetime import datetime
bp=Blueprint("bookings",__name__,url_prefix="/api")

def window_open(start,end):
    now=datetime.now()
    try:return (not start or now>=datetime.fromisoformat(start)) and (not end or now<=datetime.fromisoformat(end))
    except ValueError:return False

@bp.get("/bookings")
@require_roles("student","examiner","admin")
def list_bookings():
    u=request.current_user
    with db_session() as c:
        if u["role"]=="student":
            rows=c.execute("""SELECT b.*,s.exam_date,s.start_time,s.end_time,e.examination_name,c.course_name,ex.name examiner_name
            FROM bookings b JOIN slots s ON s.id=b.slot_id JOIN examinations e ON e.id=s.examination_id
            JOIN courses c ON c.id=e.course_id JOIN users ex ON ex.id=s.examiner_id WHERE b.student_id=? ORDER BY s.exam_date DESC""",(u["id"],)).fetchall()
        elif u["role"]=="examiner":
            rows=c.execute("""SELECT b.*,s.exam_date,s.start_time,e.examination_name,u.name student_name FROM bookings b
            JOIN slots s ON s.id=b.slot_id JOIN examinations e ON e.id=s.examination_id JOIN users u ON u.id=b.student_id
            WHERE s.examiner_id=? ORDER BY s.exam_date""",(u["id"],)).fetchall()
        else:
            rows=c.execute("SELECT * FROM bookings ORDER BY booking_date DESC").fetchall()
    return jsonify(items=[dict(r) for r in rows])

@bp.post("/slots/<int:slot_id>/book")
@require_roles("student","examiner")
def book_slot(slot_id):
    student=request.current_user["id"]
    with db_session() as c:
        c.execute("BEGIN IMMEDIATE")
        s=c.execute("SELECT * FROM slots WHERE id=?",(slot_id,)).fetchone()
        if not s or s["status"]!="Available" or s["available_seats"]<1:return jsonify(error="Slot is unavailable"),409
        e=c.execute("SELECT * FROM examinations WHERE id=?",(s["examination_id"],)).fetchone()
        controls = c.execute(
            "SELECT student_booking_open FROM examination_controls WHERE id = 1"
        ).fetchone()
        if not controls or controls["student_booking_open"] != 1:
            return jsonify(error="Booking is closed by admin"), 403
        if e["examination_status"]!="Booking Open" or not window_open(e["slot_booking_start"],e["slot_booking_end"]):
            return jsonify(error="Booking is not currently open"),403
        existing=c.execute("""SELECT b.id FROM bookings b JOIN slots old ON old.id=b.slot_id
        WHERE b.student_id=? AND old.examination_id=? AND b.status='Booked'""",(student,e["id"])).fetchone()
        if existing:return jsonify(error="You already have a booking for this examination"),409
        c.execute("INSERT INTO bookings(student_id,slot_id,status) VALUES(?,?,'Booked')",(student,slot_id))
        c.execute("UPDATE slots SET available_seats=available_seats-1,status=CASE WHEN available_seats-1=0 THEN 'Full' ELSE 'Available' END,updated_at=CURRENT_TIMESTAMP WHERE id=?",(slot_id,))
        bid=c.execute("SELECT last_insert_rowid() id").fetchone()["id"]
        c.execute("INSERT INTO notifications(user_id,title,message) VALUES(?,?,?)",(student,"Booking confirmed",f"Booking #{bid} confirmed."))
    invalidate(("schedules:","exams:"))
    return jsonify(message="Slot booked",booking_id=bid),201

@bp.post("/bookings/<int:booking_id>/cancel")
@require_roles("student","examiner","admin")
def cancel_booking(booking_id):
    with db_session() as c:
        b=c.execute("SELECT * FROM bookings WHERE id=?",(booking_id,)).fetchone()
        if not b:return jsonify(error="Booking not found"),404
        if request.current_user["role"] in ("student","examiner") and b["student_id"]!=request.current_user["id"]:return jsonify(error="Not your booking"),403
        if b["status"]!="Booked":return jsonify(error="Booking is not active"),409
        s=c.execute("SELECT * FROM slots WHERE id=?",(b["slot_id"],)).fetchone()
        e=c.execute("SELECT * FROM examinations WHERE id=?",(s["examination_id"],)).fetchone()
        if request.current_user["role"] in ("student","examiner") and e["slot_booking_end"] and datetime.now()>datetime.fromisoformat(e["slot_booking_end"]):
            return jsonify(error="Cancellation deadline has passed"),403
        c.execute("UPDATE bookings SET status='Cancelled',updated_at=CURRENT_TIMESTAMP WHERE id=?",(booking_id,))
        c.execute("UPDATE slots SET available_seats=MIN(maximum_capacity,available_seats+1),status='Available',updated_at=CURRENT_TIMESTAMP WHERE id=?",(s["id"],))
    invalidate(("schedules:","exams:"))
    return jsonify(message="Booking cancelled")
