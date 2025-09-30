from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import crud, schemas, security, audit
from ..deps import get_db

router = APIRouter()

@router.post("/", response_model=schemas.ProformaInvoiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.manage_invoices"))])
async def create_proforma_invoice(
    invoice: schemas.ProformaInvoiceCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Create a new proforma invoice.
    Requires 'billing.manage_invoices' permission.
    """
    if not crud.get_customer(db, invoice.customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
    new_invoice = crud.create_proforma_invoice(db=db, invoice=invoice)
    after_dict = schemas.ProformaInvoiceResponse.model_validate(new_invoice).model_dump()
    await logger.log("create", "proforma_invoice", new_invoice.id, after_values=after_dict, risk_level='medium')
    return new_invoice

@router.get("/", response_model=schemas.PaginatedResponse[schemas.ProformaInvoiceResponse], dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_proforma_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of proforma invoices with pagination.
    Requires 'billing.view_invoices' permission.
    """
    invoices = crud.get_proforma_invoices(db, skip=skip, limit=limit, customer_id=customer_id)
    total = crud.get_proforma_invoices_count(db, customer_id=customer_id)
    return {"items": invoices, "total": total}

@router.get("/{invoice_id}", response_model=schemas.ProformaInvoiceResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_proforma_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single proforma invoice by ID.
    Requires 'billing.view_invoices' permission.
    """
    db_invoice = crud.get_proforma_invoice(db, invoice_id=invoice_id)
    if db_invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proforma Invoice not found")
    return db_invoice

@router.put("/{invoice_id}", response_model=schemas.ProformaInvoiceResponse, dependencies=[Depends(security.require_permission("billing.manage_invoices"))])
async def update_proforma_invoice(
    invoice_id: int, 
    invoice_update: schemas.ProformaInvoiceCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Update an existing proforma invoice.
    Requires 'billing.manage_invoices' permission.
    """
    db_invoice_before = crud.get_proforma_invoice(db, invoice_id=invoice_id)
    if db_invoice_before is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proforma Invoice not found")
    before_dict = schemas.ProformaInvoiceResponse.model_validate(db_invoice_before).model_dump()
    db.expire(db_invoice_before)

    updated_invoice = crud.update_proforma_invoice(db=db, invoice_id=invoice_id, invoice_update=invoice_update)
    if not updated_invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proforma Invoice not found after update.")
    after_dict = schemas.ProformaInvoiceResponse.model_validate(updated_invoice).model_dump()

    await logger.log("update", "proforma_invoice", invoice_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_invoice

@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("billing.manage_invoices"))])
async def delete_proforma_invoice(
    invoice_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Delete a proforma invoice.
    Requires 'billing.manage_invoices' permission.
    """
    db_invoice_before = crud.get_proforma_invoice(db, invoice_id=invoice_id)
    if db_invoice_before is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proforma Invoice not found")
    before_dict = schemas.ProformaInvoiceResponse.model_validate(db_invoice_before).model_dump()

    deleted = crud.delete_proforma_invoice(db, invoice_id=invoice_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proforma Invoice not found")
    await logger.log("delete", "proforma_invoice", invoice_id, before_values=before_dict, risk_level='high')
    return None