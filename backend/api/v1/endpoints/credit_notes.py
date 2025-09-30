from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import crud, schemas, security
from ..deps import get_db

router = APIRouter()

@router.get("/", response_model=schemas.PaginatedResponse[schemas.CreditNoteResponse], dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_credit_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(15, ge=1, le=1000),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of credit notes with pagination.
    Requires 'billing.view_invoices' permission.
    """
    credit_notes = crud.get_credit_notes(db, skip=skip, limit=limit, customer_id=customer_id)
    total = crud.get_credit_notes_count(db, customer_id=customer_id)
    return schemas.PaginatedResponse(items=credit_notes, total=total)

@router.post("/", response_model=schemas.CreditNoteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.create_invoices"))])
def create_credit_note(
    credit_note: schemas.CreditNoteCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new credit note.
    Requires 'billing.create_invoices' permission.
    """
    if not crud.get_customer(db, credit_note.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return crud.create_credit_note(db, credit_note)

@router.get("/{credit_note_id}", response_model=schemas.CreditNoteResponse, dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def read_credit_note(credit_note_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single credit note by ID.
    """
    db_credit_note = crud.get_credit_note(db, credit_note_id)
    if not db_credit_note:
        raise HTTPException(status_code=404, detail="Credit Note not found")
    return db_credit_note