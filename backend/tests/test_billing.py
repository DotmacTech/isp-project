from datetime import date, timedelta
from decimal import Decimal
import pytest

from billing_engine import (
    generate_invoices_for_due_customers,
    suspend_services_for_overdue_customers,
    reactivate_paid_customers_services,
)
import crud
import schemas
from models import Invoice, Customer, InternetService

# Test for billing_engine functions (no API calls)

def test_generate_invoices_for_due_customers(db_session, test_customer, test_service):
    """
    Test that invoices are generated only for customers due for billing today.
    """
    # test_customer is configured to be due today by the fixture
    
    # Create another customer who is not due today
    tomorrow = date.today() + timedelta(days=1)
    # Handle month wrap-around
    if tomorrow.month != date.today().month:
        billing_day = 1
    else:
        billing_day = tomorrow.day

    not_due_customer_create = schemas.CustomerCreate(
        name="Not Due Customer",
        login="notdue",
        partner_id=test_customer.partner_id,
        location_id=test_customer.location_id,
        billing_config=schemas.CustomerBillingBase(
            enabled=True,
            billing_date=billing_day,
        )
    )
    not_due_customer = crud.create_customer(db_session, not_due_customer_create)
    
    # Run the billing engine function
    generate_invoices_for_due_customers(db_session)
    
    # Check invoices for the due customer
    due_customer_invoices = db_session.query(Invoice).filter(Invoice.customer_id == test_customer.id).all()
    assert len(due_customer_invoices) == 1
    invoice = due_customer_invoices[0]
    assert invoice.total == test_service.tariff.price
    assert len(invoice.items) == 1
    assert invoice.items[0].description == f"{test_service.description} (Tariff: {test_service.tariff.title})"
    
    # Check invoices for the not-due customer
    not_due_customer_invoices = db_session.query(Invoice).filter(Invoice.customer_id == not_due_customer.id).all()
    assert len(not_due_customer_invoices) == 0

def test_suspend_services_for_overdue_customers(db_session, overdue_customer, test_tariff):
    """
    Test that services are suspended for customers with overdue invoices.
    """
    # The overdue_customer fixture creates a customer with an old, unpaid invoice.
    # Let's give them an active service.
    active_service_create = schemas.InternetServiceCreate(
        customer_id=overdue_customer.id,
        tariff_id=test_tariff.id,
        status='active',
        description="Active Service to be suspended",
        login="overdue_active_service"
    )
    active_service = crud.create_internet_service(db_session, active_service_create)
    
    # Run the suspension function
    suspend_services_for_overdue_customers(db_session)
    
    # Refresh objects from the database
    db_session.refresh(overdue_customer)
    db_session.refresh(active_service)
    
    # Assertions
    assert overdue_customer.status == 'blocked'
    assert active_service.status == 'blocked'

def test_reactivate_paid_customers_services(db_session, paid_up_customer_with_blocked_service):
    """
    Test that services are reactivated for customers who have paid their dues.
    """
    customer = paid_up_customer_with_blocked_service
    service = db_session.query(InternetService).filter(InternetService.customer_id == customer.id).first()
    
    assert customer.status == 'blocked' # Initial status
    assert service.status == 'blocked' # Initial status
    
    # Run the reactivation function
    reactivate_paid_customers_services(db_session)
    
    # Refresh objects
    db_session.refresh(customer)
    db_session.refresh(service)
    
    # Assertions
    # Note: This function should reactivate both the customer and their services.
    assert customer.status == 'active' 
    assert service.status == 'active'

# Tests for API endpoints

def test_create_manual_invoice_api(test_client, super_admin_auth_headers, test_customer):
    """
    Test manual invoice creation via the API using an authenticated client.
    """
    invoice_data = {
        "customer_id": test_customer.id,
        "items": [
            {"description": "Manual Service 1", "quantity": 1, "price": 150.50}
        ]
    }
    
    response = test_client.post("/api/v1/billing/invoices/", json=invoice_data, headers=super_admin_auth_headers)
    
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["customer_id"] == test_customer.id
    assert Decimal(data["total"]) == Decimal("150.50")
    assert Decimal(data["due"]) == Decimal("150.50")
    assert len(data["items"]) == 1
    assert data["items"][0]["description"] == "Manual Service 1"

def test_create_payment_and_reactivate_api(test_client, super_admin_auth_headers, db_session, overdue_customer, blocked_service):
    """
    Test that making a payment for an overdue invoice reactivates the customer's services.
    """
    # First, we need to make sure the customer is actually blocked.
    # The suspend job would have done this. Let's simulate it for the test.
    overdue_customer.status = 'blocked'
    db_session.commit()
    db_session.refresh(overdue_customer)
    assert overdue_customer.status == 'blocked'

    overdue_invoice = db_session.query(Invoice).filter(Invoice.customer_id == overdue_customer.id).first()
    assert overdue_invoice is not None
    assert overdue_invoice.status == 'not_paid'
    
    service_to_check = db_session.query(InternetService).filter(InternetService.id == blocked_service.id).first()
    assert service_to_check.status == 'blocked'

    payment_data = {
        "customer_id": overdue_customer.id,
        "invoice_id": overdue_invoice.id,
        "payment_type_id": 1, # From conftest setup
        "receipt_number": "PAY-TEST-001",
        "amount": str(overdue_invoice.due)
    }
    
    response = test_client.post("/api/v1/billing/payments/", json=payment_data, headers=super_admin_auth_headers)
    
    assert response.status_code == 201, response.text
    
    # Re-fetch the objects from the database to get their updated state
    refreshed_invoice = db_session.query(Invoice).filter(Invoice.id == overdue_invoice.id).one()
    refreshed_service = db_session.query(InternetService).filter(InternetService.id == blocked_service.id).one()
    refreshed_customer = db_session.query(Customer).filter(Customer.id == overdue_customer.id).one()
    
    assert refreshed_invoice.status == 'paid'
    assert refreshed_service.status == 'active'
    assert refreshed_customer.status == 'active'
