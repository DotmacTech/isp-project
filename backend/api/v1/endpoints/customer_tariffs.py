from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from .... import crud, schemas
from ..deps import get_db

router = APIRouter()

@router.get("/internet", response_model=schemas.PaginatedInternetTariffResponse)
def get_internet_tariffs_for_customer(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of internet tariffs available for customers.
    """
    tariffs = crud.get_internet_tariffs_for_customer_portal(db, skip=skip, limit=limit)
    total = len(tariffs)  # In a real implementation, you would calculate the total count
    return {"items": tariffs, "total": total}

@router.get("/voice", response_model=schemas.PaginatedVoiceTariffResponse)
def get_voice_tariffs_for_customer(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of voice tariffs available for customers.
    """
    tariffs = crud.get_voice_tariffs_for_customer_portal(db, skip=skip, limit=limit)
    total = len(tariffs)  # In a real implementation, you would calculate the total count
    return {"items": tariffs, "total": total}

@router.get("/recurring", response_model=schemas.PaginatedRecurringTariffResponse)
def get_recurring_tariffs_for_customer(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of recurring tariffs available for customers.
    """
    tariffs = crud.get_recurring_tariffs_for_customer_portal(db, skip=skip, limit=limit)
    total = len(tariffs)  # In a real implementation, you would calculate the total count
    return {"items": tariffs, "total": total}

@router.get("/bundle", response_model=schemas.PaginatedBundleTariffResponse)
def get_bundle_tariffs_for_customer(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of bundle tariffs available for customers.
    """
    tariffs = crud.get_bundle_tariffs_for_customer_portal(db, skip=skip, limit=limit)
    total = len(tariffs)  # In a real implementation, you would calculate the total count
    return {"items": tariffs, "total": total}

@router.get("/onetime", response_model=schemas.PaginatedOneTimeTariffResponse)
def get_one_time_tariffs_for_customer(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of one-time tariffs available for customers.
    """
    tariffs = crud.get_one_time_tariffs_for_customer_portal(db, skip=skip, limit=limit)
    total = len(tariffs)  # In a real implementation, you would calculate the total count
    return {"items": tariffs, "total": total}