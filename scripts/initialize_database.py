import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),"..","backend")))
from database import init_db
if __name__=="__main__":
    init_db()
    print("Database initialized. Admin account is created if absent.")
    print("Configure ADMIN_EMAIL and ADMIN_PASSWORD before first initialization.")
