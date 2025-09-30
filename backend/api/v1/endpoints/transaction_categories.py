from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db
from ....import crud, schemas, security

router = APIRouter()

@router.post("/", response_model=schemas.TransactionCategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def create_transaction_category(category: schemas.TransactionCategoryCreate, db: Session = Depends(get_db)):
    return crud.create_transaction_category(db, category)

@router.get("/", response_model=List[schemas.TransactionCategoryResponse], dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_transaction_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_transaction_categories(db, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=schemas.TransactionCategoryResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
def read_transaction_category(category_id: int, db: Session = Depends(get_db)):
    db_category = crud.get_transaction_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Transaction category not found")
    return db_category

# Note: Update and Delete for transaction categories are omitted for simplicity,
# as they can have complex dependencies. They can be added here if needed.