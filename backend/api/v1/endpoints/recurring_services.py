from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import crud, schemas, security
from ..deps import get_db

router = APIRouter()

@router.post("/", response_model=schemas.RecurringServiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def create_recurring_service(service: schemas.RecurringServiceCreate, db: Session = Depends(get_db)):
    """
    Create a new recurring service.
    Requires 'crm.edit_accounts' permission.
    """
    if not crud.get_customer(db, service.customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if not crud.get_recurring_tariff(db, service.tariff_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring Tariff not found")
    return crud.create_recurring_service(db=db, service=service)

@router.get("/", response_model=schemas.PaginatedRecurringServiceResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_recurring_services(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of recurring services with pagination and filtering.
    Requires 'crm.view_accounts' permission.
    """
    services = crud.get_recurring_services(db, skip=skip, limit=limit, customer_id=customer_id)
    total = crud.get_recurring_services_count(db, customer_id=customer_id)
    return {"items": services, "total": total}

@router.get("/{service_id}", response_model=schemas.RecurringServiceResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_recurring_service(service_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single recurring service by ID.
    Requires 'crm.view_accounts' permission.
    """
    db_service = crud.get_recurring_service(db, service_id=service_id)
    if db_service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring Service not found")
    return db_service

@router.put("/{service_id}", response_model=schemas.RecurringServiceResponse, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def update_recurring_service(service_id: int, service_update: schemas.RecurringServiceUpdate, db: Session = Depends(get_db)):
    """
    Update an existing recurring service.
    Requires 'crm.edit_accounts' permission.
    """
    return crud.update_recurring_service(db=db, service_id=service_id, service_update=service_update)

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def delete_recurring_service(service_id: int, db: Session = Depends(get_db)):
    """
    Delete a recurring service.
    Requires 'crm.edit_accounts' permission.
    """
    deleted = crud.delete_recurring_service(db, service_id=service_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring Service not found")
    return