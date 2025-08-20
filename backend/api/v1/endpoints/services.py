from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db
import crud, schemas, security

router = APIRouter(prefix="/services", tags=["services"])

# --- Internet Services ---
@router.post("/internet/", response_model=schemas.InternetServiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def create_internet_service(service: schemas.InternetServiceCreate, db: Session = Depends(get_db)):
    # Basic validation
    if not crud.get_customer(db, service.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    if not crud.get_internet_tariff(db, service.tariff_id):
        raise HTTPException(status_code=404, detail="Tariff not found")
    return crud.create_internet_service(db=db, service=service)

@router.get("/internet/", response_model=schemas.PaginatedInternetServiceResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_internet_services(skip: int = 0, limit: int = 100, customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    services = crud.get_internet_services(db, skip=skip, limit=limit, customer_id=customer_id)
    total = crud.get_internet_services_count(db, customer_id=customer_id)
    return {"items": services, "total": total}

@router.get("/internet/{service_id}", response_model=schemas.InternetServiceResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_internet_service(service_id: int, db: Session = Depends(get_db)):
    db_service = crud.get_internet_service(db, service_id=service_id)
    if db_service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return db_service

@router.put("/internet/{service_id}", response_model=schemas.InternetServiceResponse, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def update_internet_service(service_id: int, service_update: schemas.InternetServiceUpdate, db: Session = Depends(get_db)):
    return crud.update_internet_service(db=db, service_id=service_id, service_update=service_update)

@router.delete("/internet/{service_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
def delete_internet_service(service_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_internet_service(db, service_id=service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")
    return