from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db
from ....import crud, schemas, security, audit

router = APIRouter()

@router.get("/", response_model=List[schemas.TaxResponse], dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_taxes(db: Session = Depends(get_db), show_all: bool = False):
    return crud.get_taxes(db, show_all=show_all)

@router.post("/", response_model=schemas.TaxResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def create_tax(
    tax: schemas.TaxCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    new_tax = crud.create_tax(db, tax)
    after_dict = schemas.TaxResponse.model_validate(new_tax).model_dump()
    await logger.log("create", "tax", new_tax.id, after_values=after_dict, risk_level='medium')
    return new_tax

@router.put("/{tax_id}", response_model=schemas.TaxResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def update_tax(
    tax_id: int, 
    tax_update: schemas.TaxUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_tax_before = crud.get_tax(db, tax_id)
    if not db_tax_before:
        raise HTTPException(status_code=404, detail="Tax not found")
    before_dict = schemas.TaxResponse.model_validate(db_tax_before).model_dump()
    db.expire(db_tax_before)

    updated_tax = crud.update_tax(db, tax_id, tax_update)
    if not updated_tax:
        raise HTTPException(status_code=404, detail="Tax not found after update.")
    after_dict = schemas.TaxResponse.model_validate(updated_tax).model_dump()

    await logger.log("update", "tax", tax_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_tax

@router.delete("/{tax_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def delete_tax(
    tax_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_tax_before = crud.get_tax(db, tax_id)
    if not db_tax_before:
        raise HTTPException(status_code=404, detail="Tax not found")
    before_dict = schemas.TaxResponse.model_validate(db_tax_before).model_dump()

    db_tax = crud.delete_tax(db, tax_id)
    if not db_tax:
        raise HTTPException(status_code=404, detail="Tax not found")
    await logger.log("delete", "tax", tax_id, before_values=before_dict, risk_level='high')
    return None