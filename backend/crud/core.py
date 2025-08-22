from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, text
import models, schemas, auth_utils
from datetime import date
from typing import Optional, List

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

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

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
    customer_data = customer.model_dump(exclude={"billing_config"})
    db_customer = models.Customer(**customer_data)
    if customer.billing_config:
        db_customer.billing_config = models.CustomerBilling(**customer.billing_config.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.query(models.Customer).options(joinedload(models.Customer.billing_config)).filter(models.Customer.id == customer_id).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None) -> List[models.Customer]:
    query = db.query(models.Customer).options(joinedload(models.Customer.billing_config))
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
        update_data = customer_update.model_dump(exclude_unset=True, exclude={"billing_config"})
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

def get_partners(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Partner).offset(skip).limit(limit).all()

def create_partner(db: Session, partner: schemas.PartnerCreate):
    db_partner = models.Partner(**partner.model_dump())
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

# --- Service CRUD ---
def create_internet_service(db: Session, service: schemas.InternetServiceCreate) -> models.InternetService:
    db_service = models.InternetService(**service.model_dump())
    db.add(db_service)
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
        update_data = service_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_service, key, value)
        db.commit()
        db.refresh(db_service)
    return db_service

def delete_internet_service(db: Session, service_id: int) -> Optional[models.InternetService]:
    db_service = get_internet_service(db, service_id)
    if db_service:
        db.delete(db_service)
        db.commit()
    return db_service

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

def get_invoice(db: Session, invoice_id: int) -> Optional[models.Invoice]:
    return db.query(models.Invoice).options(joinedload(models.Invoice.items)).filter(models.Invoice.id == invoice_id).first()

def get_invoices(db: Session, skip: int = 0, limit: int = 100, customer_id: Optional[int] = None) -> List[models.Invoice]:
    query = db.query(models.Invoice).options(joinedload(models.Invoice.items))
    if customer_id:
        query = query.filter(models.Invoice.customer_id == customer_id)
    return query.order_by(models.Invoice.id.desc()).offset(skip).limit(limit).all()

def get_invoices_count(db: Session, customer_id: Optional[int] = None) -> int:
    query = db.query(models.Invoice)
    if customer_id:
        query = query.filter(models.Invoice.customer_id == customer_id)
    return query.count()

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

def get_payments(db: Session, skip: int = 0, limit: int = 100) -> List[models.Payment]:
    return db.query(models.Payment).offset(skip).limit(limit).all()

def get_payments_count(db: Session) -> int:
    return db.query(models.Payment).count()

def get_payment_methods(db: Session) -> List[models.PaymentMethod]:
    return db.query(models.PaymentMethod).filter(models.PaymentMethod.is_active == True).all()

def get_taxes(db: Session) -> List[models.Tax]:
    return db.query(models.Tax).filter(models.Tax.archived == False).all()


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
    Finds all 'blocked' services for a customer and sets their status to 'active'.
    Returns the number of services updated.
    NOTE: This function does NOT commit the session. The caller is responsible for the commit.
    """
    services_to_update = db.query(models.InternetService).filter(
        models.InternetService.customer_id == customer_id,
        models.InternetService.status == 'blocked'
    )
    
    count = services_to_update.count()
    if count > 0:
        services_to_update.update({"status": "active"}, synchronize_session=False)
    
    return count

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