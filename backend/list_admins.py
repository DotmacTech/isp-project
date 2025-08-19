
import os
import sys
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import models

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def list_admin_accounts():
    db: Session = SessionLocal()
    try:
        administrators = crud.get_administrators(db)
        if not administrators:
            print("No administrator accounts found.")
            return

        print("Administrator Accounts:")
        print("---------------------")
        for admin in administrators:
            user = crud.get_user(db, admin.user_id)
            if user:
                print(f"ID: {admin.id}")
                print(f"  User ID: {user.id}")
                print(f"  Email: {user.email}")
                print(f"  Full Name: {user.full_name}")
                print(f"  Partner ID: {admin.partner_id}")
                print(f"  Is Active: {user.is_active}")
                print("---------------------")
            else:
                print(f"Administrator ID: {admin.id} (User not found for this admin profile)")
                print("---------------------")
    finally:
        db.close()

if __name__ == "__main__":
    list_admin_accounts()
