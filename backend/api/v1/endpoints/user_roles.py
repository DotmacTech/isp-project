from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from ..deps import get_db 
from .... import crud, models, schemas, security

router = APIRouter()

@router.post("/", response_model=schemas.UserRoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
def assign_role_to_user(user_role: schemas.UserRoleCreate, db: Session = Depends(get_db)):
    # Check if user and role exist
    db_user = crud.get_user(db, user_role.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_role = crud.get_role(db, user_role.role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check for existing assignment
    existing_assignment = db.query(models.UserRole).filter(
        models.UserRole.user_id == user_role.user_id,
        models.UserRole.role_id == user_role.role_id,
        models.UserRole.customer_id == user_role.customer_id,
        models.UserRole.reseller_id == user_role.reseller_id
    ).first()
    if existing_assignment:
        raise HTTPException(status_code=400, detail="User already has this role assigned for the given scope")

    return crud.assign_role_to_user(db=db, user_role=user_role)

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
def remove_role_from_user(
    user_id: int,
    role_id: int,
    customer_id: Optional[int] = None,
    reseller_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    db_user_role = crud.remove_role_from_user(db, user_id, role_id, customer_id, reseller_id)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role assignment not found")
    return

@router.get("/{user_id}", response_model=list[schemas.UserRoleResponse], dependencies=[Depends(security.require_permission("system.manage_users"))])
def get_user_roles(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_roles(db, user_id)

@router.put("/{user_id}/sync-roles", response_model=List[schemas.RoleResponse], dependencies=[Depends(security.require_permission("system.manage_users"))])
def sync_user_roles_endpoint(user_id: int, data: schemas.UserRolesSync, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user_roles = crud.sync_user_roles(db=db, user_id=user_id, role_ids=data.role_ids)
    
    updated_roles = [user_role.role for user_role in updated_user_roles if user_role.role]
    return updated_roles
