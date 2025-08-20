from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Table,
    Enum,
    BigInteger,
    DECIMAL,
    UniqueConstraint,
    Text
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ARRAY, CITEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# Enums for RBAC
class UserKind(enum.Enum):
    staff = "staff"
    customer = "customer"
    reseller = "reseller"

class RoleScope(enum.Enum):
    system = "system"
    customer = "customer"
    reseller = "reseller"

# New RBAC Schema Tables
class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(CITEXT, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    kind = Column(Enum(UserKind), nullable=False, default=UserKind.staff)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    administrator_profile = relationship("Administrator", back_populates="user", uselist=False, cascade="all, delete-orphan")
    user_profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

class Customer(Base):
    __tablename__ = "customers" # Existing table, adding relationship

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, nullable=False)
    login = Column(CITEXT, unique=True)
    status = Column(String(20), default='active', index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    parent_id = Column(BigInteger, ForeignKey("customers.id"))
    email = Column(CITEXT, index=True)
    billing_email = Column(CITEXT)
    phone = Column(String(50))
    category = Column(String(20), default='person')
    street_1 = Column(String(255))
    zip_code = Column(String(20))
    city = Column(String(100))
    billing_type = Column(String(20), default='recurring')
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user_profiles = relationship("UserProfile", back_populates="customer", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="customer", cascade="all, delete-orphan")
    partner = relationship("Partner", back_populates="customers")
    location = relationship("Location")
    billing_config = relationship("CustomerBilling", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    services = relationship("InternetService", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")

class CustomerBilling(Base):
    __tablename__ = "customer_billing"

    customer_id = Column(BigInteger, ForeignKey("customers.id"), primary_key=True)
    enabled = Column(Boolean, default=True)
    billing_date = Column(Integer, default=1)
    grace_period = Column(Integer, default=3)

    customer = relationship("Customer", back_populates="billing_config")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default='Nigeria')
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    timezone = Column(String(100), default='Africa/Lagos')
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Reseller(Base):
    __tablename__ = "resellers" # Existing table, adding relationship

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # ... other existing columns ...
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Assuming this exists

    user_profiles = relationship("UserProfile", back_populates="reseller")
    user_roles = relationship("UserRole", back_populates="reseller")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id"))
    reseller_id = Column(BigInteger, ForeignKey("resellers.id"))

    user = relationship("User", back_populates="user_profile")
    customer = relationship("Customer", back_populates="user_profiles")
    reseller = relationship("Reseller", back_populates="user_profiles")

class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    scope = Column(Enum(RoleScope), nullable=False, default=RoleScope.system)
    parent_role_id = Column(BigInteger, ForeignKey("roles.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent_role = relationship("Role", remote_side=[id])
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    @hybrid_property
    def permissions(self):
        return [rp.permission for rp in self.role_permissions]

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    module = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    role_permissions = relationship("RolePermission", back_populates="permission")

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(BigInteger, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("permissions.id"), primary_key=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=False)
    customer_id = Column(BigInteger, ForeignKey("customers.id"), nullable=True)
    reseller_id = Column(BigInteger, ForeignKey("resellers.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    customer = relationship("Customer", back_populates="user_roles")
    reseller = relationship("Reseller", back_populates="user_roles")

    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'customer_id', 'reseller_id', name='_user_role_scope_uc'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_type = Column(String(20), nullable=False)
    user_id = Column(Integer)
    user_name = Column(String(255))
    session_id = Column(String(255))
    action = Column(String(100), nullable=False, index=True)
    action_category = Column(String(50))
    table_name = Column(String(100), index=True)
    record_id = Column(Integer, index=True)
    before_values = Column(JSON)
    after_values = Column(JSON)
    changed_fields = Column(JSON)
    ip_address = Column(String(45)) # To support IPv6
    user_agent = Column(String)
    request_url = Column(String)
    request_method = Column(String(10))
    risk_level = Column(String(20), default='low')
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# Existing tables, modified or renamed
# Association Table for Framework Roles and Permissions (renamed)
framework_role_permissions_table = Table('framework_role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('framework_roles.id')),
    Column('permission_id', Integer, ForeignKey('framework_permissions.id'))
)

class FrameworkPermission(Base): # Renamed from Permission
    __tablename__ = "framework_permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True) # Renamed from 'name' to 'code'
    description = Column(String)
    module = Column(String) # Added module field
    is_system = Column(Boolean, default=False) # Added is_system
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    framework_config = Column(JSON, default={})
    ui_customizations = Column(JSON, default={})
    branding_config = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    administrators = relationship("Administrator", back_populates="partner")
    customers = relationship("Customer", back_populates="partner")


class Administrator(Base):
    __tablename__ = "administrators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True) # Link to new User model
    partner_id = Column(Integer, ForeignKey("partners.id"))
    # Removed: login, password_hash, name, email (now in User model)
    phone = Column(String)
    role = Column(String, default="admin") # Keep for backward compatibility, but new RBAC will be primary
    timeout = Column(Integer, default=1200)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    framework_roles = Column(ARRAY(Integer), default=[]) # Keep for backward compatibility
    custom_permissions = Column(JSON, default={})
    ui_preferences = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="administrator_profile")
    partner = relationship("Partner", back_populates="administrators")


class FrameworkConfig(Base):
    __tablename__ = "framework_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, unique=True, nullable=False, index=True)
    config_value = Column(JSON)
    config_type = Column(String, default="json")
    is_system = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FrameworkRole(Base): # Renamed from Role
    __tablename__ = "framework_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String)
    is_system = Column(Boolean, default=False) # Added is_system
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    permissions = relationship(
        "FrameworkPermission",
        secondary=framework_role_permissions_table,
        backref="framework_roles"
    )

# --- Tariffs (Service Plans) ---
class InternetTariff(Base):
    __tablename__ = "internet_tariffs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    price = Column(DECIMAL(10, 4), default=0)
    speed_download = Column(Integer, nullable=False)
    speed_upload = Column(Integer, nullable=False)
    # Simplified for now, can be expanded

# --- Services (Customer Subscriptions) ---
class InternetService(Base):
    __tablename__ = "internet_services"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("internet_tariffs.id"), nullable=False)
    status = Column(String(20), default='active')
    description = Column(Text, nullable=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))
    login = Column(String(255), nullable=False)
    password = Column(String(255))
    ipv4 = Column(String) # Using String for INET for simplicity in this context
    mac = Column(String(100))

    customer = relationship("Customer", back_populates="services")
    tariff = relationship("InternetTariff")

# --- Billing ---
class TransactionCategory(Base):
    __tablename__ = "transaction_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class Tax(Base):
    __tablename__ = "taxes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rate = Column(DECIMAL(5, 4), nullable=False)
    archived = Column(Boolean, default=False)

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    number = Column(String(50), unique=True, nullable=False)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    date_till = Column(DateTime(timezone=True))
    status = Column(String(20), default='not_paid')
    total = Column(DECIMAL(10, 4), default=0)
    due = Column(DECIMAL(10, 4), default=0)

    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(DECIMAL(10, 4), nullable=False)
    tax = Column(DECIMAL(5, 2), default=0)

    invoice = relationship("Invoice", back_populates="items")

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    payment_type_id = Column(Integer, ForeignKey("payment_methods.id"), nullable=False)
    receipt_number = Column(String(100), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    amount = Column(DECIMAL(10, 4), nullable=False)
    comment = Column(Text)

    customer = relationship("Customer", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")
    payment_method = relationship("PaymentMethod")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False) # debit/credit
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    price = Column(DECIMAL(10, 4), nullable=False)
    total = Column(DECIMAL(10, 4), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    category_id = Column(Integer, ForeignKey("transaction_categories.id"), nullable=False)
    description = Column(Text)
    service_id = Column(Integer)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))

    customer = relationship("Customer", back_populates="transactions")
    category = relationship("TransactionCategory")
    invoice = relationship("Invoice")
