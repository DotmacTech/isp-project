from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db 
from .... import crud, schemas, security, models

router = APIRouter()

@router.post("", response_model=schemas.TicketResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("support.create_tickets"))])
def create_ticket(
    ticket_in: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Create a new ticket.
    Requires 'support.create_tickets' permission.
    """
    # Example validation: ensure customer and ticket type exist
    if not crud.get_customer(db, ticket_in.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    if not crud.get_ticket_type(db, ticket_in.type_id):
        raise HTTPException(status_code=404, detail="Ticket type not found")
    if not crud.get_ticket_status(db, ticket_in.status_id):
        raise HTTPException(status_code=404, detail="Ticket status not found")

    return crud.create_ticket(db=db, ticket_data=ticket_in, reporter_user_id=current_user.id)

@router.get("", response_model=schemas.PaginatedTicketResponse, dependencies=[Depends(security.require_permission("support.view_tickets"))])
def read_tickets(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of tickets with optional pagination.
    Requires 'support.view_tickets' permission.
    """
    tickets = crud.get_tickets(db, skip=skip, limit=limit)
    total = crud.get_tickets_count(db)
    return {"items": tickets, "total": total}

@router.get("/{ticket_id}/", response_model=schemas.TicketResponse, dependencies=[Depends(security.require_permission("support.view_tickets"))])
def read_ticket(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single ticket by ID.
    Requires 'support.view_tickets' permission.
    """
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket

@router.put("/{ticket_id}/", response_model=schemas.TicketResponse, dependencies=[Depends(security.require_permission("support.edit_tickets"))])
def update_ticket(
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing ticket.
    Requires 'support.edit_tickets' permission.
    """
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return crud.update_ticket(db=db, ticket_id=ticket_id, ticket_update=ticket_update)

@router.delete("/{ticket_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("support.edit_tickets"))])
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a ticket.
    Requires 'support.edit_tickets' permission.
    """
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    deleted = crud.delete_ticket(db, ticket_id=ticket_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return