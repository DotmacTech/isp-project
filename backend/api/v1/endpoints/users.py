from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .... import crud
from .... import models
from .... import schemas
from .... import security
from .... import audit
from ..deps import get_db

router = APIRouter()

# This endpoint should be defined before any endpoints with path parameters like `/{user_id}`
# to ensure "me" is not interpreted as a user_id.
@router.get("/me", response_model=schemas.UserResponse)
def read_user_me(current_user: models.User = Depends(security.get_current_active_user)):
    """
    Get current user.
    """
    return current_user

@router.get("/", response_model=schemas.PaginatedResponse[schemas.UserResponse], dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve users with pagination.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    total = crud.get_users_count(db)
    return {"items": users, "total": total}

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Create new user.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = crud.create_user(db=db, user=user)
    # Don't log password hash
    after_dict = schemas.UserResponse.model_validate(new_user).model_dump()
    await logger.log("create", "user", new_user.id, after_values=after_dict, risk_level='high', business_context=f"User '{new_user.email}' created.")
    return new_user

@router.put("/{user_id}", response_model=schemas.UserResponse, dependencies=[Depends(security.require_permission("system.manage_users"))])
async def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Update a user.
    """
    db_user_before = crud.get_user(db, user_id=user_id)
    if db_user_before is None:
        raise HTTPException(status_code=404, detail="User not found")
    before_dict = schemas.UserResponse.model_validate(db_user_before).model_dump()
    db.expire(db_user_before)

    updated_user = crud.update_user(db=db, user_id=user_id, user_update=user)
    after_dict = schemas.UserResponse.model_validate(updated_user).model_dump()
    await logger.log("update", "user", user_id, before_values=before_dict, after_values=after_dict, risk_level='medium', business_context=f"User '{updated_user.email}' updated.")
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
async def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Delete a user.
    """
    db_user_before = crud.get_user(db, user_id=user_id)
    if db_user_before is None:
        raise HTTPException(status_code=404, detail="User not found")
    before_dict = schemas.UserResponse.model_validate(db_user_before).model_dump()

    deleted_user = crud.delete_user(db=db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await logger.log("delete", "user", user_id, before_values=before_dict, risk_level='critical', business_context=f"User '{before_dict.get('email')}' deleted.")
    return None