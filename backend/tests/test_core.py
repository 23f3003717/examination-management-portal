from tests.conftest import login
def test_course_requires_admin(client):
    assert client.post("/api/courses",json={"course_code":"MAD2","course_name":"Modern Application Development II"}).status_code==401
    login(client,"admin@test.local","TestAdmin123!")
    r=client.post("/api/courses",json={"course_code":"MAD2","course_name":"Modern Application Development II"})
    assert r.status_code==201
    assert client.get("/api/courses").json["items"][0]["course_code"]=="MAD2"
def test_student_cannot_open_admin_dashboard(client):
    client.post("/api/auth/register",json={"name":"Student","email":"s@test.local","password":"Student123!"})
    login(client,"s@test.local","Student123!")
    assert client.get("/api/admin/dashboard").status_code==403
