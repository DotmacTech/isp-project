from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, text
from .. import models, schemas, auth_utils
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Type, Any, Dict
from .. import freeradius_crud
from .. import freeradius_schemas

def get_user_permissions(db: Session, user_id: int, customer_id: int = None, reseller_id: int = None) -> list[str]:
    """
    Get all effective permissions for a user, including those from parent roles,
    based on their system, customer, and reseller scopes.
    This uses a recursive CTE for high efficiency.
    """
    recursive_cte_sql = text("""
        WITH RECURSIVE effective_roles AS (
            -- Base case: direct roles assigned to the user within the correct scope
            SELECT r.id, r.parent_role_id
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id
              AND (
                  (r.scope = 'system' AND :customer_id IS NULL AND :reseller_id IS NULL) OR
                  (r.scope = 'customer' AND ur.customer_id = :customer_id) OR
                  (r.scope = 'reseller' AND ur.reseller_id = :reseller_id)
              )
        
            UNION
        
            -- Recursive step: roles inherited from the roles found above
            SELECT r.id, r.parent_role_id
            FROM roles r
            JOIN effective_roles er ON r.id = er.parent_role_id
        )
        SELECT DISTINCT p.code
        FROM effective_roles er
        JOIN role_permissions rp ON er.id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id;
    """)

    permissions_query = db.execute(
        recursive_cte_sql,
        {
            "user_id": user_id,
            "customer_id": customer_id,
            "reseller_id": reseller_id
        }
    ).fetchall()

    return [code for code, in permissions_query]

# User CRUD
def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = auth_utils.get_password_hash(user.password)
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

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).order_by(models.User.id).offset(skip).limit(limit).all()

def get_users_count(db: Session) -> int:
    return db.query(models.User).count()

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            db_user.hashed_password = auth_utils.get_password_hash(update_data["password"])
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
    db_profile = models.UserProfile(user_id=user_id, **profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def get_user_profile(db: Session, user_id: int) -> Optional[models.UserProfile]:
    return db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()

# Customer CRUD (Expanded)
def create_customer(db: Session, customer: schemas.CustomerCreate) -> models.Customer:
    """
    Creates a new customer with explicit field mapping for robustness.
    This avoids issues with model_dump() if the schema is complex or has validators.
    """
    db_customer = models.Customer(
        name=customer.name,
        login=customer.login,
        partner_id=customer.partner_id,
        location_id=customer.location_id,
        status=customer.status or 'new', # Ensure a default status
        email=customer.email,
        phone=customer.phone,
        category=customer.category or 'person',
        street_1=customer.street_1,
        zip_code=customer.zip_code,
        city=customer.city,
    )
    if customer.password:
        db_customer.password_hash = auth_utils.get_password_hash(customer.password)

    if customer.billing_config:
        db_customer.billing_config = models.CustomerBilling(**customer.billing_config.model_dump())

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.query(models.Customer).options(joinedload(models.Customer.billing_config)).filter(models.Customer.id == customer_id).first()

def get_customer_by_login(db: Session, login: str) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.login == login).first()

def get_customer_by_email(db: Session, email: str) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.email == email).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None) -> List[models.Customer]:
    query = db.query(models.Customer).options(
        joinedload(models.Customer.billing_config),
        joinedload(models.Customer.partner),
        joinedload(models.Customer.location)
    )
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Customer.name.ilike(search_term),
                models.Customer.login.ilike(search_term),
                models.Customer.email.ilike(search_term),
                models.Customer.phone.ilike(search_term)
            )
        )
    if status:
        query = query.filter(models.Customer.status == status)
    return query.order_by(models.Customer.id.desc()).offset(skip).limit(limit).all()

def get_customers_count(db: Session, search: Optional[str] = None, status: Optional[str] = None) -> int:
    query = db.query(models.Customer)
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            models.Customer.name.ilike(search_term), models.Customer.login.ilike(search_term),
            models.Customer.email.ilike(search_term), models.Customer.phone.ilike(search_term)
        ))
    if status:
        query = query.filter(models.Customer.status == status)
    return query.count()

def get_location(db: Session, location_id: int) -> Optional[models.Location]:
    return db.query(models.Location).filter(models.Location.id == location_id).first()

def create_location(db: Session, location: schemas.LocationCreate) -> models.Location:
    db_location = models.Location(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def update_location(db: Session, location_id: int, location_update: schemas.LocationUpdate) -> Optional[models.Location]:
    db_location = get_location(db, location_id)
    if db_location:
        update_data = location_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_location, key, value)
        db.commit()
        db.refresh(db_location)
    return db_location

def delete_location(db: Session, location_id: int) -> Optional[models.Location]:
    db_location = get_location(db, location_id)
    if db_location:
        db.delete(db_location)
        db.commit()
    return db_location

def get_locations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Location]:
    return db.query(models.Location).order_by(models.Location.name).offset(skip).limit(limit).all()

def update_customer(db: Session, customer_id: int, customer_update: schemas.CustomerUpdate) -> Optional[models.Customer]:
    db_customer = get_customer(db, customer_id)
    if db_customer:
        update_data = customer_update.model_dump(exclude_unset=True, exclude={"billing_config", "password"})
        
        # Handle password update separately
        if customer_update.password:
            db_customer.password_hash = auth_utils.get_password_hash(customer_update.password)

        for key, value in update_data.items():
            setattr(db_customer, key, value)

        if customer_update.billing_config:
            if db_customer.billing_config:
                billing_update_data = customer_update.billing_config.model_dump(exclude_unset=True)
                for key, value in billing_update_data.items():
                    setattr(db_customer.billing_config, key, value)
            else:
                db_customer.billing_config = models.CustomerBilling(**customer_update.billing_config.model_dump())

        db.commit()
        db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    db_customer = get_customer(db, customer_id)
    if db_customer:
        db.delete(db_customer)
        db.commit()
    return db_customer

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
        update_data = role_update.model_dump(exclude_unset=True)
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
    db_log = models.AuditLog(**log_data.model_dump())
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
    db_permission = models.Permission(**permission.model_dump())
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

def update_permission(db: Session, permission_id: int, permission_update: schemas.PermissionUpdate) -> Optional[models.Permission]:
    db_permission = get_permission(db, permission_id)
    if db_permission:
        update_data = permission_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_permission, key, value)
        db.commit()
        db.refresh(db_permission)
    return db_permission

def delete_permission(db: Session, permission_id: int) -> Optional[models.Permission]:
    db_permission = get_permission(db, permission_id)
    if db_permission:
        db.delete(db_permission)
        db.commit()
    return db_permission

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

def get_partners_count(db: Session):
    return db.query(models.Partner).count()

def get_partners(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Partner).offset(skip).limit(limit).all()

def create_partner(db: Session, partner: schemas.PartnerCreate):
    db_partner = models.Partner(**partner.model_dump())
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    return db_partner

def update_partner(db: Session, partner_id: int, partner_update: schemas.PartnerUpdate) -> Optional[models.Partner]:
    db_partner = get_partner(db, partner_id)
    if db_partner:
        update_data = partner_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_partner, key, value)
        db.commit()
        db.refresh(db_partner)
    return db_partner

def delete_partner(db: Session, partner_id: int) -> Optional[models.Partner]:
    # Prevent deleting partner if it's in use
    customer_count = db.query(models.Customer).filter(models.Customer.partner_id == partner_id).count()
    admin_count = db.query(models.Administrator).filter(models.Administrator.partner_id == partner_id).count()
    if customer_count > 0 or admin_count > 0:
        raise ValueError("Cannot delete partner: it is currently assigned to customers or administrators.")

    db_partner = get_partner(db, partner_id)
    if db_partner:
        db.delete(db_partner)
        db.commit()
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
        update_data = admin_update.model_dump(exclude_unset=True)
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

# Settings (FrameworkConfig) CRUD
def get_setting(db: Session, setting_id: int):
    return db.query(models.FrameworkConfig).filter(models.FrameworkConfig.id == setting_id).first()

def get_setting_by_key(db: Session, key: str):
    return db.query(models.FrameworkConfig).filter(models.FrameworkConfig.config_key == key).first()

def get_settings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FrameworkConfig).offset(skip).limit(limit).all()

def create_setting(db: Session, setting: schemas.SettingCreate):
    db_setting = models.FrameworkConfig(**setting.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def update_setting(db: Session, setting_id: int, setting: schemas.SettingUpdate):
    db_setting = get_setting(db, setting_id)
    if db_setting:
        update_data = setting.model_dump(exclude_unset=True)
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


# --- Tariff CRUD ---
def create_internet_tariff(db: Session, tariff: schemas.InternetTariffCreate) -> models.InternetTariff:
    db_tariff = models.InternetTariff(**tariff.model_dump())
    db.add(db_tariff)
    db.commit()
    db.refresh(db_tariff)
    return db_tariff

def get_internet_tariff(db: Session, tariff_id: int) -> Optional[models.InternetTariff]:
    return db.query(models.InternetTariff).filter(models.InternetTariff.id == tariff_id).first()

def get_internet_tariffs(db: Session, skip: int = 0, limit: int = 100) -> List[models.InternetTariff]:
    return db.query(models.InternetTariff).offset(skip).limit(limit).all()

def get_internet_tariffs_count(db: Session) -> int:
    return db.query(models.InternetTariff).count()

def update_internet_tariff(db: Session, tariff_id: int, tariff_update: schemas.InternetTariffUpdate) -> Optional[models.InternetTariff]:
    db_tariff = get_internet_tariff(db, tariff_id)
    if db_tariff:
        update_data = tariff_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tariff, key, value)
        db.commit()
        db.refresh(db_tariff)
    return db_tariff

def delete_internet_tariff(db: Session, tariff_id: int) -> Optional[models.InternetTariff]:
    db_tariff = get_internet_tariff(db, tariff_id)
    if db_tariff:
        db.delete(db_tariff)
        db.commit()
    return db_tariff

# --- Voice Tariff CRUD ---
def create_voice_tariff(db: Session, tariff: schemas.VoiceTariffCreate) -> models.VoiceTariff:
    db_tariff = models.VoiceTariff(**tariff.model_dump())
    db.add(db_tariff)
    db.commit()
    db.refresh(db_tariff)
    return db_tariff

def get_voice_tariff(db: Session, tariff_id: int) -> Optional[models.VoiceTariff]:
    return db.query(models.VoiceTariff).filter(models.VoiceTariff.id == tariff_id).first()

def get_voice_tariffs(db: Session, skip: int = 0, limit: int = 100) -> List[models.VoiceTariff]:
    return db.query(models.VoiceTariff).offset(skip).limit(limit).all()

def get_voice_tariffs_count(db: Session) -> int:
    return db.query(models.VoiceTariff).count()

def update_voice_tariff(db: Session, tariff_id: int, tariff_update: schemas.VoiceTariffUpdate) -> Optional[models.VoiceTariff]:
    db_tariff = get_voice_tariff(db, tariff_id)
    if db_tariff:
        update_data = tariff_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tariff, key, value)
        db.commit()
        db.refresh(db_tariff)
    return db_tariff

def delete_voice_tariff(db: Session, tariff_id: int) -> Optional[models.VoiceTariff]:
    db_tariff = get_voice_tariff(db, tariff_id)
    if db_tariff:
        db.delete(db_tariff)
        db.commit()
    return db_tariff

# --- Recurring Tariff CRUD ---
def create_recurring_tariff(db: Session, tariff: schemas.RecurringTariffCreate) -> models.RecurringTariff:
    db_tariff = models.RecurringTariff(**tariff.model_dump())
    db.add(db_tariff)
    db.commit()
    db.refresh(db_tariff)
    return db_tariff

def get_recurring_tariff(db: Session, tariff_id: int) -> Optional[models.RecurringTariff]:
    return db.query(models.RecurringTariff).filter(models.RecurringTariff.id == tariff_id).first()

def get_recurring_tariffs(db: Session, skip: int = 0, limit: int = 100) -> List[models.RecurringTariff]:
    return db.query(models.RecurringTariff).offset(skip).limit(limit).all()

def get_recurring_tariffs_count(db: Session) -> int:
    return db.query(models.RecurringTariff).count()

def update_recurring_tariff(db: Session, tariff_id: int, tariff_update: schemas.RecurringTariffUpdate) -> Optional[models.RecurringTariff]:
    db_tariff = get_recurring_tariff(db, tariff_id)
    if db_tariff:
        update_data = tariff_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tariff, key, value)
        db.commit()
        db.refresh(db_tariff)
    return db_tariff

def delete_recurring_tariff(db: Session, tariff_id: int) -> Optional[models.RecurringTariff]:
    db_tariff = get_recurring_tariff(db, tariff_id)
    if db_tariff:
        db.delete(db_tariff)
        db.commit()
    return db_tariff

# --- One-Time Tariff CRUD ---
def create_one_time_tariff(db: Session, tariff: schemas.OneTimeTariffCreate) -> models.OneTimeTariff:
    db_tariff = models.OneTimeTariff(**tariff.model_dump())
    db.add(db_tariff)
    db.commit()
    db.refresh(db_tariff)
    return db_tariff

def get_one_time_tariff(db: Session, tariff_id: int) -> Optional[models.OneTimeTariff]:
    return db.query(models.OneTimeTariff).filter(models.OneTimeTariff.id == tariff_id).first()

def get_one_time_tariffs(db: Session, skip: int = 0, limit: int = 100) -> List[models.OneTimeTariff]:
    return db.query(models.OneTimeTariff).offset(skip).limit(limit).all()

def get_one_time_tariffs_count(db: Session) -> int:
    return db.query(models.OneTimeTariff).count()

def update_one_time_tariff(db: Session, tariff_id: int, tariff_update: schemas.OneTimeTariffUpdate) -> Optional[models.OneTimeTariff]:
    db_tariff = get_one_time_tariff(db, tariff_id)
    if db_tariff:
        update_data = tariff_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tariff, key, value)
        db.commit()
        db.refresh(db_tariff)
    return db_tariff

def delete_one_time_tariff(db: Session, tariff_id: int) -> Optional[models.OneTimeTariff]:
    db_tariff = get_one_time_tariff(db, tariff_id)
    if db_tariff:
        db.delete(db_tariff)
        db.commit()
    return db_tariff

# --- Bundle Tariff CRUD ---
def create_bundle_tariff(db: Session, tariff: schemas.BundleTariffCreate) -> models.BundleTariff:
    db_tariff = models.BundleTariff(**tariff.model_dump())
    db.add(db_tariff)
    db.commit()
    db.refresh(db_tariff)
    return db_tariff

def get_bundle_tariff(db: Session, tariff_id: int) -> Optional[models.BundleTariff]:
    return db.query(models.BundleTariff).filter(models.BundleTariff.id == tariff_id).first()

def get_bundle_tariffs(db: Session, skip: int = 0, limit: int = 100) -> List[models.BundleTariff]:
    return db.query(models.BundleTariff).offset(skip).limit(limit).all()

def get_bundle_tariffs_count(db: Session) -> int:
    return db.query(models.BundleTariff).count()

def update_bundle_tariff(db: Session, tariff_id: int, tariff_update: schemas.BundleTariffUpdate) -> Optional[models.BundleTariff]:
    db_tariff = get_bundle_tariff(db, tariff_id)
    if db_tariff:
        update_data = tariff_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tariff, key, value)
        db.commit()
        db.refresh(db_tariff)
    return db_tariff

def delete_bundle_tariff(db: Session, tariff_id: int) -> Optional[models.BundleTariff]:
    db_tariff = get_bundle_tariff(db, tariff_id)
    if db_tariff:
        db.delete(db_tariff)
        db.commit()
    return db_tariff

# --- Customer Portal Tariffs ---
def get_internet_tariffs_for_customer_portal(db: Session, skip: int = 0, limit: int = 100) -> List[models.InternetTariff]:
    """
    Get internet tariffs that are visible on the customer portal.
    """
    return db.query(models.InternetTariff).filter(
        models.InternetTariff.show_on_customer_portal == True
    ).offset(skip).limit(limit).all()

def get_voice_tariffs_for_customer_portal(db: Session, skip: int = 0, limit: int = 100) -> List[models.VoiceTariff]:
    """
    Get voice tariffs that are visible on the customer portal.
    """
    return db.query(models.VoiceTariff).filter(
        models.VoiceTariff.show_on_customer_portal == True
    ).offset(skip).limit(limit).all()

def get_recurring_tariffs_for_customer_portal(db: Session, skip: int = 0, limit: int = 100) -> List[models.RecurringTariff]:
    """
    Get recurring tariffs that are visible on the customer portal.
    """
    return db.query(models.RecurringTariff).filter(
        models.RecurringTariff.show_on_customer_portal == True
    ).offset(skip).limit(limit).all()

def get_bundle_tariffs_for_customer_portal(db: Session, skip: int = 0, limit: int = 100) -> List[models.BundleTariff]:
    """
    Get bundle tariffs that are visible on the customer portal.
    """
    return db.query(models.BundleTariff).filter(
        models.BundleTariff.show_on_customer_portal == True
    ).offset(skip).limit(limit).all()

def get_one_time_tariffs_for_customer_portal(db: Session, skip: int = 0, limit: int = 100) -> List[models.OneTimeTariff]:
    """
    Get one-time tariffs that are visible on the customer portal.
    """
    return db.query(models.OneTimeTariff).filter(
        models.OneTimeTariff.show_on_customer_portal == True
    ).offset(skip).limit(limit).all()

    return db.query(models.BundleTariff).count()

def update_bundle_tariff(db: Session, tariff_id: int, tariff_update: schemas.BundleTariffUpdate) -> Optional[models.BundleTariff]:
    db_tariff = get_bundle_tariff(db, tariff_id)
    if db_tariff:
        update_data = tariff_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tariff, key, value)
        db.commit()
        db.refresh(db_tariff)
    return db_tariff

def delete_bundle_tariff(db: Session, tariff_id: int) -> Optional[models.BundleTariff]:
    db_tariff = get_bundle_tariff(db, tariff_id)
    if db_tariff:
        db.delete(db_tariff)
        db.commit()
    return db_tariff

# --- Service CRUD ---
def create_internet_service(db: Session, service: schemas.InternetServiceCreate) -> models.InternetService:
    db_service = models.InternetService(**service.model_dump())
    db.add(db_service)

    # --- FreeRADIUS Integration ---
    # Sync with radcheck/radreply tables if the service has a login/password
    if db_service.login and db_service.password:
        tariff = db.query(models.InternetTariff).filter(models.InternetTariff.id == db_service.tariff_id).first()
        rate_limit = f"{tariff.speed_upload}k/{tariff.speed_download}k" if tariff else None

        radius_user_data = freeradius_schemas.RadiusUserCreate(
            username=db_service.login,
            password=db_service.password,
            rate_limit=rate_limit,
            framed_ip_address=str(db_service.ipv4) if db_service.ipv4 else None
        )
        freeradius_crud.create_or_update_radius_user(db, user=radius_user_data)
    
    db.commit()
    db.refresh(db_service)
    return db_service

def get_internet_service(db: Session, service_id: int) -> Optional[models.InternetService]:
    return db.query(models.InternetService).options(
        joinedload(models.InternetService.customer),
        joinedload(models.InternetService.tariff)
    ).filter(models.InternetService.id == service_id).first()

def get_internet_services(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None, status: Optional[str] = None) -> List[models.InternetService]:
    query = db.query(models.InternetService).options(
        joinedload(models.InternetService.customer),
        joinedload(models.InternetService.tariff)
    )
    if customer_id:
        query = query.filter(models.InternetService.customer_id == customer_id)
    if status:
        query = query.filter(models.InternetService.status == status)
    return query.offset(skip).limit(limit).all()

def get_internet_services_count(db: Session, customer_id: Optional[int] = None) -> int:
    query = db.query(models.InternetService)
    if customer_id:
        query = query.filter(models.InternetService.customer_id == customer_id)
    return query.count()

def update_internet_service(db: Session, service_id: int, service_update: schemas.InternetServiceUpdate) -> Optional[models.InternetService]:
    db_service = get_internet_service(db, service_id)
    if db_service:
        # Store original login if it's being changed, to clean up old RADIUS user
        original_login = db_service.login
        login_changed = 'login' in service_update.model_dump(exclude_unset=True) and service_update.login != original_login

        update_data = service_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_service, key, value)

        # --- FreeRADIUS Integration ---
        # If the service is active and has credentials, sync it.
        if db_service.status == 'active' and db_service.login and db_service.password:
            tariff = db.query(models.InternetTariff).filter(models.InternetTariff.id == db_service.tariff_id).first()
            rate_limit = f"{tariff.speed_upload}k/{tariff.speed_download}k" if tariff else None
            radius_user_data = freeradius_schemas.RadiusUserCreate(
                username=db_service.login,
                password=db_service.password,
                rate_limit=rate_limit,
                framed_ip_address=str(db_service.ipv4) if db_service.ipv4 else None
            )
            freeradius_crud.create_or_update_radius_user(db, user=radius_user_data)
            # If login was changed, delete the old RADIUS user attributes
            if login_changed and original_login:
                freeradius_crud.delete_radius_user_attributes(db, username=original_login)
        # If the service is NOT active, remove the user from RADIUS to prevent logins.
        elif db_service.login:
            freeradius_crud.delete_radius_user_attributes(db, username=db_service.login)

        db.commit()
        db.refresh(db_service)
    return db_service

def delete_internet_service(db: Session, service_id: int) -> Optional[models.InternetService]:
    db_service = get_internet_service(db, service_id)
    if db_service:
        login_to_delete = db_service.login
        db.delete(db_service)

        # --- FreeRADIUS Integration ---
        if login_to_delete:
            freeradius_crud.delete_radius_user_attributes(db, username=login_to_delete)
        
        db.commit()
    return db_service

# --- Voice Service CRUD ---
def create_voice_service(db: Session, service: schemas.VoiceServiceCreate) -> models.VoiceService:
    db_service = models.VoiceService(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def get_voice_service(db: Session, service_id: int) -> Optional[models.VoiceService]:
    return db.query(models.VoiceService).options(
        joinedload(models.VoiceService.customer),
        joinedload(models.VoiceService.tariff)
    ).filter(models.VoiceService.id == service_id).first()

def get_voice_services(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None, status: Optional[str] = None) -> List[models.VoiceService]:
    query = db.query(models.VoiceService).options(
        joinedload(models.VoiceService.customer),
        joinedload(models.VoiceService.tariff)
    )
    if customer_id:
        query = query.filter(models.VoiceService.customer_id == customer_id)
    if status:
        query = query.filter(models.VoiceService.status == status)
    return query.offset(skip).limit(limit).all()

def get_voice_services_count(db: Session, customer_id: Optional[int] = None, status: Optional[str] = None) -> int:
    query = db.query(models.VoiceService)
    if customer_id:
        query = query.filter(models.VoiceService.customer_id == customer_id)
    if status:
        query = query.filter(models.VoiceService.status == status)
    return query.count()

def update_voice_service(db: Session, service_id: int, service_update: schemas.VoiceServiceUpdate) -> Optional[models.VoiceService]:
    db_service = get_voice_service(db, service_id)
    if db_service:
        update_data = service_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_service, key, value)
        db.commit()
        db.refresh(db_service)
    return db_service

def delete_voice_service(db: Session, service_id: int) -> Optional[models.VoiceService]:
    db_service = get_voice_service(db, service_id)
    if db_service:
        db.delete(db_service)
        db.commit()
    return db_service

# --- Recurring Service CRUD ---
def create_recurring_service(db: Session, service: schemas.RecurringServiceCreate) -> models.RecurringService:
    db_service = models.RecurringService(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def get_recurring_service(db: Session, service_id: int) -> Optional[models.RecurringService]:
    return db.query(models.RecurringService).options(
        joinedload(models.RecurringService.customer),
        joinedload(models.RecurringService.tariff)
    ).filter(models.RecurringService.id == service_id).first()

def get_recurring_services(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None, status: Optional[str] = None) -> List[models.RecurringService]:
    query = db.query(models.RecurringService).options(
        joinedload(models.RecurringService.customer),
        joinedload(models.RecurringService.tariff)
    )
    if customer_id:
        query = query.filter(models.RecurringService.customer_id == customer_id)
    if status:
        query = query.filter(models.RecurringService.status == status)
    return query.offset(skip).limit(limit).all()

def get_recurring_services_count(db: Session, customer_id: Optional[int] = None, status: Optional[str] = None) -> int:
    query = db.query(models.RecurringService)
    if customer_id:
        query = query.filter(models.RecurringService.customer_id == customer_id)
    if status:
        query = query.filter(models.RecurringService.status == status)
    return query.count()

def update_recurring_service(db: Session, service_id: int, service_update: schemas.RecurringServiceUpdate) -> Optional[models.RecurringService]:
    db_service = get_recurring_service(db, service_id)
    if db_service:
        update_data = service_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_service, key, value)
        db.commit()
        db.refresh(db_service)
    return db_service

def delete_recurring_service(db: Session, service_id: int) -> Optional[models.RecurringService]:
    db_service = get_recurring_service(db, service_id)
    if db_service:
        db.delete(db_service)
        db.commit()
    return db_service

# --- Bundle Service CRUD ---
def create_bundle_service(db: Session, service: schemas.BundleServiceCreate) -> models.BundleService:
    db_service = models.BundleService(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def get_bundle_service(db: Session, service_id: int) -> Optional[models.BundleService]:
    return db.query(models.BundleService).options(
        joinedload(models.BundleService.customer),
        joinedload(models.BundleService.bundle)
    ).filter(models.BundleService.id == service_id).first()

def get_bundle_services(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None, status: Optional[str] = None) -> List[models.BundleService]:
    query = db.query(models.BundleService).options(
        joinedload(models.BundleService.customer),
        joinedload(models.BundleService.bundle)
    )
    if customer_id:
        query = query.filter(models.BundleService.customer_id == customer_id)
    if status:
        query = query.filter(models.BundleService.status == status)
    return query.offset(skip).limit(limit).all()

def get_bundle_services_count(db: Session, customer_id: Optional[int] = None, status: Optional[str] = None) -> int:
    query = db.query(models.BundleService)
    if customer_id:
        query = query.filter(models.BundleService.customer_id == customer_id)
    if status:
        query = query.filter(models.BundleService.status == status)
    return query.count()

def update_bundle_service(db: Session, service_id: int, service_update: schemas.BundleServiceUpdate) -> Optional[models.BundleService]:
    db_service = get_bundle_service(db, service_id)
    if db_service:
        update_data = service_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_service, key, value)
        db.commit()
        db.refresh(db_service)
    return db_service

def delete_bundle_service(db: Session, service_id: int) -> Optional[models.BundleService]:
    db_service = get_bundle_service(db, service_id)
    if db_service:
        db.delete(db_service)
        db.commit()
    return db_service

# --- Transaction Category CRUD ---
def get_transaction_category(db: Session, category_id: int) -> Optional[models.TransactionCategory]:
    return db.query(models.TransactionCategory).filter(models.TransactionCategory.id == category_id).first()

def get_transaction_categories(db: Session, skip: int = 0, limit: int = 100) -> List[models.TransactionCategory]:
    return db.query(models.TransactionCategory).order_by(models.TransactionCategory.name).offset(skip).limit(limit).all()

def create_transaction_category(db: Session, category: schemas.TransactionCategoryCreate) -> models.TransactionCategory:
    db_category = models.TransactionCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_transaction_categories_count(db: Session) -> int:
    return db.query(models.TransactionCategory).count()


# --- Billing CRUD ---
def create_invoice(db: Session, invoice: schemas.InvoiceCreate) -> models.Invoice:
    # Business logic (numbering, totals) is handled in the calling service/engine.
    db_invoice = models.Invoice(
        customer_id=invoice.customer_id,
        status=invoice.status,
        number=invoice.number,
        total=invoice.total,
        due=invoice.due,
        date_till=invoice.date_till
    )
    
    for item_data in invoice.items:
        db_invoice.items.append(models.InvoiceItem(**item_data.model_dump()))

    db.add(db_invoice)
    db.flush() # Flush to assign an ID to db_invoice before returning
    db.refresh(db_invoice)
    return db_invoice

def update_invoice(db: Session, invoice_id: int, invoice_update: schemas.InvoiceUpdate) -> Optional[models.Invoice]:
    db_invoice = get_invoice(db, invoice_id)
    if not db_invoice:
        return None

    update_data = invoice_update.model_dump(exclude_unset=True, exclude={"items"})
    for key, value in update_data.items():
        setattr(db_invoice, key, value)

    if invoice_update.items is not None:
        # This logic replaces all existing items with the new ones.
        db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id == invoice_id).delete(synchronize_session=False)
        
        new_total = Decimal("0.0")
        for item_data in invoice_update.items:
            db_item = models.InvoiceItem(**item_data.model_dump(), invoice_id=invoice_id)
            db.add(db_item)
            new_total += item_data.price * item_data.quantity
        
        db_invoice.total = new_total
        # Recalculate due amount based on existing payments
        total_paid = db.query(func.sum(models.Payment.amount)).filter(models.Payment.invoice_id == invoice_id).scalar() or Decimal("0.0")
        db_invoice.due = new_total - total_paid

    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def get_invoice(db: Session, invoice_id: int) -> Optional[models.Invoice]:
    return db.query(models.Invoice).options(joinedload(models.Invoice.items)).filter(models.Invoice.id == invoice_id).first()

def get_invoices(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None) -> List[models.Invoice]:
    query = db.query(models.Invoice).options(joinedload(models.Invoice.items))
    if customer_id:
        query = query.filter(models.Invoice.customer_id == customer_id)
    return query.order_by(models.Invoice.id.desc()).offset(skip).limit(limit).all()

def get_invoices_count(db: Session, customer_id: Optional[int] = None) -> int:
    query = db.query(func.count(models.Invoice.id))
    if customer_id:
        query = query.filter(models.Invoice.customer_id == customer_id)
    return query.scalar()

def get_invoice_statistics(db: Session, customer_id: Optional[int] = None) -> Dict[str, Any]:
    """Get invoice statistics including total, paid, pending, overdue counts and total amounts"""
    from sqlalchemy import case, and_
    from datetime import date
    
    today = date.today()
    
    # Build base query
    query = db.query(
        func.count(models.Invoice.id).label('total'),
        func.sum(case((models.Invoice.status == 'paid', 1), else_=0)).label('paid'),
        func.sum(case((and_(models.Invoice.status != 'paid', models.Invoice.date_till >= today), 1), else_=0)).label('pending'),
        func.sum(case((and_(models.Invoice.status != 'paid', models.Invoice.date_till < today), 1), else_=0)).label('overdue'),
        func.sum(models.Invoice.total).label('total_amount'),
        func.sum(case((models.Invoice.status == 'paid', models.Invoice.total), else_=0)).label('paid_amount'),
        func.sum(case((and_(models.Invoice.status != 'paid', models.Invoice.date_till >= today), models.Invoice.total), else_=0)).label('pending_amount'),
        func.sum(case((and_(models.Invoice.status != 'paid', models.Invoice.date_till < today), models.Invoice.total), else_=0)).label('overdue_amount')
    )
    
    # Apply customer filter if provided
    if customer_id:
        query = query.filter(models.Invoice.customer_id == customer_id)
    
    result = query.first()
    
    return {
        'total': result.total or 0,
        'paid': result.paid or 0,
        'pending': result.pending or 0,
        'overdue': result.overdue or 0,
        'total_amount': float(result.total_amount or 0),
        'paid_amount': float(result.paid_amount or 0),
        'pending_amount': float(result.pending_amount or 0),
        'overdue_amount': float(result.overdue_amount or 0)
    }

def create_payment(db: Session, payment: schemas.PaymentCreate) -> models.Payment:
    db_payment = models.Payment(**payment.model_dump())
    db.add(db_payment)
    
    # If linked to an invoice, update invoice status
    if payment.invoice_id:
        invoice = get_invoice(db, payment.invoice_id)
        if invoice:
            invoice.due -= payment.amount
            if invoice.due <= 0:
                invoice.status = 'paid'

    # We commit here to ensure the payment and invoice status updates are reflected
    # before we check the customer's overall balance status.
    db.commit()

    # --- Immediate Reactivation Logic ---
    # After a payment, check if the customer has any other outstanding invoices.
    if not has_unpaid_invoices(db, customer_id=payment.customer_id):
        print(f"Customer {payment.customer_id} has no more unpaid invoices. Reactivating services.")
        reactivated_count = reactivate_customer_services(db, customer_id=payment.customer_id)
        
        # Also update the customer's status if they were blocked
        customer_to_update = get_customer(db, payment.customer_id)
        status_changed = False
        if customer_to_update and customer_to_update.status == 'blocked':
            customer_to_update.status = 'active'
            status_changed = True
            print(f"  -> Set customer {customer_to_update.id} status to 'active'")

        if reactivated_count > 0 or status_changed:
            # The reactivation function stages the changes, so we commit them here.
            db.commit()
            if reactivated_count > 0:
                print(f"Reactivated {reactivated_count} services for customer {payment.customer_id}.")

    db.refresh(db_payment)
    return db_payment

def get_payment(db: Session, payment_id: int) -> Optional[models.Payment]:
    return db.query(models.Payment).filter(models.Payment.id == payment_id).first()

def update_payment(db: Session, payment_id: int, payment_update: schemas.PaymentUpdate) -> Optional[models.Payment]:
    db_payment = get_payment(db, payment_id)
    if db_payment:
        update_data = payment_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_payment, key, value)
        db.commit()
        db.refresh(db_payment)
    return db_payment

def get_payments(db: Session, skip: int = 0, limit: int = 100) -> List[models.Payment]:
    return db.query(models.Payment).offset(skip).limit(limit).all()

def get_payments_count(db: Session) -> int:
    return db.query(models.Payment).count()

def get_payment_statistics(db: Session) -> Dict[str, Any]:
    """Get payment statistics including counts and amounts by status"""
    from sqlalchemy import func
    
    # Get total count and sum of all payments
    result = db.query(
        func.count(models.Payment.id).label('total'),
        func.sum(models.Payment.amount).label('total_amount')
    ).first()
    
    # For now, we'll assume all payments are successful
    # In a real implementation, you might have different payment statuses
    return {
        'total': result.total or 0,
        'total_amount': float(result.total_amount or 0),
        'successful': result.total or 0,
        'pending': 0,
        'failed': 0
    }

def get_payment_methods(db: Session, is_active: Optional[bool] = True) -> List[models.PaymentMethod]:
    query = db.query(models.PaymentMethod)
    # If is_active is True (default) or None, filter for active methods.
    # If is_active is explicitly False, return all methods.
    if is_active:
        query = query.filter(models.PaymentMethod.is_active == True)
    return query.order_by(models.PaymentMethod.name).all()

def get_taxes(db: Session, show_all: bool = False) -> List[models.Tax]:
    """
    Retrieves a list of taxes.
    By default, only non-archived taxes are returned.
    """
    query = db.query(models.Tax)
    if not show_all:
        query = query.filter(models.Tax.archived == False)
    return query.order_by(models.Tax.name).all()

def get_tax(db: Session, tax_id: int) -> Optional[models.Tax]:
    """Retrieves a single tax by its ID."""
    return db.query(models.Tax).filter(models.Tax.id == tax_id).first()

def create_tax(db: Session, tax: schemas.TaxCreate) -> models.Tax:
    """Creates a new tax."""
    db_tax = models.Tax(**tax.model_dump())
    db.add(db_tax)
    db.commit()
    db.refresh(db_tax)
    return db_tax

def update_tax(db: Session, tax_id: int, tax_update: schemas.TaxUpdate) -> Optional[models.Tax]:
    """Updates an existing tax."""
    db_tax = get_tax(db, tax_id)
    if db_tax:
        update_data = tax_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tax, key, value)
        db.commit()
        db.refresh(db_tax)
    return db_tax

def delete_tax(db: Session, tax_id: int) -> Optional[models.Tax]:
    """Soft deletes a tax by archiving it."""
    db_tax = get_tax(db, tax_id)
    if db_tax:
        db_tax.archived = True
        db.commit()
    return db_tax

def get_payment_method(db: Session, method_id: int) -> Optional[models.PaymentMethod]:
    """
    Retrieves a single payment method by its ID.
    """
    return db.query(models.PaymentMethod).filter(models.PaymentMethod.id == method_id).first()

def create_payment_method(db: Session, method: schemas.PaymentMethodCreate) -> models.PaymentMethod:
    """
    Creates a new payment method.
    """
    db_method = models.PaymentMethod(**method.model_dump())
    db.add(db_method)
    db.commit()
    db.refresh(db_method)
    return db_method

def update_payment_method(db: Session, method_id: int, method_update: schemas.PaymentMethodUpdate) -> Optional[models.PaymentMethod]:
    """
    Updates an existing payment method.
    """
    db_method = get_payment_method(db, method_id)
    if db_method:
        update_data = method_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_method, key, value)
        db.commit()
        db.refresh(db_method)
    return db_method

def delete_payment_method(db: Session, method_id: int) -> Optional[models.PaymentMethod]:
    """
    Deletes a payment method if it is not in use.
    Raises ValueError if the method is in use.
    """
    payment_count = db.query(models.Payment).filter(models.Payment.payment_type_id == method_id).count()
    if payment_count > 0:
        raise ValueError("Cannot delete payment method, it is currently in use by one or more payments.")
    db_method = get_payment_method(db, method_id)
    if db_method:
        db.delete(db_method)
        db.commit()
    return db_method

# --- Automated Billing & Suspension CRUD Functions ---

def get_customers_due_for_billing(db: Session, billing_day: int) -> List[models.Customer]:
    """
    Retrieves active customers who are enabled for billing and are due on the specified day.
    """
    return db.query(models.Customer).join(models.Customer.billing_config).filter(
        models.Customer.status == 'active',
        models.CustomerBilling.enabled == True,
        models.CustomerBilling.billing_date == billing_day
    ).all()

def suspend_all_active_services_for_customer(db: Session, customer_id: int) -> int:
    """
    Finds all active services (internet, voice, etc.) for a customer and sets their status to 'blocked'.
    Returns the total number of services updated.
    NOTE: This function does NOT commit the session.
    """
    total_updated = 0
    service_models = [models.InternetService, models.VoiceService, models.RecurringService, models.BundleService]
    
    for service_model in service_models:
        services_to_update = db.query(service_model).filter(
            service_model.customer_id == customer_id,
            service_model.status == 'active'
        )
        count = services_to_update.update({"status": "blocked"}, synchronize_session=False)
        total_updated += count
        
    return total_updated

def get_customers_with_overdue_invoices(db: Session) -> List[models.Customer]:
    """
    Retrieves customers who have unpaid invoices that are past their grace period.
    """
    # This subquery finds the IDs of customers with at least one overdue invoice.
    overdue_customer_ids = db.query(
        models.Invoice.customer_id
    ).join(
        models.Customer, models.Invoice.customer_id == models.Customer.id
    ).join(
        models.CustomerBilling, models.Customer.id == models.CustomerBilling.customer_id
    ).filter(
        models.Invoice.status == 'not_paid',
        # The expression for an overdue invoice is: invoice_date + grace_period_days < today
        models.Invoice.date_created + (models.CustomerBilling.grace_period * text("'1 day'::interval")) < func.current_date()
    ).distinct().subquery()

    # Now, fetch the full customer objects for those IDs.
    return db.query(models.Customer).filter(
        models.Customer.id.in_(overdue_customer_ids.select())
    ).all()

def has_unpaid_invoices(db: Session, customer_id: int) -> bool:
    """Checks if a customer has any invoices with status 'not_paid'."""
    count = db.query(models.Invoice).filter(
        models.Invoice.customer_id == customer_id,
        models.Invoice.status == 'not_paid'
    ).count()
    return count > 0

def reactivate_customer_services(db: Session, customer_id: int) -> int:
    """
    Finds all 'blocked' services (internet, voice, etc.) for a customer and sets their status to 'active'.
    Returns the total number of services updated.
    NOTE: This function does NOT commit the session. The caller is responsible for the commit.
    """
    total_updated = 0
    service_models = [models.InternetService, models.VoiceService, models.RecurringService, models.BundleService]

    for service_model in service_models:
        services_to_update = db.query(service_model).filter(
            service_model.customer_id == customer_id,
            service_model.status == 'blocked'
        )
        count = services_to_update.update({"status": "active"}, synchronize_session=False)
        total_updated += count
    
    return total_updated

def get_customers_to_reactivate(db: Session) -> List[models.Customer]:
    """
    Retrieves customers who have at least one 'blocked' service but no 'not_paid' invoices.
    This is a reconciliation function for the scheduled job.
    """
    customers_with_unpaid_invoices = db.query(models.Invoice.customer_id).filter(
        models.Invoice.status == 'not_paid'
    ).distinct().subquery()

    customers_with_blocked_services = db.query(models.InternetService.customer_id).filter(
        models.InternetService.status == 'blocked'
    ).distinct().subquery()

    return db.query(models.Customer).filter(
        models.Customer.id.in_(customers_with_blocked_services.select()),
        models.Customer.id.notin_(customers_with_unpaid_invoices.select())
    ).all()

def create_lead(db: Session, lead: schemas.LeadCreate) -> models.Lead:
    db_lead = models.Lead(**lead.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

def get_lead(db: Session, lead_id: int) -> Optional[models.Lead]:
    return db.query(models.Lead).filter(models.Lead.id == lead_id).first()

def get_leads(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None) -> List[models.Lead]:
    query = db.query(models.Lead)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Lead.name.ilike(search_term),
                models.Lead.email.ilike(search_term),
                models.Lead.phone.ilike(search_term)
            )
        )
    if status:
        query = query.filter(models.Lead.status == status)
    return query.order_by(models.Lead.id.desc()).offset(skip).limit(limit).all()

def get_leads_count(db: Session, search: Optional[str] = None, status: Optional[str] = None) -> int:
    query = db.query(models.Lead)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Lead.name.ilike(search_term),
                models.Lead.email.ilike(search_term),
                models.Lead.phone.ilike(search_term)
            )
        )
    if status:
        query = query.filter(models.Lead.status == status)
    return query.count()

def update_lead(db: Session, db_obj: models.Lead, obj_in: schemas.LeadUpdate) -> models.Lead:
    update_data = obj_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_lead(db: Session, lead_id: int) -> Optional[models.Lead]:
    db_lead = get_lead(db, lead_id)
    if db_lead:
        db.delete(db_lead)
        db.commit()
    return db_lead

def create_opportunity(db: Session, opportunity: schemas.OpportunityCreate) -> models.Opportunity:
    db_opportunity = models.Opportunity(**opportunity.model_dump())
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity


def get_opportunity(db: Session, opportunity_id: int) -> Optional[models.Opportunity]:
    return db.query(models.Opportunity).options(joinedload(models.Opportunity.lead)).filter(models.Opportunity.id == opportunity_id).first()

def get_opportunities(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, stage: Optional[str] = None) -> List[models.Opportunity]:
    query = db.query(models.Opportunity).options(joinedload(models.Opportunity.lead))
    if search:
        search_term = f"%{search}%"
        query = query.filter(models.Opportunity.name.ilike(search_term))
    if stage:
        query = query.filter(models.Opportunity.stage == stage)
    return query.order_by(models.Opportunity.id.desc()).offset(skip).limit(limit).all()

def get_opportunities_count(db: Session, search: Optional[str] = None, stage: Optional[str] = None) -> int:
    query = db.query(models.Opportunity)
    if search:
        search_term = f"%{search}%"
        query = query.filter(models.Opportunity.name.ilike(search_term))
    if stage:
        query = query.filter(models.Opportunity.stage == stage)
    return query.count()

def update_opportunity(db: Session, db_obj: models.Opportunity, obj_in: schemas.OpportunityUpdate) -> models.Opportunity:
    update_data = obj_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_opportunity(db: Session, opportunity_id: int) -> Optional[models.Opportunity]:
    db_opportunity = get_opportunity(db, opportunity_id)
    if db_opportunity:
        db.delete(db_opportunity)
        db.commit()
    return db_opportunity

def convert_opportunity_to_customer(db: Session, opportunity: models.Opportunity, conversion_data: schemas.OpportunityConvert) -> models.Customer:
    """
    Converts a won opportunity into a new customer.
    This is a transactional operation.
    """
    try:
        # 1. Get the original lead
        lead = get_lead(db, opportunity.lead_id)
        if not lead:
            raise ValueError("Original lead for this opportunity not found.")

        # 2. Create the new customer record
        customer_create_schema = schemas.CustomerCreate(
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            **conversion_data.model_dump()
        )
        new_customer = create_customer(db, customer=customer_create_schema)

        # 3. Update the opportunity
        opportunity.stage = "Closed Won"
        opportunity.customer_id = new_customer.id

        # 4. Update the lead
        lead.status = "Converted"
        
        db.commit()
        db.refresh(new_customer)
        return new_customer
    except Exception as e:
        db.rollback()
        raise e

# --- Proforma Invoice CRUD ---

def create_proforma_invoice(db: Session, invoice: schemas.ProformaInvoiceCreate) -> models.ProformaInvoice:
    db_invoice = models.ProformaInvoice(
        customer_id=invoice.customer_id,
        status=invoice.status,
        number=invoice.number,
        total=invoice.total,
        due=invoice.due,
        date_till=invoice.date_till
    )
    
    for item_data in invoice.items:
        db_invoice.items.append(models.ProformaInvoiceItem(**item_data.model_dump()))

    db.add(db_invoice)
    db.flush()
    db.refresh(db_invoice)
    return db_invoice

def get_proforma_invoice(db: Session, invoice_id: int) -> Optional[models.ProformaInvoice]:
    return db.query(models.ProformaInvoice).options(joinedload(models.ProformaInvoice.items)).filter(models.ProformaInvoice.id == invoice_id).first()

def get_proforma_invoices(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None) -> List[models.ProformaInvoice]:
    query = db.query(models.ProformaInvoice).options(joinedload(models.ProformaInvoice.items))
    if customer_id:
        query = query.filter(models.ProformaInvoice.customer_id == customer_id)
    return query.order_by(models.ProformaInvoice.id.desc()).offset(skip).limit(limit).all()

def get_proforma_invoices_count(db: Session, customer_id: Optional[int] = None) -> int:
    query = db.query(func.count(models.ProformaInvoice.id))
    if customer_id:
        query = query.filter(models.ProformaInvoice.customer_id == customer_id)
    return query.scalar()

def update_proforma_invoice(db: Session, invoice_id: int, invoice_update: schemas.ProformaInvoiceCreate) -> Optional[models.ProformaInvoice]:
    db_invoice = get_proforma_invoice(db, invoice_id)
    if not db_invoice:
        return None

    update_data = invoice_update.model_dump(exclude_unset=True, exclude={"items"})
    for key, value in update_data.items():
        setattr(db_invoice, key, value)

    if invoice_update.items is not None:
        db.query(models.ProformaInvoiceItem).filter(models.ProformaInvoiceItem.proforma_invoice_id == invoice_id).delete(synchronize_session=False)
        
        new_total = Decimal("0.0")
        for item_data in invoice_update.items:
            db_item = models.ProformaInvoiceItem(**item_data.model_dump(), proforma_invoice_id=invoice_id)
            db.add(db_item)
            new_total += item_data.price * item_data.quantity
        
        db_invoice.total = new_total
        db_invoice.due = new_total

    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def delete_proforma_invoice(db: Session, invoice_id: int) -> Optional[models.ProformaInvoice]:
    db_invoice = get_proforma_invoice(db, invoice_id)
    if db_invoice:
        db.delete(db_invoice)
        db.commit()
    return db_invoice

# --- Transaction CRUD ---

def create_transaction(db: Session, transaction: schemas.TransactionCreate) -> models.Transaction:
    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transaction(db: Session, transaction_id: int) -> Optional[models.Transaction]:
    return db.query(models.Transaction).options(
        joinedload(models.Transaction.customer),
        joinedload(models.Transaction.category)
    ).filter(models.Transaction.id == transaction_id).first()

def get_transactions(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None) -> List[models.Transaction]:
    query = db.query(models.Transaction).options(
        joinedload(models.Transaction.customer),
        joinedload(models.Transaction.category)
    )
    if customer_id:
        query = query.filter(models.Transaction.customer_id == customer_id)
    return query.order_by(models.Transaction.date.desc(), models.Transaction.id.desc()).offset(skip).limit(limit).all()

def get_transactions_count(db: Session, customer_id: Optional[int] = None) -> int:
    query = db.query(func.count(models.Transaction.id))
    if customer_id:
        query = query.filter(models.Transaction.customer_id == customer_id)
    return query.scalar()

# --- Credit Note CRUD ---

def create_credit_note(db: Session, credit_note: schemas.CreditNoteCreate) -> models.CreditNote:
    db_credit_note = models.CreditNote(**credit_note.model_dump())
    db.add(db_credit_note)
    db.commit()
    db.refresh(db_credit_note)
    return db_credit_note

def get_credit_note(db: Session, credit_note_id: int) -> Optional[models.CreditNote]:
    return db.query(models.CreditNote).options(
        joinedload(models.CreditNote.customer)
    ).filter(models.CreditNote.id == credit_note_id).first()

def get_credit_notes(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None) -> List[models.CreditNote]:
    query = db.query(models.CreditNote).options(
        joinedload(models.CreditNote.customer)
    )
    if customer_id:
        query = query.filter(models.CreditNote.customer_id == customer_id)
    return query.order_by(models.CreditNote.date_created.desc(), models.CreditNote.id.desc()).offset(skip).limit(limit).all()

def get_credit_notes_count(db: Session, customer_id: Optional[int] = None) -> int:
    query = db.query(func.count(models.CreditNote.id))
    if customer_id:
        query = query.filter(models.CreditNote.customer_id == customer_id)
    return query.scalar()


# --- Usage Tracking CRUD ---

def create_usage_record(db: Session, usage: schemas.UsageTrackingCreate) -> models.UsageTracking:
    """Creates a new usage tracking record."""
    db_usage = models.UsageTracking(**usage.model_dump())
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage

# =============================================================================
# NETWORK & DEVICE MANAGEMENT CRUD
# =============================================================================

# --- Generic Lookup Table CRUD ---

def get_network_lookup(db: Session, model: Type[Any], item_id: int) -> Optional[Any]:
    return db.query(model).filter(model.id == item_id).first()

def get_network_lookups(db: Session, model: Type[Any], skip: int, limit: int) -> List[Any]:
    return db.query(model).order_by(model.name).offset(skip).limit(limit).all()

def create_network_lookup(db: Session, model: Type[Any], item: schemas.NetworkLookupCreate) -> Any:
    db_item = model(name=item.name)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_network_lookup(db: Session, model: Type[Any], item_id: int) -> Optional[Any]:
    db_item = get_network_lookup(db, model, item_id)
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item

# --- Network Site CRUD ---

def get_network_site(db: Session, site_id: int) -> Optional[models.NetworkSite]:
    return db.query(models.NetworkSite).filter(models.NetworkSite.id == site_id).first()

def get_network_sites(db: Session, skip: int = 0, limit: int = 100) -> List[models.NetworkSite]:
    return db.query(models.NetworkSite).order_by(models.NetworkSite.title).offset(skip).limit(limit).all()

def get_network_sites_count(db: Session) -> int:
    return db.query(models.NetworkSite).count()

def create_network_site(db: Session, site: schemas.NetworkSiteCreate) -> models.NetworkSite:
    db_site = models.NetworkSite(**site.model_dump())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

def update_network_site(db: Session, site_id: int, site_update: schemas.NetworkSiteUpdate) -> Optional[models.NetworkSite]:
    db_site = get_network_site(db, site_id)
    if db_site:
        update_data = site_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_site, key, value)
        db.commit()
        db.refresh(db_site)
    return db_site

def delete_network_site(db: Session, site_id: int) -> Optional[models.NetworkSite]:
    db_site = get_network_site(db, site_id)
    if db_site:
        db.delete(db_site)
        db.commit()
    return db_site

# --- Monitoring Device CRUD ---

def get_monitoring_device(db: Session, device_id: int) -> Optional[models.MonitoringDevice]:
    return db.query(models.MonitoringDevice).filter(models.MonitoringDevice.id == device_id).first()

def get_monitoring_devices(db: Session, skip: int = 0, limit: int = 100) -> List[models.MonitoringDevice]:
    return db.query(models.MonitoringDevice).order_by(models.MonitoringDevice.title).offset(skip).limit(limit).all()

def get_monitoring_devices_count(db: Session) -> int:
    return db.query(models.MonitoringDevice).count()

def create_monitoring_device(db: Session, device: schemas.MonitoringDeviceCreate) -> models.MonitoringDevice:
    db_device = models.MonitoringDevice(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

def update_monitoring_device(db: Session, device_id: int, device_update: schemas.MonitoringDeviceUpdate) -> Optional[models.MonitoringDevice]:
    db_device = get_monitoring_device(db, device_id)
    if db_device:
        update_data = device_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_device, key, value)
        db.commit()
        db.refresh(db_device)
    return db_device

def delete_monitoring_device(db: Session, device_id: int) -> Optional[models.MonitoringDevice]:
    db_device = get_monitoring_device(db, device_id)
    if db_device:
        db.delete(db_device)
        db.commit()
    return db_device

# --- Router CRUD ---

def get_router(db: Session, router_id: int) -> Optional[models.Router]:
    return db.query(models.Router).filter(models.Router.id == router_id).first()

def get_router_by_ip(db: Session, ip: str) -> Optional[models.Router]:
    return db.query(models.Router).filter(models.Router.ip == ip).first()

def get_routers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Router]:
    return db.query(models.Router).order_by(models.Router.title).offset(skip).limit(limit).all()

def get_routers_count(db: Session) -> int:
    return db.query(models.Router).count()

def create_router(db: Session, router: schemas.RouterCreate) -> models.Router:
    db_router = models.Router(**router.model_dump())
    db.add(db_router)

    # --- Sync to FreeRADIUS nas table ---
    if db_router.radius_secret:
        db.flush()  # Flush to get the router ID for the description
        nas_create = freeradius_schemas.NasCreate(
            nasname=str(router.ip),
            shortname=router.title,
            secret=router.radius_secret,
            description=f"Managed by ISP Framework - Router ID: {db_router.id}"
        )
        freeradius_crud.create_nas(db, nas=nas_create)

    db.commit()
    db.refresh(db_router)
    return db_router

def update_router(db: Session, router_id: int, router_update: schemas.RouterUpdate) -> Optional[models.Router]:
    db_router = get_router(db, router_id)
    if not db_router:
        return None

    # Find the corresponding NAS entry using the router's original unique title
    original_title = db_router.title
    db_nas = freeradius_crud.get_nas_by_shortname(db, shortname=original_title)

    # Get the update data from the Pydantic model
    update_data = router_update.model_dump(exclude_unset=True)

    # --- Sync to FreeRADIUS nas table ---
    # Determine the final state of the router's RADIUS-relevant properties
    # by checking the update data first, then falling back to the existing object.
    final_radius_secret = update_data.get("radius_secret", db_router.radius_secret)
    final_ip = update_data.get("ip", str(db_router.ip))
    final_title = update_data.get("title", db_router.title)

    if final_radius_secret is not None: # Handles setting a secret, even an empty one ""
        nas_data = {
            "nasname": str(final_ip),
            "shortname": final_title,
            "secret": final_radius_secret,
            "description": f"Managed by ISP Framework - Router ID: {db_router.id}"
        }
        if db_nas:
            # Update existing NAS
            freeradius_crud.update_nas(db, nas_id=db_nas.id, nas_update_data=nas_data)
        else:
            # Create new NAS if it didn't exist but now a secret is added
            freeradius_crud.create_nas(db, nas=freeradius_schemas.NasCreate(**nas_data))
    elif "radius_secret" in update_data and final_radius_secret is None:
        # This case handles explicitly removing a secret (setting it to null)
        if db_nas:
            freeradius_crud.delete_nas(db, nas_id=db_nas.id)

    # After handling NAS sync, apply all updates to the router object itself
    for key, value in update_data.items():
        setattr(db_router, key, value)

    db.commit()
    db.refresh(db_router)
    return db_router

def delete_router(db: Session, router_id: int) -> Optional[models.Router]:
    db_router = get_router(db, router_id)
    if db_router:
        # --- Sync to FreeRADIUS nas table ---
        db_nas = freeradius_crud.get_nas_by_shortname(db, shortname=db_router.title)
        if db_nas:
            freeradius_crud.delete_nas(db, nas_id=db_nas.id)

        db.delete(db_router)
        db.commit()
    return db_router
 
# --- IPAM CRUD ---
 
def get_ipv4_network(db: Session, network_id: int) -> Optional[models.IPv4Network]:
    return db.query(models.IPv4Network).filter(models.IPv4Network.id == network_id).first()
 
def get_ipv4_networks(db: Session, skip: int = 0, limit: int = 100) -> List[models.IPv4Network]:
    return db.query(models.IPv4Network).offset(skip).limit(limit).all()
 
def create_ipv4_network(db: Session, network: schemas.IPv4NetworkCreate) -> models.IPv4Network:
    db_network = models.IPv4Network(**network.model_dump())
    db.add(db_network)
    db.commit()
    db.refresh(db_network)
    return db_network
 
def update_ipv4_network(db: Session, network_id: int, network_update: schemas.IPv4NetworkCreate) -> Optional[models.IPv4Network]:
    db_network = get_ipv4_network(db, network_id)
    if db_network:
        update_data = network_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_network, key, value)
        db.commit()
        db.refresh(db_network)
    return db_network
 
def delete_ipv4_network(db: Session, network_id: int) -> Optional[models.IPv4Network]:
    db_network = get_ipv4_network(db, network_id)
    if db_network:
        db.delete(db_network)
        db.commit()
    return db_network
 
def create_ipv4_ip(db: Session, network_id: int, ip_data: schemas.IPv4IPCreate) -> models.IPv4IP:
    db_ip = models.IPv4IP(**ip_data.model_dump(), ipv4_networks_id=network_id)
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip
 
def generate_ipv4_ips(db: Session, network_id: int, ips_to_create: List[str], title: Optional[str], comment: Optional[str]) -> int:
    new_ips = [
        models.IPv4IP(ipv4_networks_id=network_id, ip=ip_str, title=title, comment=comment)
        for ip_str in ips_to_create
    ]
    db.add_all(new_ips)
    db.commit()
    return len(new_ips)
 
def get_ipv6_network(db: Session, network_id: int) -> Optional[models.IPv6Network]:
    return db.query(models.IPv6Network).filter(models.IPv6Network.id == network_id).first()
 
def get_ipv6_networks(db: Session, skip: int = 0, limit: int = 100) -> List[models.IPv6Network]:
    return db.query(models.IPv6Network).offset(skip).limit(limit).all()
 
def create_ipv6_network(db: Session, network: schemas.IPv6NetworkCreate) -> models.IPv6Network:
    db_network = models.IPv6Network(**network.model_dump())
    db.add(db_network)
    db.commit()
    db.refresh(db_network)
    return db_network
 
def update_ipv6_network(db: Session, network_id: int, network_update: schemas.IPv6NetworkCreate) -> Optional[models.IPv6Network]:
    db_network = get_ipv6_network(db, network_id)
    if db_network:
        update_data = network_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_network, key, value)
        db.commit()
        db.refresh(db_network)
    return db_network
 
def delete_ipv6_network(db: Session, network_id: int) -> Optional[models.IPv6Network]:
    db_network = get_ipv6_network(db, network_id)
    if db_network:
        db.delete(db_network)
        db.commit()
    return db_network

def get_invoices_by_date_range(db: Session, start_date: date, end_date: date) -> List[models.Invoice]:
    """
    Return all invoices with date_created between start_date and end_date (inclusive).
    Assumes Invoice model is available as models.Invoice and has a date_created field.
    """
    return db.query(models.Invoice).options(joinedload(models.Invoice.items)).filter(
        models.Invoice.date_created >= start_date,
        models.Invoice.date_created <= end_date
    ).all()

def check_database_health(db: Session) -> bool:
    """
    Checks database connectivity using SQLAlchemy's text() for a simple SELECT 1.
    Returns True if the query succeeds, False otherwise.
    """
    try:
        db.execute(text('SELECT 1'))
        return True
    except Exception:
        return False
