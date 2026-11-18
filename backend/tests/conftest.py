import os, tempfile, pytest
from app import create_app
@pytest.fixture
def client():
    fd,path=tempfile.mkstemp(suffix=".sqlite3");os.close(fd)
    app=create_app({"TESTING":True,"DATABASE_PATH":path,"SECRET_KEY":"test-secret","ADMIN_EMAIL":"admin@test.local","ADMIN_PASSWORD":"TestAdmin123!"})
    with app.test_client() as c:yield c
    os.unlink(path)
def login(client,email,password):
    return client.post("/api/auth/login",json={"email":email,"password":password})
