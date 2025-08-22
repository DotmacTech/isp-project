from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..deps import get_db
import crud, schemas, security, audit

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("/", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.create_accounts"))])
async def create_customer(
    customer: schemas.CustomerCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    new_customer = crud.create_customer(db=db, customer=customer)
    after_dict = schemas.CustomerResponse.model_validate(new_customer).model_dump()
    await logger.log("create", "customers", new_customer.id, after_values=after_dict, risk_level='low')
    return new_customer

@router.get("/", response_model=schemas.PaginatedCustomerResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_customers(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    customers = crud.get_customers(db, skip=skip, limit=limit, search=search, status=status)
    total = crud.get_customers_count(db, search=search, status=status)
    return {"items": customers, "total": total}

@router.get("/{customer_id}", response_model=schemas.CustomerResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = crud.get_customer(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.put("/{customer_id}", response_model=schemas.CustomerResponse, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
async def update_customer(
    customer_id: int, 
    customer: schemas.CustomerUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_customer_before = crud.get_customer(db, customer_id)
    if not db_customer_before:
        raise HTTPException(status_code=404, detail="Customer not found")
    before_dict = schemas.CustomerResponse.model_validate(db_customer_before).model_dump()
    db.expire(db_customer_before)

    updated_customer = crud.update_customer(db=db, customer_id=customer_id, customer_update=customer)
    if not updated_customer:
        raise HTTPException(status_code=404, detail="Customer not found after update.")
    after_dict = schemas.CustomerResponse.model_validate(updated_customer).model_dump()

    await logger.log("update", "customers", customer_id, before_values=before_dict, after_values=after_dict, risk_level='low')
    return updated_customer

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("crm.delete_accounts"))])
async def delete_customer(
    customer_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_customer_before = crud.get_customer(db, customer_id)
    if not db_customer_before:
        raise HTTPException(status_code=404, detail="Customer not found")
    before_dict = schemas.CustomerResponse.model_validate(db_customer_before).model_dump()

    deleted_customer = crud.delete_customer(db, customer_id=customer_id)
    if deleted_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    await logger.log("delete", "customers", customer_id, before_values=before_dict, risk_level='high')
    return None
