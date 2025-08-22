from sqlalchemy.orm import Session
from datetime import date, timedelta
import crud
import schemas
from decimal import Decimal

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
        active_services = crud.get_internet_services(db, customer_id=customer.id, status='active', limit=1000)

        if not active_services:
            print(f"  -> No active services found for customer {customer.id}. Skipping.")
            continue

        invoice_items = []
        for service in active_services:
            # More complex logic for discounts, pro-rating, etc. would go here
            invoice_items.append(schemas.InvoiceItemCreate(
                description=f"{service.description} (Tariff: {service.tariff.title})",
                quantity=1,
                price=service.tariff.price or Decimal('0.0')
            ))

        if not invoice_items:
            print(f"  -> No billable (active) services found for customer {customer.id}. Skipping.")
            continue

        # --- Business Logic for Invoice Creation ---
        # 1. Calculate total
        total_amount = sum(item.price * item.quantity for item in invoice_items)

        # 2. Generate a robust invoice number (e.g., from a sequence or based on date)
        # This is a safer approach than count-based numbering.
        invoice_count_for_month = db.query(crud.models.Invoice).filter(crud.models.Invoice.date_created >= today.replace(day=1)).count()
        invoice_number = f"INV-{today.strftime('%Y-%m')}-{invoice_count_for_month + 1:04d}"

        # 3. Determine due date
        due_date = today + timedelta(days=customer.billing_config.billing_due if customer.billing_config else 14)

        invoice_create_schema = schemas.InvoiceCreate(
            customer_id=customer.id,
            items=invoice_items,
            number=invoice_number,
            total=total_amount,
            due=total_amount,
            date_till=due_date
        )

        try:
            new_invoice = crud.create_invoice(db, invoice=invoice_create_schema)
            print(f"  -> Successfully created Invoice #{new_invoice.number} for customer {customer.id} with {len(invoice_items)} item(s).")
        except Exception as e:
            print(f"  -> ERROR: Failed to create invoice for customer {customer.id}. Reason: {e}")

    db.commit() # Commit all generated invoices at the end of the run
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

        # Update customer status
        if customer.status != 'blocked':
            customer.status = 'blocked'
            print(f"  -> Set customer status to 'blocked'")

        # Suspend all active services for the customer
        services_to_suspend = db.query(crud.models.InternetService).filter(
            crud.models.InternetService.customer_id == customer.id,
            crud.models.InternetService.status == 'active'
        )
        updated_count = services_to_suspend.update({"status": "blocked"}, synchronize_session=False)
        print(f"  -> Suspended {updated_count} active service(s).")

    db.commit() # Commit all suspensions at once
    print("--- Suspension process complete. ---")


def reactivate_paid_customers_services(db: Session):
    """
    Finds customers who have paid off their balance but still have blocked services,
    and reactivates them. This acts as a reconciliation job.
    """
    print("--- Starting reconciliation for service reactivation ---")
    
    customers_to_reactivate = crud.get_customers_to_reactivate(db)
    print(f"Found {len(customers_to_reactivate)} customer(s) eligible for service reactivation.")

    total_reactivated_count = 0
    for customer in customers_to_reactivate:
        print(f"Processing paid-up customer: {customer.name} (ID: {customer.id})")
        
        reactivated_count = crud.reactivate_customer_services(db, customer_id=customer.id)
        
        if reactivated_count > 0:
            # Also update the customer's status back to 'active' if they were blocked
            if customer.status == 'blocked':
                customer.status = 'active'
                print(f"  -> Set customer status to 'active'")

            total_reactivated_count += reactivated_count
            print(f"  -> Staged reactivation for {reactivated_count} service(s).")

    if total_reactivated_count > 0:
        db.commit()
        print(f"Committed a total of {total_reactivated_count} service reactivations.")
    print("--- Reactivation reconciliation complete. ---")