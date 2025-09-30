from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .... import crud
from .... import security
from .... import audit
from .... import schemas
from ..deps import get_db

router = APIRouter(prefix="/services", tags=["Services"])

@router.get("/internet", response_model=schemas.PaginatedInternetServiceResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_internet_services(
    skip: int = 0, limit: int = 100,
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    services = crud.get_internet_services(db, skip=skip, limit=limit, customer_id=customer_id, status=status)
    total = crud.get_internet_services_count(db, customer_id=customer_id)
    return {"total": total, "items": services}

@router.post("/internet", response_model=schemas.InternetServiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def create_internet_service(service: schemas.InternetServiceCreate, db: Session = Depends(get_db)):
    # Add validation for customer and tariff existence
    if not crud.get_customer(db, service.customer_id):
        raise HTTPException(status_code=404, detail=f"Customer with id {service.customer_id} not found")
    if not crud.get_internet_tariff(db, service.tariff_id):
        raise HTTPException(status_code=404, detail=f"Internet Tariff with id {service.tariff_id} not found")
    return crud.create_internet_service(db=db, service=service)

@router.get("/internet/{service_id}", response_model=schemas.InternetServiceResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_internet_service(service_id: int, db: Session = Depends(get_db)):
    db_service = crud.get_internet_service(db, service_id=service_id)
    if db_service is None:
        raise HTTPException(status_code=404, detail="Internet Service not found")
    return db_service

@router.put("/internet/{service_id}", response_model=schemas.InternetServiceResponse, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def update_internet_service(service_id: int, service: schemas.InternetServiceUpdate, db: Session = Depends(get_db)):
    updated_service = crud.update_internet_service(db, service_id=service_id, service_update=service)
    if updated_service is None:
        raise HTTPException(status_code=404, detail="Internet Service not found")
    return updated_service

@router.delete("/internet/{service_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def delete_internet_service(service_id: int, db: Session = Depends(get_db)):
    deleted_service = crud.delete_internet_service(db, service_id=service_id)
    if deleted_service is None:
        raise HTTPException(status_code=404, detail="Internet Service not found")
    return