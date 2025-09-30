from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError

from ..deps import get_db
from ....import crud, schemas, security, audit

router = APIRouter()

@router.post("/", response_model=schemas.TicketTypeResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("support.manage_config"))])
async def create_ticket_type(
    type_in: schemas.TicketTypeCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Create a new ticket type.
    """
    new_type = crud.create_ticket_type(db=db, type_data=type_in)
    after_dict = schemas.TicketTypeResponse.model_validate(new_type).model_dump()
    await logger.log(
        action="create", 
        table_name="ticket_type", 
        record_id=new_type.id, 
        after_values=after_dict, 
        risk_level='low',
        business_context=f"Ticket type '{new_type.title}' created."
    )
    return new_type

@router.get("/", response_model=List[schemas.TicketTypeResponse], dependencies=[Depends(security.require_permission("support.manage_config"))])
def read_ticket_types(db: Session = Depends(get_db)):
    """
    Retrieve a list of ticket types.
    """
    return crud.get_ticket_types(db)

@router.put("/{type_id}", response_model=schemas.TicketTypeResponse, dependencies=[Depends(security.require_permission("support.manage_config"))])
async def update_ticket_type(
    type_id: int, 
    type_update: schemas.TicketTypeUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_type_before = crud.get_ticket_type(db, type_id=type_id)
    if db_type_before is None:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    before_dict = schemas.TicketTypeResponse.model_validate(db_type_before).model_dump()
    db.expire(db_type_before)

    updated_type = crud.update_ticket_type(db, type_id=type_id, type_update=type_update)
    if updated_type is None:
        raise HTTPException(status_code=404, detail="Ticket type not found after update.")
    after_dict = schemas.TicketTypeResponse.model_validate(updated_type).model_dump()

    await logger.log(
        action="update", 
        table_name="ticket_type", 
        record_id=type_id, 
        before_values=before_dict, 
        after_values=after_dict, 
        risk_level='low',
        business_context=f"Ticket type '{updated_type.title}' updated."
    )
    return updated_type

@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("support.manage_config"))])
async def delete_ticket_type(
    type_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_type_before = crud.get_ticket_type(db, type_id=type_id)
    if db_type_before is None:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    before_dict = schemas.TicketTypeResponse.model_validate(db_type_before).model_dump()

    try:
        deleted_type = crud.delete_ticket_type(db, type_id=type_id)
        if deleted_type is None:
            raise HTTPException(status_code=404, detail="Ticket type not found")
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    
    await logger.log(
        action="delete", 
        table_name="ticket_type", 
        record_id=type_id, 
        before_values=before_dict, 
        risk_level='medium',
        business_context=f"Ticket type '{before_dict.get('title')}' deleted."
    )
    return None