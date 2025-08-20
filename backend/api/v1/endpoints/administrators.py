from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
import crud, models, schemas, security

router = APIRouter(prefix="/administrators", tags=["administrators"])

@router.post("/", response_model=schemas.Administrator, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
def create_administrator(
    admin_create: schemas.AdministratorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user) # To get partner_id from current admin
):
    # Check if the user exists and is a staff user
    user = crud.get_user(db, admin_create.user_id)
    if not user or user.kind != schemas.UserKind.staff:
        raise HTTPException(status_code=400, detail="User not found or is not a staff user.")

    # Check if an administrator profile already exists for this user
    if crud.get_administrator_by_user_id(db, admin_create.user_id):
        raise HTTPException(status_code=400, detail="Administrator profile already exists for this user.")

    # For simplicity, assign to the partner of the current logged-in admin
    # In a multi-partner setup, this would need to be more robust
    current_admin_profile = crud.get_administrator_by_user_id(db, current_user.id)
    if not current_admin_profile:
        raise HTTPException(status_code=400, detail="Current user is not an administrator.")
    
    partner_id = current_admin_profile.partner_id

    return crud.create_administrator(db=db, admin_data=admin_create, partner_id=current_admin_profile.partner_id)

@router.get("/me", response_model=schemas.Administrator)
async def read_admin_me(current_admin: schemas.Administrator = Depends(security.get_current_administrator)):
    return current_admin

@router.get("/{admin_id}", response_model=schemas.Administrator, dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_administrator(
    admin_id: int, 
    db: Session = Depends(get_db),
):
    db_admin = crud.get_administrator(db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Administrator not found")
    return db_admin

@router.get("/", response_model=list[schemas.Administrator], dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_administrators(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
):
    admins = crud.get_administrators(db, skip=skip, limit=limit)
    return admins

@router.put("/{admin_id}", response_model=schemas.Administrator, dependencies=[Depends(security.require_permission("system.manage_users"))])
def update_administrator(
    admin_id: int, 
    admin_update: schemas.AdministratorUpdate, 
    db: Session = Depends(get_db),
):
    return crud.update_administrator(db=db, admin_id=admin_id, admin_update=admin_update)

@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
def delete_administrator(
    admin_id: int, 
    db: Session = Depends(get_db),
):
    db_admin = crud.delete_administrator(db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Administrator not found")
    return
