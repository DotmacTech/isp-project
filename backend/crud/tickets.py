from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func
from typing import Optional, List
from .. import models, schemas

def get_ticket(db: Session, ticket_id: int) -> Optional[models.Ticket]:
    """
    Retrieves a single ticket with all its related data eagerly loaded for a full response.
    This is used for the ticket detail view.
    """
    return db.query(models.Ticket).options(
        joinedload(models.Ticket.customer),
        joinedload(models.Ticket.reporter),
        joinedload(models.Ticket.assignee).joinedload(models.Administrator.user),
        joinedload(models.Ticket.status),
        joinedload(models.Ticket.group),
        joinedload(models.Ticket.ticket_type),
        joinedload(models.Ticket.messages).joinedload(models.TicketMessage.author)
    ).filter(models.Ticket.id == ticket_id).first()

def get_tickets(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None) -> List[models.Ticket]:
    """
    Retrieves a list of tickets, with optional filtering by customer.
    Eagerly loads data needed for the list view but omits messages for performance.
    """
    query = db.query(models.Ticket).options(
        joinedload(models.Ticket.customer),
        joinedload(models.Ticket.reporter),
        joinedload(models.Ticket.assignee).joinedload(models.Administrator.user),
        joinedload(models.Ticket.status),
        joinedload(models.Ticket.group),
        joinedload(models.Ticket.ticket_type)
    ).order_by(models.Ticket.updated_at.desc().nulls_last(), models.Ticket.id.desc())

    if customer_id:
        query = query.filter(models.Ticket.customer_id == customer_id)

    return query.offset(skip).limit(limit).all()

def get_tickets_count(db: Session, customer_id: Optional[int] = None) -> int:
    """
    Gets the total count of tickets, with optional filtering.
    """
    query = db.query(func.count(models.Ticket.id))
    if customer_id:
        query = query.filter(models.Ticket.customer_id == customer_id)
    return query.scalar()

def create_ticket(db: Session, ticket_data: schemas.TicketCreate, reporter_user_id: int) -> models.Ticket:
    """
    Creates a new ticket and its initial message in a single transaction.
    """
    db_ticket = models.Ticket(
        subject=ticket_data.subject,
        priority=ticket_data.priority,
        customer_id=ticket_data.customer_id,
        type_id=ticket_data.type_id,
        status_id=ticket_data.status_id,
        group_id=ticket_data.group_id,
        assign_to=ticket_data.assign_to,
        reporter_user_id=reporter_user_id
    )
    
    initial_message = models.TicketMessage(
        message=ticket_data.initial_message,
        author_user_id=reporter_user_id,
        ticket=db_ticket
    )
    
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def create_ticket_message(db: Session, ticket: models.Ticket, message_data: schemas.TicketMessageCreate, author_user_id: int) -> models.TicketMessage:
    """
    Adds a new message to an existing ticket and updates the ticket's `updated_at` timestamp.
    """
    db_message = models.TicketMessage(
        ticket_id=ticket.id,
        message=message_data.message,
        is_internal_note=message_data.is_internal_note,
        author_user_id=author_user_id
    )
    ticket.updated_at = func.now()
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def update_ticket(db: Session, ticket_id: int, ticket_update: schemas.TicketUpdate) -> Optional[models.Ticket]:
    """
    Updates an existing ticket and its `updated_at` timestamp.
    """
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket:
        update_data = ticket_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_ticket, key, value)
        
        db_ticket.updated_at = func.now()
        
        db.commit()
        db.refresh(db_ticket)
    return db_ticket

def delete_ticket(db: Session, ticket_id: int) -> Optional[models.Ticket]:
    """
    Deletes a ticket from the database.
    """
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket:
        db.delete(db_ticket)
        db.commit()
    return db_ticket