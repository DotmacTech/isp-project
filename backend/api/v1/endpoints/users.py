from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db
import crud, schemas, security, audit

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/", response_model=schemas.UserResponse)
async def read_users_me(current_user: schemas.UserResponse = Depends(security.get_current_user)):
    return current_user

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
async def create_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = crud.create_user(db=db, user=user)
    after_dict = schemas.UserResponse.from_orm(new_user).dict()
    
    await logger.log("create", "users", new_user.id, after_values=after_dict, risk_level='medium')
    
    return new_user

@router.get("/{user_id}", response_model=schemas.UserResponse, dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/", response_model=list[schemas.UserResponse], dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}", response_model=schemas.UserResponse, dependencies=[Depends(security.require_permission("system.manage_users"))])
async def update_user(
    user_id: int, 
    user: schemas.UserUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_user_before = crud.get_user(db, user_id)
    if not db_user_before:
        raise HTTPException(status_code=404, detail="User not found")
    before_dict = schemas.UserResponse.from_orm(db_user_before).dict()
    db.expire(db_user_before)

    updated_user = crud.update_user(db=db, user_id=user_id, user_update=user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found after update.")
    after_dict = schemas.UserResponse.from_orm(updated_user).dict()

    await logger.log("update", "users", user_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
async def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_user_before = crud.get_user(db, user_id)
    if not db_user_before:
        raise HTTPException(status_code=404, detail="User not found")
    before_dict = schemas.UserResponse.from_orm(db_user_before).dict()

    deleted_user = crud.delete_user(db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await logger.log("delete", "users", user_id, before_values=before_dict, risk_level='high')
    return None
