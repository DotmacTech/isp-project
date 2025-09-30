from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import crud, schemas, security
from ..deps import get_db

router = APIRouter()

@router.get("/", response_model=schemas.PaginatedResponse[schemas.TransactionResponse], dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(15, ge=1, le=1000),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of transactions with pagination.
    Requires 'billing.view_invoices' permission.
    """
    transactions = crud.get_transactions(db, skip=skip, limit=limit, customer_id=customer_id)
    total = crud.get_transactions_count(db, customer_id=customer_id)
    return schemas.PaginatedResponse(items=transactions, total=total)

@router.post("/", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.create_invoices"))])
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction.
    Requires 'billing.create_invoices' permission.
    """
    if not crud.get_customer(db, transaction.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    if not crud.get_transaction_category(db, transaction.category_id):
        raise HTTPException(status_code=404, detail="Transaction category not found")
    
    return crud.create_transaction(db, transaction)

@router.get("/{transaction_id}", response_model=schemas.TransactionResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single transaction by ID.
    """
    db_transaction = crud.get_transaction(db, transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction