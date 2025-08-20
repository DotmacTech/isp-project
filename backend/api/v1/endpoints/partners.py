from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
import crud, schemas, security

router = APIRouter(prefix="/partners", tags=["partners"])

@router.post("/", response_model=schemas.Partner, status_code=status.HTTP_201_CREATED)
def create_partner(partner: schemas.PartnerCreate, db: Session = Depends(get_db)):
    return crud.create_partner(db=db, partner=partner)

@router.get("/", response_model=list[schemas.Partner], dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_partners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    partners = crud.get_partners(db, skip=skip, limit=limit)
    return partners

@router.get("/{partner_id}", response_model=schemas.Partner)
def read_partner(partner_id: int, db: Session = Depends(get_db)):
    db_partner = crud.get_partner(db, partner_id=partner_id)
    if db_partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    return db_partner
