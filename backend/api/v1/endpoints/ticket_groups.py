from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError

from ..deps import get_db
from .... import crud, schemas, security

router = APIRouter()

@router.post("", response_model=schemas.TicketGroupResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("support.manage_config"))])
def create_ticket_group(group_in: schemas.TicketGroupCreate, db: Session = Depends(get_db)):
    """
    Create a new ticket group.
    """
    return crud.create_ticket_group(db=db, group=group_in)

@router.get("", response_model=List[schemas.TicketGroupResponse], dependencies=[Depends(security.require_permission("support.manage_config"))])
def read_ticket_groups(db: Session = Depends(get_db)):
    """
    Retrieve a list of ticket groups.
    """
    return crud.get_ticket_groups(db)

@router.put("/{group_id}/", response_model=schemas.TicketGroupResponse, dependencies=[Depends(security.require_permission("support.manage_config"))])
def update_ticket_group(group_id: int, group_update: schemas.TicketGroupUpdate, db: Session = Depends(get_db)):
    db_group = crud.update_ticket_group(db, group_id=group_id, group_update=group_update)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Ticket group not found")
    return db_group

@router.delete("/{group_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("support.manage_config"))])
def delete_ticket_group(group_id: int, db: Session = Depends(get_db)):
    try:
        deleted_group = crud.delete_ticket_group(db, group_id=group_id)
        if deleted_group is None:
            raise HTTPException(status_code=404, detail="Ticket group not found")
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return None