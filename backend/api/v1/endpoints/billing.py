from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db
import crud, schemas, security

router = APIRouter(prefix="/billing", tags=["billing"])

# --- Invoices ---
@router.post("/invoices/", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.create_invoices"))])
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    return crud.create_invoice(db=db, invoice=invoice)

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