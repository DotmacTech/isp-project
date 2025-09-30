from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from .... import crud, schemas, security
from ..deps import get_db

router = APIRouter()

@router.get("/stats", dependencies=[Depends(security.require_permission("billing.process_payments"))])
def get_payment_statistics(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get payment statistics including counts and amounts by status"""
    return crud.get_payment_statistics(db)

@router.get("/", response_model=schemas.PaginatedPaymentResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_payments(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    payments = crud.get_payments(db, skip=skip, limit=limit)
    total = crud.get_payments_count(db)
    return {"total": total, "items": payments}

@router.post("/", response_model=schemas.PaymentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.process_payments"))])
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    # Add validation for customer, invoice, and payment method existence
    if not crud.get_customer(db, payment.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    if payment.invoice_id and not crud.get_invoice(db, payment.invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    if not crud.get_payment_method(db, payment.payment_type_id):
        raise HTTPException(status_code=404, detail="Payment Method not found")
    return crud.create_payment(db=db, payment=payment)

@router.get("/{payment_id}", response_model=schemas.PaymentResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_payment(payment_id: int, db: Session = Depends(get_db)):
    db_payment = crud.get_payment(db, payment_id=payment_id)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return db_payment

@router.put("/{payment_id}", response_model=schemas.PaymentResponse, dependencies=[Depends(security.require_permission("billing.process_payments"))])
def update_payment(payment_id: int, payment: schemas.PaymentUpdate, db: Session = Depends(get_db)):
    updated_payment = crud.update_payment(db, payment_id=payment_id, payment_update=payment)
    if updated_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return updated_payment