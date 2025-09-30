from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from decimal import Decimal

from .... import crud, schemas, security
from ..deps import get_db

router = APIRouter()

@router.get("/stats/", dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def get_invoice_statistics(
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get invoice statistics including counts and amounts by status"""
    return crud.get_invoice_statistics(db, customer_id=customer_id)

@router.get("", response_model=schemas.PaginatedInvoiceResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_invoices(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    invoices = crud.get_invoices(db, skip=skip, limit=limit, customer_id=customer_id)
    total = crud.get_invoices_count(db, customer_id=customer_id)
    return {"total": total, "items": invoices}

@router.post("", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.create_invoices"))])
def create_manual_invoice(invoice_data: schemas.ManualInvoiceCreate, db: Session = Depends(get_db)):
    total_amount = sum(item.price * item.quantity for item in invoice_data.items)
    invoice_count = crud.get_invoices_count(db)
    invoice_number = f"MANUAL-{date.today().strftime('%Y')}-{invoice_count + 1:05d}"

    full_invoice_data = schemas.InvoiceCreate(
        **invoice_data.model_dump(),
        number=invoice_number,
        total=total_amount,
        due=total_amount,
        date_till=date.today() + timedelta(days=14)
    )
    return crud.create_invoice(db, invoice=full_invoice_data)

@router.get("/{invoice_id}/", response_model=schemas.InvoiceResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = crud.get_invoice(db, invoice_id=invoice_id)
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

@router.put("/{invoice_id}/", response_model=schemas.InvoiceResponse, dependencies=[Depends(security.require_permission("billing.edit_invoices"))])
def update_invoice(invoice_id: int, invoice: schemas.InvoiceUpdate, db: Session = Depends(get_db)):
    updated_invoice = crud.update_invoice(db, invoice_id=invoice_id, invoice_update=invoice)
    if updated_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return updated_invoice