from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError

from ..deps import get_db
from .... import crud, schemas, security

router = APIRouter()

@router.post("/", response_model=schemas.TicketStatusResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("support.manage_config"))])
def create_ticket_status(status_in: schemas.TicketStatusCreate, db: Session = Depends(get_db)):
    """
    Create a new ticket status.
    Requires 'support.manage_config' permission.
    """
    return crud.create_ticket_status(db=db, status=status_in)

@router.get("/", response_model=List[schemas.TicketStatusResponse], dependencies=[Depends(security.require_permission("support.manage_config"))])
def read_ticket_statuses(db: Session = Depends(get_db)):
    """
    Retrieve a list of ticket statuses.
    Requires 'support.manage_config' permission.
    """
    return crud.get_ticket_statuses(db)

@router.get("/{status_id}", response_model=schemas.TicketStatusResponse, dependencies=[Depends(security.require_permission("support.manage_config"))])
def read_ticket_status(
    status_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single ticket status by ID.
    Requires 'support.manage_config' permission.
    """
    db_status = crud.get_ticket_status(db, status_id=status_id)
    if db_status is None:
        raise HTTPException(status_code=404, detail="Ticket status not found")
    return db_status

@router.put("/{status_id}", response_model=schemas.TicketStatusResponse, dependencies=[Depends(security.require_permission("support.manage_config"))])
def update_ticket_status(status_id: int, status_update: schemas.TicketStatusUpdate, db: Session = Depends(get_db)):
    db_status = crud.update_ticket_status(db, status_id=status_id, status_update=status_update)
    if db_status is None:
        raise HTTPException(status_code=404, detail="Ticket status not found")
    return db_status

@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("support.manage_config"))])
def delete_ticket_status(status_id: int, db: Session = Depends(get_db)):
    """
    Delete a ticket status. Will fail if the status is in use.
    """
    try:
        deleted_status = crud.delete_ticket_status(db, status_id=status_id)
        if deleted_status is None:
            raise HTTPException(status_code=404, detail="Ticket status not found")
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return None