from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .... import crud
from .... import models
from .... import schemas
from .... import security
from ..deps import get_db

router = APIRouter(
    dependencies=[Depends(security.require_permission("network.manage_devices"))]
)

# --- Device Producers ---
@router.get("/producers/", response_model=List[schemas.NetworkLookupResponse])
def read_producers(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return crud.get_network_lookups(db, models.MonitoringProducer, skip, limit)

@router.post("/producers/", response_model=schemas.NetworkLookupResponse, status_code=201)
def create_producer(item: schemas.NetworkLookupCreate, db: Session = Depends(get_db)):
    return crud.create_network_lookup(db, models.MonitoringProducer, item)

@router.delete("/producers/{item_id}", response_model=schemas.NetworkLookupResponse)
def delete_producer(item_id: int, db: Session = Depends(get_db)):
    deleted_item = crud.delete_network_lookup(db, models.MonitoringProducer, item_id)
    if not deleted_item:
        raise HTTPException(status_code=404, detail="Producer not found")
    return deleted_item

# --- Device Types ---
@router.get("/types/", response_model=List[schemas.NetworkLookupResponse])
def read_types(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return crud.get_network_lookups(db, models.MonitoringDeviceType, skip, limit)

@router.post("/types/", response_model=schemas.NetworkLookupResponse, status_code=201)
def create_type(item: schemas.NetworkLookupCreate, db: Session = Depends(get_db)):
    return crud.create_network_lookup(db, models.MonitoringDeviceType, item)

@router.delete("/types/{item_id}", response_model=schemas.NetworkLookupResponse)
def delete_type(item_id: int, db: Session = Depends(get_db)):
    deleted_item = crud.delete_network_lookup(db, models.MonitoringDeviceType, item_id)
    if not deleted_item:
        raise HTTPException(status_code=404, detail="Device type not found")
    return deleted_item

# --- Monitoring Groups ---
@router.get("/groups/", response_model=List[schemas.NetworkLookupResponse])
def read_groups(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return crud.get_network_lookups(db, models.MonitoringGroup, skip, limit)

@router.post("/groups/", response_model=schemas.NetworkLookupResponse, status_code=201)
def create_group(item: schemas.NetworkLookupCreate, db: Session = Depends(get_db)):
    return crud.create_network_lookup(db, models.MonitoringGroup, item)

@router.delete("/groups/{item_id}", response_model=schemas.NetworkLookupResponse)
def delete_group(item_id: int, db: Session = Depends(get_db)):
    deleted_item = crud.delete_network_lookup(db, models.MonitoringGroup, item_id)
    if not deleted_item:
        raise HTTPException(status_code=404, detail="Monitoring group not found")
    return deleted_item