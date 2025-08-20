from sqlalchemy.orm import Session
from datetime import date
import crud
import schemas

def generate_invoices_for_due_customers(db: Session):
    """
    Main function for the billing run. Generates invoices for all customers due today.
    This function is intended to be called by a scheduled job (e.g., daily cron).
    """
    today = date.today()
    billing_day = today.day
    print(f"--- Starting invoice generation for billing day: {billing_day} ---")

    customers_to_bill = crud.get_customers_due_for_billing(db, billing_day=billing_day)
    print(f"Found {len(customers_to_bill)} customer(s) due for billing.")

    for customer in customers_to_bill:
        print(f"Processing customer: {customer.name} (ID: {customer.id})")
        
        # Aggregate all active services for the customer
        active_services = crud.get_internet_services(db, customer_id=customer.id, limit=100)
        
        if not active_services:
            print(f"  -> No active services found for customer {customer.id}. Skipping.")
            continue

        invoice_items = []
        for service in active_services:
            if service.status == 'active':
                invoice_items.append(schemas.InvoiceItemCreate(
                    description=f"{service.description} (Tariff: {service.tariff.title})",
                    quantity=1,
                    price=service.tariff.price
                ))
        
        if not invoice_items:
            print(f"  -> No billable (active) services found for customer {customer.id}. Skipping.")
            continue

        invoice_create_schema = schemas.InvoiceCreate(
            customer_id=customer.id,
            items=invoice_items
        )

        try:
            new_invoice = crud.create_invoice(db, invoice=invoice_create_schema)
            print(f"  -> Successfully created Invoice #{new_invoice.number} for customer {customer.id} with {len(invoice_items)} item(s).")
        except Exception as e:
            print(f"  -> ERROR: Failed to create invoice for customer {customer.id}. Reason: {e}")

    print("--- Invoice generation complete. ---")


def suspend_services_for_overdue_customers(db: Session):
    """
    Finds customers with overdue invoices and suspends their active services.
    This function is intended to be called by a scheduled job (e.g., daily cron).
    """
    print("--- Starting suspension process for overdue customers ---")
    
    overdue_customers = crud.get_customers_with_overdue_invoices(db)
    print(f"Found {len(overdue_customers)} customer(s) with overdue invoices.")

    for customer in overdue_customers:
        print(f"Processing overdue customer: {customer.name} (ID: {customer.id})")
        
        active_services = crud.get_internet_services(db, customer_id=customer.id, limit=100)
        
        for service in active_services:
            if service.status == 'active':
                try:
                    service_update = schemas.InternetServiceUpdate(status='blocked')
                    crud.update_internet_service(db, service_id=service.id, service_update=service_update)
                    print(f"  -> Suspended service ID: {service.id} ('{service.description}')")
                except Exception as e:
                    print(f"  -> ERROR: Failed to suspend service {service.id}. Reason: {e}")

    print("--- Suspension process complete. ---")


def reactivate_paid_customers_services(db: Session):
    """
    Finds customers who have paid off their balance but still have blocked services,
    and reactivates them. This acts as a reconciliation job.
    """
    print("--- Starting reconciliation for service reactivation ---")
    
    customers_to_reactivate = crud.get_customers_to_reactivate(db)
    print(f"Found {len(customers_to_reactivate)} customer(s) eligible for service reactivation.")

    for customer in customers_to_reactivate:
        print(f"Processing paid-up customer: {customer.name} (ID: {customer.id})")
        
        reactivated_count = crud.reactivate_customer_services(db, customer_id=customer.id)
        
        if reactivated_count > 0:
            try:
                db.commit()
                print(f"  -> Reactivated {reactivated_count} service(s).")
            except Exception as e:
                print(f"  -> ERROR: Failed to commit reactivation for customer {customer.id}. Reason: {e}")
                db.rollback()

    print("--- Reactivation reconciliation complete. ---")