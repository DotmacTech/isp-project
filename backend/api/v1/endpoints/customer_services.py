from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .... import crud, schemas
from ..deps import get_db
from ....security import get_current_customer

router = APIRouter()

@router.post("/subscribe/internet", response_model=schemas.InternetServiceResponse, status_code=status.HTTP_201_CREATED)
def subscribe_to_internet_service(
    service: schemas.InternetServiceCreate,
    db: Session = Depends(get_db),
    current_customer: schemas.CustomerResponse = Depends(get_current_customer)
):
    """
    Subscribe to an internet service tariff.
    """
    # Verify that the customer is authorized to subscribe to this service
    # Customers can only subscribe to services for themselves
    if service.customer_id != current_customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot subscribe to services for other customers")
    
    # Basic validation
    if not crud.get_internet_tariff(db, service.tariff_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internet Tariff not found")
    
    return crud.create_internet_service(db=db, service=service)

@router.post("/subscribe/voice", response_model=schemas.VoiceServiceResponse, status_code=status.HTTP_201_CREATED)
def subscribe_to_voice_service(
    service: schemas.VoiceServiceCreate,
    db: Session = Depends(get_db),
    current_customer: schemas.CustomerResponse = Depends(get_current_customer)
):
    """
    Subscribe to a voice service tariff.
    """
    # Verify that the customer is authorized to subscribe to this service
    # Customers can only subscribe to services for themselves
    if service.customer_id != current_customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot subscribe to services for other customers")
    
    # Basic validation
    if not crud.get_voice_tariff(db, service.tariff_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice Tariff not found")
    
    return crud.create_voice_service(db=db, service=service)

@router.post("/subscribe/recurring", response_model=schemas.RecurringServiceResponse, status_code=status.HTTP_201_CREATED)
def subscribe_to_recurring_service(
    service: schemas.RecurringServiceCreate,
    db: Session = Depends(get_db),
    current_customer: schemas.CustomerResponse = Depends(get_current_customer)
):
    """
    Subscribe to a recurring service tariff.
    """
    # Verify that the customer is authorized to subscribe to this service
    # Customers can only subscribe to services for themselves
    if service.customer_id != current_customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot subscribe to services for other customers")
    
    # Basic validation
    if not crud.get_recurring_tariff(db, service.tariff_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring Tariff not found")
    
    return crud.create_recurring_service(db=db, service=service)

@router.post("/subscribe/bundle", response_model=schemas.BundleServiceResponse, status_code=status.HTTP_201_CREATED)
def subscribe_to_bundle_service(
    service: schemas.BundleServiceCreate,
    db: Session = Depends(get_db),
    current_customer: schemas.CustomerResponse = Depends(get_current_customer)
):
    """
    Subscribe to a bundle service tariff.
    """
    # Verify that the customer is authorized to subscribe to this service
    # Customers can only subscribe to services for themselves
    if service.customer_id != current_customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot subscribe to services for other customers")
    
    # Basic validation
    if not crud.get_bundle_tariff(db, service.bundle_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle Tariff not found")
    
    return crud.create_bundle_service(db=db, service=service)