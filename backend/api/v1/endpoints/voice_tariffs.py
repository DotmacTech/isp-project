from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from .... import crud, schemas, security, audit
from ..deps import get_db

router = APIRouter()

@router.post("/", response_model=schemas.VoiceTariffResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def create_voice_tariff(
    tariff: schemas.VoiceTariffCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Create a new voice tariff.
    Requires 'billing.manage_tariffs' permission.
    """
    new_tariff = crud.create_voice_tariff(db=db, tariff=tariff)
    after_dict = schemas.VoiceTariffResponse.model_validate(new_tariff).model_dump()
    await logger.log("create", "voice_tariff", new_tariff.id, after_values=after_dict, risk_level='medium')
    return new_tariff

@router.get("/", response_model=schemas.PaginatedVoiceTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_voice_tariffs(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of voice tariffs with pagination.
    Requires 'billing.manage_tariffs' permission.
    """
    tariffs = crud.get_voice_tariffs(db, skip=skip, limit=limit)
    total = crud.get_voice_tariffs_count(db)
    return {"items": tariffs, "total": total}

@router.get("/{tariff_id}", response_model=schemas.VoiceTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_voice_tariff(tariff_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single voice tariff by ID.
    Requires 'billing.manage_tariffs' permission.
    """
    db_tariff = crud.get_voice_tariff(db, tariff_id=tariff_id)
    if db_tariff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice Tariff not found")
    return db_tariff

@router.put("/{tariff_id}", response_model=schemas.VoiceTariffResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def update_voice_tariff(
    tariff_id: int, 
    tariff_update: schemas.VoiceTariffUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Update an existing voice tariff.
    Requires 'billing.manage_tariffs' permission.
    """
    db_tariff_before = crud.get_voice_tariff(db, tariff_id=tariff_id)
    if db_tariff_before is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice Tariff not found")
    before_dict = schemas.VoiceTariffResponse.model_validate(db_tariff_before).model_dump()
    db.expire(db_tariff_before)

    updated_tariff = crud.update_voice_tariff(db=db, tariff_id=tariff_id, tariff_update=tariff_update)
    if not updated_tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice Tariff not found after update.")
    after_dict = schemas.VoiceTariffResponse.model_validate(updated_tariff).model_dump()

    await logger.log("update", "voice_tariff", tariff_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_tariff

@router.delete("/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def delete_voice_tariff(
    tariff_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Delete a voice tariff.
    Requires 'billing.manage_tariffs' permission.
    """
    db_tariff_before = crud.get_voice_tariff(db, tariff_id=tariff_id)
    if db_tariff_before is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice Tariff not found")
    before_dict = schemas.VoiceTariffResponse.model_validate(db_tariff_before).model_dump()

    deleted = crud.delete_voice_tariff(db, tariff_id=tariff_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice Tariff not found")
    await logger.log("delete", "voice_tariff", tariff_id, before_values=before_dict, risk_level='high')
    return None