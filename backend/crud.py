from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
import models, schemas, security
from typing import Optional, List

# Helper function to get user permissions
def get_user_permissions(db: Session, user_id: int, customer_id: int = None, reseller_id: int = None) -> list[str]:
    """
    Get all effective permissions for a user based on their system-wide,
    customer-scoped, and reseller-scoped roles in a single query.
    """
    # Build the query filters
    scope_filters = [
        # System-level roles
        (models.UserRole.customer_id.is_(None) & models.UserRole.reseller_id.is_(None)),
    ]
    if customer_id is not None:
        scope_filters.append(models.UserRole.customer_id == customer_id)
    if reseller_id is not None:
        scope_filters.append(models.UserRole.reseller_id == reseller_id)

    # Combine filters with OR
    combined_filter = or_(*scope_filters)

    # Execute a single query to get all permission codes
    permissions_query = db.query(models.Permission.code).join(
        models.RolePermission, models.Permission.id == models.RolePermission.permission_id
    ).join(
        models.Role, models.RolePermission.role_id == models.Role.id
    ).join(
        models.UserRole, models.Role.id == models.UserRole.role_id
    ).filter(models.UserRole.user_id == user_id).filter(combined_filter).distinct()

    return [code for code, in permissions_query]

# User CRUD
def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        kind=user.kind,
        is_active=user.is_active,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            db_user.hashed_password = security.get_password_hash(update_data["password"])
            del update_data["password"]
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# UserProfile CRUD
def create_user_profile(db: Session, user_id: int, profile: schemas.UserProfileCreate) -> models.UserProfile:
    db_profile = models.UserProfile(user_id=user_id, **profile.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def get_user_profile(db: Session, user_id: int) -> Optional[models.UserProfile]:
    return db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()

# Role CRUD (New RBAC)
def create_role(db: Session, role: schemas.RoleCreate) -> models.Role:
    db_role = models.Role(
        name=role.name,
        description=role.description,
        scope=role.scope,
        parent_role_id=role.parent_role_id
    )
    if role.permission_codes:
        permissions = db.query(models.Permission).filter(models.Permission.code.in_(role.permission_codes)).all()
        for perm in permissions:
            db_role.role_permissions.append(models.RolePermission(permission=perm))
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_role(db: Session, role_id: int) -> Optional[models.Role]:
    return db.query(models.Role).options(joinedload(models.Role.role_permissions).joinedload(models.RolePermission.permission)).filter(models.Role.id == role_id).first()

def get_role_by_name(db: Session, name: str) -> Optional[models.Role]:
    return db.query(models.Role).options(joinedload(models.Role.role_permissions).joinedload(models.RolePermission.permission)).filter(models.Role.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> list[models.Role]:
    return db.query(models.Role).options(joinedload(models.Role.role_permissions).joinedload(models.RolePermission.permission)).offset(skip).limit(limit).all()

def update_role(db: Session, role_id: int, role_update: schemas.RoleUpdate) -> Optional[models.Role]:
    db_role = get_role(db, role_id)
    if db_role:
        update_data = role_update.dict(exclude_unset=True)
        if "permission_codes" in update_data:
            new_permission_codes = update_data.pop("permission_codes", [])

            # Explicitly delete old associations to avoid the AssertionError
            db.query(models.RolePermission).filter(models.RolePermission.role_id == role_id).delete(synchronize_session=False)

            # Add new associations
            if new_permission_codes:
                permissions = db.query(models.Permission).filter(models.Permission.code.in_(new_permission_codes)).all()
                for perm in permissions:
                    db.add(models.RolePermission(role_id=role_id, permission_id=perm.id))

        for key, value in update_data.items():
            setattr(db_role, key, value)
        
        db.commit()
        # After commit, the object is expired. We need to get it again to have the latest state.
        db.refresh(db_role, attribute_names=['role_permissions'])
        return get_role(db, role_id)
    return db_role

def delete_role(db: Session, role_id: int) -> Optional[models.Role]:
    db_role = get_role(db, role_id)
    if db_role:
        db.delete(db_role)
        db.commit()
    return db_role

# Audit Log CRUD
def create_audit_log(db: Session, log_data: schemas.AuditLogCreate) -> models.AuditLog:
    db_log = models.AuditLog(**log_data.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> List[models.AuditLog]:
    return db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).offset(skip).limit(limit).all()

def get_audit_logs_count(db: Session) -> int:
    return db.query(models.AuditLog).count()


# Permission CRUD (New RBAC)
def create_permission(db: Session, permission: schemas.PermissionCreate) -> models.Permission:
    db_permission = models.Permission(**permission.dict())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def get_permission(db: Session, permission_id: int) -> Optional[models.Permission]:
    return db.query(models.Permission).filter(models.Permission.id == permission_id).first()

def get_permission_by_code(db: Session, code: str) -> Optional[models.Permission]:
    return db.query(models.Permission).filter(models.Permission.code == code).first()

def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> list[models.Permission]:
    return db.query(models.Permission).offset(skip).limit(limit).all()

# UserRole CRUD
def assign_role_to_user(db: Session, user_role: schemas.UserRoleCreate) -> models.UserRole:
    db_user_role = models.UserRole(
        user_id=user_role.user_id,
        role_id=user_role.role_id,
        customer_id=user_role.customer_id,
        reseller_id=user_role.reseller_id
    )
    db.add(db_user_role)
    db.commit()
    db.refresh(db_user_role)
    return db_user_role

def remove_role_from_user(db: Session, user_id: int, role_id: int, customer_id: int = None, reseller_id: int = None) -> Optional[models.UserRole]:
    db_user_role = db.query(models.UserRole).filter(
        models.UserRole.user_id == user_id,
        models.UserRole.role_id == role_id,
        models.UserRole.customer_id == customer_id,
        models.UserRole.reseller_id == reseller_id
    ).first()
    if db_user_role:
        db.delete(db_user_role)
        db.commit()
    return db_user_role

def get_user_roles(db: Session, user_id: int) -> list[models.UserRole]:
    return db.query(models.UserRole).filter(models.UserRole.user_id == user_id).all()

def sync_user_roles(db: Session, user_id: int, role_ids: List[int]) -> List[models.UserRole]:
    """
    Synchronizes the roles for a given user.
    This will remove all existing system-scoped roles and assign the new ones in a single transaction.
    """
    try:
        # Delete all existing system-scoped roles for the user.
        # NOTE: This is a simplification. A more robust implementation would handle
        # customer/reseller scopes if the UI supported assigning them.
        db.query(models.UserRole).filter(
            models.UserRole.user_id == user_id,
            models.UserRole.customer_id.is_(None),
            models.UserRole.reseller_id.is_(None)
        ).delete(synchronize_session=False)

        # Create new role assignments
        if role_ids:
            new_assignments = [models.UserRole(user_id=user_id, role_id=role_id) for role_id in role_ids]
            db.add_all(new_assignments)

        db.commit()
    except Exception:
        db.rollback()
        raise
    return db.query(models.UserRole).options(joinedload(models.UserRole.role)).filter(models.UserRole.user_id == user_id).all()
# Partner CRUD
def get_partner(db: Session, partner_id: int):
    return db.query(models.Partner).filter(models.Partner.id == partner_id).first()

def get_partners(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Partner).offset(skip).limit(limit).all()

def create_partner(db: Session, partner: schemas.PartnerCreate):
    db_partner = models.Partner(**partner.dict())
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    return db_partner

# Administrator CRUD (Modified)
def get_administrator(db: Session, admin_id: int):
    return db.query(models.Administrator).options(joinedload(models.Administrator.user)).filter(models.Administrator.id == admin_id).first()

def get_administrator_by_user_id(db: Session, user_id: int):
    return db.query(models.Administrator).options(joinedload(models.Administrator.user)).filter(models.Administrator.user_id == user_id).first()

def get_administrator_by_email(db: Session, email: str):
    return db.query(models.Administrator).options(joinedload(models.Administrator.user)).join(models.User).filter(models.User.email == email).first()

def get_administrators(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Administrator).options(joinedload(models.Administrator.user)).offset(skip).limit(limit).all()

def get_administrators_count(db: Session) -> int:
    return db.query(models.Administrator).count()

def create_administrator(db: Session, admin_data: schemas.AdministratorCreate, partner_id: int):
    db_admin = models.Administrator(
        user_id=admin_data.user_id,
        partner_id=partner_id,
        phone=admin_data.phone,
        timeout=admin_data.timeout,
        is_active=admin_data.is_active,
        custom_permissions=admin_data.custom_permissions,
        ui_preferences=admin_data.ui_preferences
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def update_administrator(db: Session, admin_id: int, admin_update: schemas.AdministratorUpdate):
    db_admin = get_administrator(db, admin_id)
    if db_admin:
        update_data = admin_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_admin, key, value)
        
        db.commit()
        db.refresh(db_admin)
    return db_admin

def delete_administrator(db: Session, admin_id: int):
    db_admin = get_administrator(db, admin_id)
    if db_admin:
        db.delete(db_admin)
        db.commit()
    return db_admin

# Framework Permission CRUD (Renamed)
def get_framework_permission(db: Session, permission_id: int):
    return db.query(models.FrameworkPermission).filter(models.FrameworkPermission.id == permission_id).first()

def get_framework_permission_by_code(db: Session, code: str):
    return db.query(models.FrameworkPermission).filter(models.FrameworkPermission.code == code).first()

def get_framework_permissions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FrameworkPermission).offset(skip).limit(limit).all()

def create_framework_permission(db: Session, permission: schemas.FrameworkPermissionCreate):
    db_permission = models.FrameworkPermission(**permission.dict())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

# Framework Role CRUD (Renamed)
def get_framework_role(db: Session, role_id: int):
    return db.query(models.FrameworkRole).options(joinedload(models.FrameworkRole.permissions)).filter(models.FrameworkRole.id == role_id).first()

def get_framework_role_by_name(db: Session, name: str):
    return db.query(models.FrameworkRole).options(joinedload(models.FrameworkRole.permissions)).filter(models.FrameworkRole.name == name).first()

def get_framework_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FrameworkRole).options(joinedload(models.FrameworkRole.permissions)).offset(skip).limit(limit).all()

def create_framework_role(db: Session, role: schemas.FrameworkRoleCreate):
    db_role = models.FrameworkRole(name=role.name, description=role.description)
    if role.permission_ids:
        permissions = db.query(models.FrameworkPermission).filter(models.FrameworkPermission.id.in_(role.permission_ids)).all()
        db_role.permissions.extend(permissions)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_framework_role(db: Session, role_id: int, role_update: schemas.FrameworkRoleUpdate):
    db_role = get_framework_role(db, role_id)
    if db_role:
        update_data = role_update.dict(exclude_unset=True)
        if "permission_ids" in update_data:
            permission_ids = update_data.pop("permission_ids")
            permissions = db.query(models.FrameworkPermission).filter(models.FrameworkPermission.id.in_(permission_ids)).all()
            db_role.permissions = permissions
        
        for key, value in update_data.items():
            setattr(db_role, key, value)
        
        db.commit()
        db.refresh(db_role)
    return db_role

def delete_framework_role(db: Session, role_id: int):
    db_role = get_framework_role(db, role_id)
    if db_role:
        db.delete(db_role)
        db.commit()
    return db_role

# Settings (FrameworkConfig) CRUD
def get_setting(db: Session, setting_id: int):
    return db.query(models.FrameworkConfig).filter(models.FrameworkConfig.id == setting_id).first()

def get_setting_by_key(db: Session, key: str):
    return db.query(models.FrameworkConfig).filter(models.FrameworkConfig.config_key == key).first()

def get_settings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FrameworkConfig).offset(skip).limit(limit).all()

def create_setting(db: Session, setting: schemas.SettingCreate):
    db_setting = models.FrameworkConfig(**setting.dict())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def update_setting(db: Session, setting_id: int, setting: schemas.SettingUpdate):
    db_setting = get_setting(db, setting_id)
    if db_setting:
        update_data = setting.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_setting, key, value)
        db.commit()
        db.refresh(db_setting)
    return db_setting

def delete_setting(db: Session, setting_id: int):
    db_setting = get_setting(db, setting_id)
    if db_setting:
        db.delete(db_setting)
        db.commit()
    return db_setting