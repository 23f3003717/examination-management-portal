import os, sys, getpass
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),"..","backend")))
from database import init_db
from config import Config
if __name__=="__main__":
    email=input(f"Admin email [{Config.ADMIN_EMAIL}]: ").strip() or Config.ADMIN_EMAIL
    name=input(f"Admin name [{Config.ADMIN_NAME}]: ").strip() or Config.ADMIN_NAME
    password=getpass.getpass("Admin password (leave blank to use configured/default development password): ")
    init_db(admin_name=name,admin_email=email,admin_password=password or None)
    print("Initialization completed. If an admin already exists, it is not recreated.")
