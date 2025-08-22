from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from ..deps import get_db
import crud

import schemas, models, security

router = APIRouter(prefix="/support", tags=["support"])

# --- Tickets ---
@router.post("/tickets/", response_model=schemas.TicketResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("support.create_tickets"))])
def create_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Basic validation
    if not crud.get_customer(db, ticket.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")

    # Validate that the provided IDs for status, type, etc. exist
    if not crud.get_ticket_status(db, ticket.status_id):
        raise HTTPException(status_code=400, detail=f"Ticket status with ID {ticket.status_id} not found")
    if not crud.get_ticket_type(db, ticket.type_id):
        raise HTTPException(status_code=400, detail=f"Ticket type with ID {ticket.type_id} not found")
    if ticket.group_id and not crud.get_ticket_group(db, ticket.group_id):
        raise HTTPException(status_code=400, detail=f"Ticket group with ID {ticket.group_id} not found")
    if ticket.assign_to and not crud.get_administrator(db, ticket.assign_to):
        raise HTTPException(status_code=400, detail=f"Administrator with ID {ticket.assign_to} not found")

    new_ticket = crud.create_ticket(db=db, ticket_data=ticket, reporter_user_id=current_user.id)
    return crud.get_ticket(db, new_ticket.id) # Re-fetch to get all relationships

@router.get("/tickets/", response_model=schemas.PaginatedTicketResponse, dependencies=[Depends(security.require_permission("support.view_tickets"))], summary="Get a list of tickets")
def read_tickets(
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    tickets = crud.get_tickets(db, skip=skip, limit=limit, customer_id=customer_id)
    total = crud.get_tickets_count(db, customer_id=customer_id)
    return {"items": tickets, "total": total}

@router.get("/tickets/{ticket_id}", response_model=schemas.TicketResponse)
def read_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # --- SCOPED ACCESS LOGIC ---
    # If the user is a customer, ensure they can only access their own tickets.
    if current_user.kind == models.UserKind.customer:
        if not current_user.user_profile or db_ticket.customer_id != current_user.user_profile.customer_id:
            # Return 404 to not leak existence of other tickets
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    else: # User is staff, so check for permission
        user_permissions = crud.get_user_permissions(db, current_user.id)
        if "support.view_tickets" not in user_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions.")

    return db_ticket

@router.put("/tickets/{ticket_id}", response_model=schemas.TicketResponse, dependencies=[Depends(security.require_permission("support.edit_tickets"))])
def update_ticket(
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    db: Session = Depends(get_db)
):
    db_ticket = crud.get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    update_data = ticket_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ticket, key, value)
    
    db.commit()
    db.refresh(db_ticket)
    return crud.get_ticket(db, db_ticket.id) # Re-fetch for relationships

@router.post("/tickets/{ticket_id}/messages", response_model=schemas.TicketMessageResponse, status_code=status.HTTP_201_CREATED)
def add_ticket_message(
    ticket_id: int,
    message: schemas.TicketMessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_ticket = crud.get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # --- Authorization Logic ---
    can_add_message = False
    if current_user.kind == models.UserKind.customer:
        # Customer can add a message to their own ticket
        if current_user.user_profile and db_ticket.customer_id == current_user.user_profile.customer_id:
            can_add_message = True
    else:  # Staff user
        user_permissions = crud.get_user_permissions(db, current_user.id)
        if "support.edit_tickets" in user_permissions:
            can_add_message = True

    if not can_add_message:
        # Use 404 for customer to not leak info, 403 for staff
        if current_user.kind == models.UserKind.customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions.")
    return crud.create_ticket_message(db, db_ticket, message, current_user.id)

# --- Ticket Configuration ---
# This section manages the lookup tables for the support system.
# A specific permission is used to protect these administrative endpoints.
config_router = APIRouter(prefix="/config", dependencies=[Depends(security.require_permission("support.manage_config"))])

# --- Ticket Statuses ---
@config_router.post("/statuses/", response_model=schemas.TicketStatusResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_status(status_data: schemas.TicketStatusCreate, db: Session = Depends(get_db)):
    return crud.create_ticket_status(db, status=status_data)

@config_router.get("/statuses/", response_model=List[schemas.TicketStatusResponse])
def read_ticket_statuses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_ticket_statuses(db, skip=skip, limit=limit)

@config_router.put("/statuses/{status_id}", response_model=schemas.TicketStatusResponse)
def update_ticket_status(status_id: int, status_update: schemas.TicketStatusUpdate, db: Session = Depends(get_db)):
    db_status = crud.get_ticket_status(db, status_id)
    if not db_status:
        raise HTTPException(status_code=404, detail="Ticket status not found")
    return crud.update_ticket_status(db, status_id, status_update)

@config_router.delete("/statuses/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_status(status_id: int, db: Session = Depends(get_db)):
    try:
        deleted_status = crud.delete_ticket_status(db, status_id)
        if not deleted_status:
            raise HTTPException(status_code=404, detail="Ticket status not found")
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete status, it is currently in use by one or more tickets.")

# --- Ticket Groups ---
@config_router.post("/groups/", response_model=schemas.TicketGroupResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_group(group_data: schemas.TicketGroupCreate, db: Session = Depends(get_db)):
    return crud.create_ticket_group(db, group=group_data)

@config_router.get("/groups/", response_model=List[schemas.TicketGroupResponse])
def read_ticket_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_ticket_groups(db, skip=skip, limit=limit)

@config_router.put("/groups/{group_id}", response_model=schemas.TicketGroupResponse)
def update_ticket_group(group_id: int, group_update: schemas.TicketGroupUpdate, db: Session = Depends(get_db)):
    db_group = crud.get_ticket_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Ticket group not found")
    return crud.update_ticket_group(db, group_id, group_update)

@config_router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_group(group_id: int, db: Session = Depends(get_db)):
    deleted_group = crud.delete_ticket_group(db, group_id)
    if not deleted_group:
        raise HTTPException(status_code=404, detail="Ticket group not found")
    return

# --- Ticket Types ---
@config_router.post("/types/", response_model=schemas.TicketTypeResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_type(type_data: schemas.TicketTypeCreate, db: Session = Depends(get_db)):
    return crud.create_ticket_type(db, type_data=type_data)

@config_router.get("/types/", response_model=List[schemas.TicketTypeResponse])
def read_ticket_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_ticket_types(db, skip=skip, limit=limit)

@config_router.put("/types/{type_id}", response_model=schemas.TicketTypeResponse)
def update_ticket_type(type_id: int, type_update: schemas.TicketTypeUpdate, db: Session = Depends(get_db)):
    db_type = crud.get_ticket_type(db, type_id)
    if not db_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    return crud.update_ticket_type(db, type_id, type_update)

@config_router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_type(type_id: int, db: Session = Depends(get_db)):
    deleted_type = crud.delete_ticket_type(db, type_id)
    if not deleted_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    return

router.include_router(config_router)