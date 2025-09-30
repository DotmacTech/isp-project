from sqlalchemy.orm import Session
from typing import Optional, List
from .. import models, schemas

from sqlalchemy.exc import IntegrityError

# --- Ticket Status CRUD ---

def get_ticket_status(db: Session, status_id: int) -> Optional[models.TicketStatus]:
    return db.query(models.TicketStatus).filter(models.TicketStatus.id == status_id).first()

def get_ticket_statuses(db: Session, skip: int = 0, limit: int = 100) -> List[models.TicketStatus]:
    return db.query(models.TicketStatus).offset(skip).limit(limit).all()

def create_ticket_status(db: Session, status: schemas.TicketStatusCreate) -> models.TicketStatus:
    db_status = models.TicketStatus(**status.model_dump())
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def update_ticket_status(db: Session, status_id: int, status_update: schemas.TicketStatusUpdate) -> Optional[models.TicketStatus]:
    db_status = get_ticket_status(db, status_id)
    if db_status:
        update_data = status_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_status, key, value)
        db.commit()
        db.refresh(db_status)
    return db_status

def delete_ticket_status(db: Session, status_id: int) -> Optional[models.TicketStatus]:
    """Deletes a ticket status. Raises IntegrityError if it's in use."""
    db_status = get_ticket_status(db, status_id)
    if db_status:
        try:
            db.delete(db_status)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise IntegrityError("Cannot delete status, it is currently in use by one or more tickets.", orig=None, params=None)
    return db_status

# --- Ticket Group CRUD ---

def get_ticket_group(db: Session, group_id: int) -> Optional[models.TicketGroup]:
    return db.query(models.TicketGroup).filter(models.TicketGroup.id == group_id).first()

def get_ticket_groups(db: Session, skip: int = 0, limit: int = 100) -> List[models.TicketGroup]:
    return db.query(models.TicketGroup).offset(skip).limit(limit).all()

def create_ticket_group(db: Session, group: schemas.TicketGroupCreate) -> models.TicketGroup:
    db_group = models.TicketGroup(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def update_ticket_group(db: Session, group_id: int, group_update: schemas.TicketGroupUpdate) -> Optional[models.TicketGroup]:
    db_group = get_ticket_group(db, group_id)
    if db_group:
        update_data = group_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_group, key, value)
        db.commit()
        db.refresh(db_group)
    return db_group

def delete_ticket_group(db: Session, group_id: int) -> Optional[models.TicketGroup]:
    db_group = get_ticket_group(db, group_id)
    if db_group:
        try:
            db.delete(db_group)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise IntegrityError("Cannot delete group, it is currently in use by one or more tickets.", orig=None, params=None)
    return db_group

# --- Ticket Type CRUD ---

def get_ticket_type(db: Session, type_id: int) -> Optional[models.TicketType]:
    return db.query(models.TicketType).filter(models.TicketType.id == type_id).first()

def get_ticket_types(db: Session, skip: int = 0, limit: int = 100) -> List[models.TicketType]:
    return db.query(models.TicketType).offset(skip).limit(limit).all()

def create_ticket_type(db: Session, type_data: schemas.TicketTypeCreate) -> models.TicketType:
    db_type = models.TicketType(**type_data.model_dump())
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def update_ticket_type(db: Session, type_id: int, type_update: schemas.TicketTypeUpdate) -> Optional[models.TicketType]:
    db_type = get_ticket_type(db, type_id)
    if db_type:
        update_data = type_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_type, key, value)
        db.commit()
        db.refresh(db_type)
    return db_type

def delete_ticket_type(db: Session, type_id: int) -> Optional[models.TicketType]:
    db_type = get_ticket_type(db, type_id)
    if db_type:
        try:
            db.delete(db_type)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise IntegrityError("Cannot delete type, it is currently in use by one or more tickets.", orig=None, params=None)
    return db_type