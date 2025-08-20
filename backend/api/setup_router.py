from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud, schemas
from .v1.deps import get_db

setup_router = APIRouter()

@setup_router.get("/status")
def get_setup_status(db: Session = Depends(get_db)):
    count = crud.get_administrators_count(db) # Still checking administrators count for initial setup
    return {"setup_complete": count > 0}

@setup_router.post("/create-admin")
def create_initial_admin(setup_data: schemas.SetupData, db: Session = Depends(get_db)):
    count = crud.get_administrators_count(db)
    if count > 0:
        raise HTTPException(status_code=403, detail="Setup has already been completed.")

    # Create partner
    partner_schema = schemas.PartnerCreate(name=setup_data.partner_name)
    partner = crud.create_partner(db, partner=partner_schema)

    # Create the initial user
    user_create_schema = schemas.UserCreate(
        email=setup_data.admin_email,
        password=setup_data.admin_password,
        full_name=setup_data.admin_full_name,
        kind=schemas.UserKind.staff # Initial admin is a staff user
    )
    user = crud.create_user(db, user=user_create_schema)

    # Create the administrator profile linked to the user
    admin_create_schema = schemas.AdministratorCreate(
        user_id=user.id,
        # Other optional fields can be set here if needed
    )
    admin = crud.create_administrator(db, admin_data=admin_create_schema, partner_id=partner.id)

    # Assign Super Admin role to the initial admin user
    super_admin_role = crud.get_role_by_name(db, name="Super Admin")
    if not super_admin_role:
        # If Super Admin role doesn't exist, create it and assign all permissions
        super_admin_role_create = schemas.RoleCreate(
            name="Super Admin",
            description="Full control of all system functions",
            scope=schemas.RoleScope.system,
            permission_codes=[p.code for p in crud.get_permissions(db)] # Assign all existing permissions
        )
        super_admin_role = crud.create_role(db, role=super_admin_role_create)
    
    user_role_create = schemas.UserRoleCreate(user_id=user.id, role_id=super_admin_role.id)
    user_role_create.customer_id = None
    user_role_create.reseller_id = None
    crud.assign_role_to_user(db, user_role_create)

    return {"message": "Initial admin user and setup completed successfully."}

