from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db
from .... import crud, schemas, security

router = APIRouter()

@router.post("/", response_model=schemas.Partner, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
def create_partner(partner: schemas.PartnerCreate, db: Session = Depends(get_db)):
    return crud.create_partner(db=db, partner=partner)

@router.get("/", response_model=schemas.PaginatedPartnerResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_partners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    partners = crud.get_partners(db, skip=skip, limit=limit)
    total = crud.get_partners_count(db)
    return {"items": partners, "total": total}

@router.get("/{partner_id}", response_model=schemas.Partner)
def read_partner(partner_id: int, db: Session = Depends(get_db)):
    db_partner = crud.get_partner(db, partner_id=partner_id)
    if db_partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    return db_partner

@router.put("/{partner_id}", response_model=schemas.Partner, dependencies=[Depends(security.require_permission("system.manage_users"))])
def update_partner(partner_id: int, partner: schemas.PartnerUpdate, db: Session = Depends(get_db)):
    db_partner = crud.update_partner(db, partner_id=partner_id, partner_update=partner)
    if db_partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    return db_partner

@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
def delete_partner(partner_id: int, db: Session = Depends(get_db)):
    try:
        deleted_partner = crud.delete_partner(db, partner_id=partner_id)
        if deleted_partner is None:
            raise HTTPException(status_code=404, detail="Partner not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return
