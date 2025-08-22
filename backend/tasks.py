from .celery_app import app
from .database import SessionLocal
from . import billing_engine

@app.task(name="tasks.run_daily_billing_jobs")
def run_daily_billing_jobs():
    """
    A single Celery task to run all daily billing operations in sequence.
    This task is scheduled by Celery Beat.
    """
    # Each task runs in its own process, so it needs its own DB session.
    db = SessionLocal()
    try:
        print("=============================================")
        print("CELERY TASK: Starting Daily Billing & Suspension Jobs")
        print("=============================================")
        
        billing_engine.generate_invoices_for_due_customers(db)
        
        print("\n---------------------------------------------\n")
        
        billing_engine.suspend_services_for_overdue_customers(db)
        
        print("\n---------------------------------------------\n")

        billing_engine.reactivate_paid_customers_services(db)

        print("\n=============================================\n")
        print("CELERY TASK: Daily jobs completed successfully.")
        return "All billing jobs completed successfully."

    except Exception as e:
        print(f"CELERY TASK ERROR: An unexpected error occurred during the job run: {e}")
        db.rollback()
        # Re-raise the exception so Celery can mark the task as FAILED
        raise
    finally:
        db.close()