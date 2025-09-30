from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
from .... import crud, models, schemas, security, audit

router = APIRouter()

@router.post("/", response_model=schemas.Administrator, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
async def create_administrator(
    admin_create: schemas.AdministratorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user), # To get partner_id from current admin
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
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

    new_admin = crud.create_administrator(db=db, admin_data=admin_create, partner_id=partner_id)
    after_dict = schemas.Administrator.model_validate(new_admin).model_dump(exclude={'user', 'partner'})
    await logger.log("create", "administrator", new_admin.id, after_values=after_dict, risk_level='high', business_context=f"Administrator profile created for user ID {new_admin.user_id}.")
    return new_admin

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
async def update_administrator(
    admin_id: int, 
    admin_update: schemas.AdministratorUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_admin_before = crud.get_administrator(db, admin_id)
    if not db_admin_before:
        raise HTTPException(status_code=404, detail="Administrator not found")
    before_dict = schemas.Administrator.model_validate(db_admin_before).model_dump(exclude={'user', 'partner'})
    db.expire(db_admin_before)

    updated_admin = crud.update_administrator(db=db, admin_id=admin_id, admin_update=admin_update)
    if not updated_admin:
        raise HTTPException(status_code=404, detail="Administrator not found after update.")
    after_dict = schemas.Administrator.model_validate(updated_admin).model_dump(exclude={'user', 'partner'})

    await logger.log("update", "administrator", admin_id, before_values=before_dict, after_values=after_dict, risk_level='medium', business_context=f"Administrator profile {admin_id} updated.")
    return updated_admin

@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
async def delete_administrator(
    admin_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_admin_before = crud.get_administrator(db, admin_id)
    if not db_admin_before:
        raise HTTPException(status_code=404, detail="Administrator not found")
    before_dict = schemas.Administrator.model_validate(db_admin_before).model_dump(exclude={'user', 'partner'})

    deleted_admin = crud.delete_administrator(db, admin_id=admin_id)
    if deleted_admin is None:
        raise HTTPException(status_code=404, detail="Administrator not found")
    
    await logger.log("delete", "administrator", admin_id, before_values=before_dict, risk_level='critical', business_context=f"Administrator profile {admin_id} for user ID {before_dict.get('user_id')} deleted.")
    return None
