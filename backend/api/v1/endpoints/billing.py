from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from datetime import date, timedelta
from decimal import Decimal

from ..deps import get_db
import crud, schemas, security

router = APIRouter(prefix="/billing", tags=["billing"])

# --- Invoices ---
@router.post("/invoices/", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.create_invoices"))])
def create_manual_invoice(invoice_data: schemas.ManualInvoiceCreate, db: Session = Depends(get_db)):
    """
    Manually creates an invoice from the UI or a direct API call.
    This endpoint handles the business logic for calculating totals and generating invoice numbers.
    """
    # --- Business Logic for Manual Invoice Creation ---
    # 1. Calculate total
    total_amount = sum(item.price * item.quantity for item in invoice_data.items)

    # 2. Generate invoice number
    today = date.today()
    invoice_count_for_month = db.query(crud.models.Invoice).filter(crud.models.Invoice.date_created >= today.replace(day=1)).count()
    invoice_number = f"INV-{today.strftime('%Y-%m')}-{invoice_count_for_month + 1:04d}"

    # 3. Determine due date (using a default of 14 days)
    due_date = today + timedelta(days=14)

    # 4. Construct the full InvoiceCreate schema to pass to the CRUD layer
    full_invoice_schema = schemas.InvoiceCreate(
        **invoice_data.model_dump(),
        number=invoice_number,
        total=total_amount,
        due=total_amount,
        date_till=due_date
    )
    return crud.create_invoice(db=db, invoice=full_invoice_schema)

@router.get("/invoices/", response_model=schemas.PaginatedInvoiceResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_invoices(skip: int = 0, limit: int = 100, customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    invoices = crud.get_invoices(db, skip=skip, limit=limit, customer_id=customer_id)
    total = crud.get_invoices_count(db, customer_id=customer_id)
    return {"items": invoices, "total": total}

@router.get("/invoices/{invoice_id}", response_model=schemas.InvoiceResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = crud.get_invoice(db, invoice_id=invoice_id)
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

# --- Payments ---
@router.post("/payments/", response_model=schemas.PaymentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.process_payments"))])
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    # Basic validation
    if not crud.get_customer(db, payment.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    if payment.invoice_id and not crud.get_invoice(db, payment.invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return crud.create_payment(db=db, payment=payment)

@router.get("/payments/", response_model=schemas.PaginatedPaymentResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    payments = crud.get_payments(db, skip=skip, limit=limit)
    total = crud.get_payments_count(db)
    return {"items": payments, "total": total}

@router.get("/payment-methods/", response_model=List[schemas.PaymentMethodResponse], dependencies=[Depends(security.require_permission("billing.process_payments"))])
def read_payment_methods(db: Session = Depends(get_db)):
    return crud.get_payment_methods(db)

@router.get("/taxes/", response_model=List[schemas.TaxResponse], dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_taxes(db: Session = Depends(get_db)):
    return crud.get_taxes(db)