from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db 
from .... import crud, schemas, security, audit

router = APIRouter()

@router.post("/", response_model=schemas.LocationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.create_accounts"))])
async def create_location(location: schemas.LocationCreate, db: Session = Depends(get_db), logger: audit.AuditLogger = Depends(audit.get_audit_logger)):
    new_location = crud.create_location(db=db, location=location)
    after_dict = schemas.LocationResponse.model_validate(new_location).model_dump()
    await logger.log("create", "locations", new_location.id, after_values=after_dict, risk_level='low')
    return new_location

@router.get("/", response_model=List[schemas.LocationResponse], dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_locations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    locations = crud.get_locations(db, skip=skip, limit=limit)
    return locations

@router.get("/{location_id}", response_model=schemas.LocationResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_location(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.get_location(db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

@router.put("/{location_id}", response_model=schemas.LocationResponse, dependencies=[Depends(security.require_permission("crm.edit_accounts"))])
async def update_location(
    location_id: int, 
    location: schemas.LocationUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_location_before = crud.get_location(db, location_id)
    if not db_location_before:
        raise HTTPException(status_code=404, detail="Location not found")
    before_dict = schemas.LocationResponse.model_validate(db_location_before).model_dump()
    db.expire(db_location_before)

    updated_location = crud.update_location(db=db, location_id=location_id, location_update=location)
    if not updated_location:
        raise HTTPException(status_code=404, detail="Location not found after update.")
    after_dict = schemas.LocationResponse.model_validate(updated_location).model_dump()

    await logger.log("update", "locations", location_id, before_values=before_dict, after_values=after_dict, risk_level='low')
    return updated_location

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("crm.delete_accounts"))])
async def delete_location(
    location_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_location_before = crud.get_location(db, location_id)
    if not db_location_before:
        raise HTTPException(status_code=404, detail="Location not found")
    before_dict = schemas.LocationResponse.model_validate(db_location_before).model_dump()

    deleted_location = crud.delete_location(db, location_id=location_id)
    if deleted_location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    await logger.log("delete", "locations", location_id, before_values=before_dict, risk_level='medium')
    return None
