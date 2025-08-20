import os
import sys
from sqlalchemy.orm import Session

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal
from billing_engine import generate_invoices_for_due_customers, suspend_services_for_overdue_customers, reactivate_paid_customers_services

def run_jobs():
    """
    Entry point for the scheduled job.
    This script runs the daily billing and suspension tasks.
    """
    db: Session = SessionLocal()
    try:
        print("=============================================")
        print("Starting Daily Billing & Suspension Jobs")
        print("=============================================")
        
        generate_invoices_for_due_customers(db)
        
        print("\n---------------------------------------------\n")
        
        suspend_services_for_overdue_customers(db)
        
        print("\n---------------------------------------------\n")

        reactivate_paid_customers_services(db)

        print("\n=============================================\n")
        
    except Exception as e:
        print(f"An unexpected error occurred during the job run: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_jobs()