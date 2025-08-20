from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db
import crud, schemas, security

router = APIRouter(prefix="/tariffs", tags=["tariffs"])

# --- Internet Tariffs ---
@router.post("/internet/", response_model=schemas.InternetTariffResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def create_internet_tariff(tariff: schemas.InternetTariffCreate, db: Session = Depends(get_db)):
    return crud.create_internet_tariff(db=db, tariff=tariff)

@router.get("/internet/", response_model=schemas.PaginatedInternetTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_internet_tariffs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tariffs = crud.get_internet_tariffs(db, skip=skip, limit=limit)
    total = crud.get_internet_tariffs_count(db)
    return {"items": tariffs, "total": total}

@router.get("/internet/{tariff_id}", response_model=schemas.InternetTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_internet_tariff(tariff_id: int, db: Session = Depends(get_db)):
    db_tariff = crud.get_internet_tariff(db, tariff_id=tariff_id)
    if db_tariff is None:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return db_tariff

@router.put("/internet/{tariff_id}", response_model=schemas.InternetTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def update_internet_tariff(tariff_id: int, tariff_update: schemas.InternetTariffUpdate, db: Session = Depends(get_db)):
    return crud.update_internet_tariff(db=db, tariff_id=tariff_id, tariff_update=tariff_update)

@router.delete("/internet/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def delete_internet_tariff(tariff_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_internet_tariff(db, tariff_id=tariff_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return