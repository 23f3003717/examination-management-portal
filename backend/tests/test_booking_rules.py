from tests.conftest import login

def test_student_registration_and_role(client):
    r=client.post("/api/auth/register",json={"name":"Demo Student","email":"demo@student.test","password":"StrongPass123!"})
    assert r.status_code==201
    login(client,"demo@student.test","StrongPass123!")
    assert client.get("/api/auth/me").json["user"]["role"]=="student"
