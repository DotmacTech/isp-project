import os
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware

import crud, models, schemas, security, audit
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://10.120.120.29:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Setup Router
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

app.include_router(setup_router, prefix="/api/setup", tags=["setup"])


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = security.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# New RBAC Endpoints
user_router = APIRouter(prefix="/api/users", tags=["users"])

@user_router.get("/me/", response_model=schemas.UserResponse)
async def read_users_me(current_user: schemas.UserResponse = Depends(security.get_current_user)):
    return current_user

@user_router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@user_router.get("/{user_id}", response_model=schemas.UserResponse, dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@user_router.get("/", response_model=list[schemas.UserResponse], dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@user_router.put("/{user_id}", response_model=schemas.UserResponse, dependencies=[Depends(security.require_permission("system.manage_users"))])
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    return crud.update_user(db=db, user_id=user_id, user_update=user)

@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return

app.include_router(user_router)

role_router = APIRouter(prefix="/api/roles", tags=["roles"])

@role_router.post("/", response_model=schemas.RoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    db_role = crud.get_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    return crud.create_role(db=db, role=role)

@role_router.get("/{role_id}", response_model=schemas.RoleResponse, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def read_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@role_router.get("/", response_model=list[schemas.RoleResponse], dependencies=[Depends(security.require_permission("system.manage_roles"))])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    roles = crud.get_roles(db, skip=skip, limit=limit)
    return roles

@role_router.put("/{role_id}", response_model=schemas.RoleResponse, dependencies=[Depends(security.require_permission("system.manage_roles"))])
async def update_role(
    role_id: int, 
    role: schemas.RoleUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    # Capture state before the update
    db_role_before = crud.get_role(db, role_id)
    if not db_role_before:
        raise HTTPException(status_code=404, detail="Role not found")
    before_dict = schemas.RoleResponse.from_orm(db_role_before).dict()
    # Expire the object to ensure it's reloaded from the DB after the update
    db.expire(db_role_before)

    # Perform the update
    updated_role = crud.update_role(db=db, role_id=role_id, role_update=role)
    if not updated_role:
         raise HTTPException(status_code=404, detail="Role not found after update.")
    after_dict = schemas.RoleResponse.from_orm(updated_role).dict()

    # Log the action
    await logger.log("update", "roles", role_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_role

@role_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def delete_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.delete_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return

app.include_router(role_router)

permission_router = APIRouter(prefix="/api/permissions", tags=["permissions"])

@permission_router.post("/", response_model=schemas.PermissionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def create_permission(permission: schemas.PermissionCreate, db: Session = Depends(get_db)):
    db_permission = crud.get_permission_by_code(db, code=permission.code)
    if db_permission:
        raise HTTPException(status_code=400, detail="Permission with this code already exists")
    return crud.create_permission(db=db, permission=permission)

@permission_router.get("/{permission_id}", response_model=schemas.PermissionResponse, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def read_permission(permission_id: int, db: Session = Depends(get_db)):
    db_permission = crud.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return db_permission

@permission_router.get("/", response_model=list[schemas.PermissionResponse], dependencies=[Depends(security.require_permission("system.manage_roles"))])
def read_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    permissions = crud.get_permissions(db, skip=skip, limit=limit)
    return permissions

app.include_router(permission_router)

user_role_router = APIRouter(prefix="/api/user-roles", tags=["user-roles"])

@user_role_router.post("/", response_model=schemas.UserRoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
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

@user_role_router.delete("/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
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

@user_role_router.get("/{user_id}", response_model=list[schemas.UserRoleResponse], dependencies=[Depends(security.require_permission("system.manage_users"))])
def get_user_roles(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_roles(db, user_id)

@user_role_router.put("/{user_id}/sync-roles", response_model=List[schemas.RoleResponse], dependencies=[Depends(security.require_permission("system.manage_users"))])
def sync_user_roles_endpoint(user_id: int, data: schemas.UserRolesSync, db: Session = Depends(get_db)):
    """
    Synchronizes roles for a user. Replaces all existing system-scoped roles with the provided list.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user_roles = crud.sync_user_roles(db=db, user_id=user_id, role_ids=data.role_ids)
    
    # Extract the Role objects from the UserRole relationships to match the response model
    updated_roles = [user_role.role for user_role in updated_user_roles if user_role.role]
    return updated_roles

app.include_router(user_role_router)

# Audit Log Router
audit_router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])

@audit_router.get("/", response_model=schemas.PaginatedAuditLogResponse, dependencies=[Depends(security.require_permission("system.view_audit_logs"))])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = crud.get_audit_logs(db, skip=skip, limit=limit)
    total = crud.get_audit_logs_count(db)
    return {"items": logs, "total": total}

app.include_router(audit_router)

# Partners (Existing, no changes needed for RBAC integration)
@app.post("/api/partners/", response_model=schemas.Partner, status_code=status.HTTP_201_CREATED)
def create_partner(partner: schemas.PartnerCreate, db: Session = Depends(get_db)):
    return crud.create_partner(db=db, partner=partner)

@app.get("/api/partners/", response_model=list[schemas.Partner])
def read_partners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    partners = crud.get_partners(db, skip=skip, limit=limit)
    return partners

@app.get("/api/partners/{partner_id}", response_model=schemas.Partner)
def read_partner(partner_id: int, db: Session = Depends(get_db)):
    db_partner = crud.get_partner(db, partner_id=partner_id)
    if db_partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    return db_partner

# Administrators (Modified to use new User model)
admin_router = APIRouter(prefix="/api/administrators", tags=["administrators"])

@admin_router.post("/", response_model=schemas.Administrator, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_users"))])
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

@admin_router.get("/me", response_model=schemas.Administrator)
async def read_admin_me(current_admin: schemas.Administrator = Depends(security.get_current_administrator)):
    return current_admin

@admin_router.get("/{admin_id}", response_model=schemas.Administrator, dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_administrator(
    admin_id: int, 
    db: Session = Depends(get_db),
):
    db_admin = crud.get_administrator(db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Administrator not found")
    return db_admin

@admin_router.get("/", response_model=list[schemas.Administrator], dependencies=[Depends(security.require_permission("system.manage_users"))])
def read_administrators(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
):
    admins = crud.get_administrators(db, skip=skip, limit=limit)
    return admins

@admin_router.put("/{admin_id}", response_model=schemas.Administrator, dependencies=[Depends(security.require_permission("system.manage_users"))])
def update_administrator(
    admin_id: int, 
    admin_update: schemas.AdministratorUpdate, 
    db: Session = Depends(get_db),
):
    return crud.update_administrator(db=db, admin_id=admin_id, admin_update=admin_update)

@admin_router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_users"))])
def delete_administrator(
    admin_id: int, 
    db: Session = Depends(get_db),
):
    db_admin = crud.delete_administrator(db, admin_id=admin_id)
    if db_admin is None:
        raise HTTPException(status_code=404, detail="Administrator not found")
    return

app.include_router(admin_router)

# Framework Permissions (Renamed endpoints)
framework_permission_router = APIRouter(prefix="/api/framework-permissions", tags=["framework-permissions"])

@framework_permission_router.post("/", response_model=schemas.FrameworkPermissionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.configure_security"))])
def create_framework_permission(permission: schemas.FrameworkPermissionCreate, db: Session = Depends(get_db)):
    db_permission = crud.get_framework_permission_by_code(db, code=permission.code)
    if db_permission:
        raise HTTPException(status_code=400, detail="Framework Permission with this code already exists")
    return crud.create_framework_permission(db=db, permission=permission)

@framework_permission_router.get("/", response_model=list[schemas.FrameworkPermissionResponse], dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_framework_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    permissions = crud.get_framework_permissions(db, skip=skip, limit=limit)
    return permissions

@framework_permission_router.get("/{permission_id}", response_model=schemas.FrameworkPermissionResponse, dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_framework_permission(permission_id: int, db: Session = Depends(get_db)):
    db_permission = crud.get_framework_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Framework Permission not found")
    return db_permission

app.include_router(framework_permission_router)

# Framework Roles (Renamed endpoints)
framework_role_router = APIRouter(prefix="/api/framework-roles", tags=["framework-roles"])

@framework_role_router.post("/", response_model=schemas.FrameworkRoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.configure_security"))])
def create_framework_role(role: schemas.FrameworkRoleCreate, db: Session = Depends(get_db)):
    db_role = crud.get_framework_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(status_code=400, detail="Framework Role with this name already exists")
    return crud.create_framework_role(db=db, role=role)

@framework_role_router.get("/", response_model=list[schemas.FrameworkRoleResponse], dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_framework_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    roles = crud.get_framework_roles(db, skip=skip, limit=limit)
    return roles

@framework_role_router.get("/{role_id}", response_model=schemas.FrameworkRoleResponse, dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_framework_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.get_framework_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Framework Role not found")
    return db_role

@framework_role_router.put("/{role_id}", response_model=schemas.FrameworkRoleResponse, dependencies=[Depends(security.require_permission("system.configure_security"))])
def update_framework_role(role_id: int, role: schemas.FrameworkRoleUpdate, db: Session = Depends(get_db)):
    return crud.update_framework_role(db=db, role_id=role_id, role_update=role)

@framework_role_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.configure_security"))])
def delete_framework_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.delete_framework_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Framework Role not found")
    return

app.include_router(framework_role_router)

# Settings (Existing, no changes needed for RBAC integration)
@app.post("/api/settings/", response_model=schemas.Setting, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.configure_security"))])
def create_setting(setting: schemas.SettingCreate, db: Session = Depends(get_db)):
    db_setting = crud.get_setting_by_key(db, key=setting.config_key)
    if db_setting:
        raise HTTPException(status_code=400, detail="Setting with this key already exists")
    return crud.create_setting(db=db, setting=setting)

@app.get("/api/settings/", response_model=list[schemas.Setting], dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_settings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    settings = crud.get_settings(db, skip=skip, limit=limit)
    return settings

@app.get("/api/settings/{setting_id}", response_model=schemas.Setting, dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_setting(setting_id: int, db: Session = Depends(get_db)):
    db_setting = crud.get_setting(db, setting_id=setting_id)
    if db_setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return db_setting

@app.put("/api/settings/{setting_id}", response_model=schemas.Setting, dependencies=[Depends(security.require_permission("system.configure_security"))])
def update_setting(setting_id: int, setting: schemas.SettingUpdate, db: Session = Depends(get_db)):
    return crud.update_setting(db=db, setting_id=setting_id, setting=setting)

@app.delete("/api/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.configure_security"))])
def delete_setting(setting_id: int, db: Session = Depends(get_db)):
    db_setting = crud.delete_setting(db, setting_id=setting_id)
    if db_setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return