from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import crud, schemas, security
from ..deps import get_db

router = APIRouter(prefix="/tariffs", tags=["Tariffs"])

# --- Internet Tariffs ---

@router.get("/internet", response_model=schemas.PaginatedInternetTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_internet_tariffs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tariffs = crud.get_internet_tariffs(db, skip=skip, limit=limit)
    total = crud.get_internet_tariffs_count(db)
    return {"total": total, "items": tariffs}

@router.post("/internet", response_model=schemas.InternetTariffResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def create_internet_tariff(tariff: schemas.InternetTariffCreate, db: Session = Depends(get_db)):
    return crud.create_internet_tariff(db=db, tariff=tariff)

@router.get("/internet/{tariff_id}", response_model=schemas.InternetTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_internet_tariff(tariff_id: int, db: Session = Depends(get_db)):
    db_tariff = crud.get_internet_tariff(db, tariff_id=tariff_id)
    if db_tariff is None:
        raise HTTPException(status_code=404, detail="Internet Tariff not found")
    return db_tariff

@router.put("/internet/{tariff_id}", response_model=schemas.InternetTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def update_internet_tariff(tariff_id: int, tariff: schemas.InternetTariffUpdate, db: Session = Depends(get_db)):
    updated_tariff = crud.update_internet_tariff(db, tariff_id=tariff_id, tariff_update=tariff)
    if updated_tariff is None:
        raise HTTPException(status_code=404, detail="Internet Tariff not found")
    return updated_tariff

@router.delete("/internet/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def delete_internet_tariff(tariff_id: int, db: Session = Depends(get_db)):
    deleted_tariff = crud.delete_internet_tariff(db, tariff_id=tariff_id)
    if deleted_tariff is None:
        raise HTTPException(status_code=404, detail="Internet Tariff not found")
    return

# Note: Endpoints for Voice, Recurring, One-Time, and Bundle tariffs would follow a similar pattern.
# For brevity, only Internet Tariffs are fully implemented here.

@router.get("/voice", response_model=schemas.PaginatedVoiceTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_voice_tariffs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tariffs = crud.get_voice_tariffs(db, skip=skip, limit=limit)
    total = crud.get_voice_tariffs_count(db)
    return {"total": total, "items": tariffs}

@router.get("/recurring", response_model=schemas.PaginatedRecurringTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_recurring_tariffs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tariffs = crud.get_recurring_tariffs(db, skip=skip, limit=limit)
    total = crud.get_recurring_tariffs_count(db)
    return {"total": total, "items": tariffs}

@router.get("/one-time", response_model=schemas.PaginatedOneTimeTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_one_time_tariffs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tariffs = crud.get_one_time_tariffs(db, skip=skip, limit=limit)
    total = crud.get_one_time_tariffs_count(db)
    return {"total": total, "items": tariffs}