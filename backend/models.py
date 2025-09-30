from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Time,
    JSON,
    ForeignKey,
    Table,
    Enum,
    BigInteger,
    DECIMAL,
    UniqueConstraint,
    Text,
    text,
    Index
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ARRAY, CITEXT, INET, UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from .database import Base
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

    authored_ticket_messages = relationship("TicketMessage", back_populates="author")
class Customer(Base):
    __tablename__ = "customers"

    id = Column(BigInteger, primary_key=True, index=True)
    login = Column(CITEXT, unique=True, nullable=False)
    password_hash = Column(String(255)) # New: for customer portal login
    status = Column(String(20), default='new', index=True) # new, active, blocked, disabled, etc.
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    parent_id = Column(BigInteger, ForeignKey("customers.id")) # for sub-accounts
    
    name = Column(String(255), nullable=False) # Personal Information
    email = Column(CITEXT, index=True) # Personal Information
    billing_email = Column(CITEXT)
    phone = Column(String(50))
    category = Column(String(20), default='person')
    
    # Address
    street_1 = Column(String(255)) # New
    zip_code = Column(String(20)) # New
    city = Column(String(100)) # New
    subdivision_id = Column(Integer) # New: state/province
    
    # Financial
    billing_type = Column(String(20), default='recurring') # recurring, prepaid_daily, prepaid_monthly
    mrr_total = Column(DECIMAL(10,4), default=0) # New
    daily_prepaid_cost = Column(DECIMAL(10,4), default=0) # New
    
    # Metadata
    gps = Column(String(100)) # New: latitude,longitude
    date_add = Column(DateTime(timezone=True), server_default=func.now()) # New: DATE DEFAULT CURRENT_DATE
    conversion_date = Column(DateTime(timezone=True)) # New
    added_by = Column(String(20), default='admin') # New
    added_by_id = Column(Integer) # New
    last_online = Column(DateTime(timezone=True)) # New
    last_update = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) # New
    
    # Framework Integration
    custom_fields = Column(JSON, default={})
    workflow_state = Column(JSON, default={}) # New
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user_profiles = relationship("UserProfile", back_populates="customer", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="customer", cascade="all, delete-orphan")
    partner = relationship("Partner", back_populates="customers")
    location = relationship("Location")
    billing_config_legacy = relationship("CustomerBilling", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    billing_config = relationship("CustomerBillingConfig", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    services = relationship("InternetService", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    commissions = relationship("ResellerCommission", back_populates="customer")
    customer_labels = relationship("CustomerLabelAssociation", back_populates="customer", cascade="all, delete-orphan") # New
    customer_info = relationship("CustomerInfo", back_populates="customer", uselist=False, cascade="all, delete-orphan") # New
    tickets = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")
    contacts = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan")
    labels = association_proxy("customer_labels", "label")

class CustomerLabel(Base):
    __tablename__ = "customer_labels"
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(255), nullable=False)
    color = Column(String(7), default='#357bf2')
    icon = Column(String(100))
    description = Column(Text)
    custom_properties = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    associations = relationship("CustomerLabelAssociation", back_populates="label")

class CustomerLabelAssociation(Base):
    __tablename__ = "customer_label_associations"
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    label_id = Column(Integer, ForeignKey("customer_labels.id", ondelete="CASCADE"), primary_key=True)

    customer = relationship("Customer", back_populates="customer_labels")
    label = relationship("CustomerLabel", back_populates="associations")

class CustomerInfo(Base):
    __tablename__ = "customer_info"
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    birthday = Column(DateTime(timezone=True)) # DATE in SQL
    passport = Column(String(100))
    company_id = Column(String(100))
    contact_person = Column(String(255))
    vat_id = Column(String(100))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    customer = relationship("Customer", back_populates="customer_info")

class ContactType(Base):
    __tablename__ = "contact_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer_associations = relationship("CustomerContact", back_populates="contact_type")

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))
    position = Column(String(100))
    department = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer_associations = relationship("CustomerContact", back_populates="contact")

class CustomerContact(Base):
    __tablename__ = "customer_contacts"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    contact_type_id = Column(Integer, ForeignKey("contact_types.id"), nullable=False)
    is_primary = Column(Boolean, default=False)
    receives_billing = Column(Boolean, default=False)
    receives_technical = Column(Boolean, default=False)
    receives_marketing = Column(Boolean, default=False)
    receives_outage_notifications = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="contacts")
    contact = relationship("Contact", back_populates="customer_associations")
    contact_type = relationship("ContactType", back_populates="customer_associations")

    __table_args__ = (UniqueConstraint('customer_id', 'contact_id', 'contact_type_id'),)

class CustomerBilling(Base):
    __tablename__ = "customer_billing"

    customer_id = Column(BigInteger, ForeignKey("customers.id"), primary_key=True)
    enabled = Column(Boolean, default=True)
    type = Column(Integer, default=1) # New
    deposit = Column(DECIMAL(10,4), default=0) # New
    billing_date = Column(Integer, default=1)
    billing_due = Column(Integer, server_default=text('14'), nullable=False) # Days after invoice creation it is due
    grace_period = Column(Integer, default=3)
    blocking_period = Column(Integer, default=0) # New
    make_invoices = Column(Boolean, default=True) # New
    payment_method = Column(Integer, default=1) # New
    min_balance = Column(DECIMAL(10,4), default=0) # New
    auto_enable_request = Column(Boolean, default=False) # New
    reminder_enabled = Column(Boolean, default=True) # New
    reminder_day_1 = Column(Integer, default=2) # New
    reminder_day_2 = Column(Integer, default=8) # New
    reminder_day_3 = Column(Integer, default=20) # New
    sub_billing_mode = Column(String(20), default='independent') # New
    send_finance_notification = Column(Boolean, default=True) # New
    partner_percent = Column(DECIMAL(5,4), default=0) # New
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) # New

    customer = relationship("Customer", back_populates="billing_config_legacy")

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

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id"))
    reseller_id = Column(BigInteger, ForeignKey("resellers.id"))

    user = relationship("User", back_populates="user_profile")
    customer = relationship("Customer", back_populates="user_profiles")
    reseller = relationship("Reseller", back_populates="user_profiles")

# =============================================================================
# RESELLER MANAGEMENT SYSTEM
# =============================================================================

class Reseller(Base):
    __tablename__ = "resellers"
    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    parent_reseller_id = Column(Integer, ForeignKey("resellers.id"))
    level = Column(Integer, default=0)
    status = Column(String(20), default='active')
    
    # Contact Information
    contact_person = Column(String(255))
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    
    # Financial Configuration
    default_markup_percent = Column(DECIMAL(5,2), default=0)
    commission_percent = Column(DECIMAL(5,2), default=0)
    credit_limit = Column(DECIMAL(12,4), default=0)
    current_balance = Column(DECIMAL(12,4), default=0)
    payment_terms = Column(Integer, default=30)
    currency = Column(String(3), default='USD')
    
    # Business Configuration
    allowed_services = Column(JSON, default=[])
    max_customers = Column(Integer, default=0)
    can_create_sub_resellers = Column(Boolean, default=False)
    white_label_enabled = Column(Boolean, default=False)
    
    # Branding
    logo_url = Column(String(500))
    brand_name = Column(String(255))
    support_email = Column(String(255))
    support_phone = Column(String(50))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user_profiles = relationship("UserProfile", back_populates="reseller")
    user_roles = relationship("UserRole", back_populates="reseller")
    parent_reseller = relationship("Reseller", remote_side=[id], backref="sub_resellers")
    customers = relationship("ResellerCustomer", back_populates="reseller", cascade="all, delete-orphan")
    commissions = relationship("ResellerCommission", back_populates="reseller", cascade="all, delete-orphan")
    pricing_rules = relationship("ResellerPricing", back_populates="reseller", cascade="all, delete-orphan")
    portal_users = relationship("ResellerUser", back_populates="reseller", cascade="all, delete-orphan")

class ResellerCustomer(Base):
    __tablename__ = "reseller_customers"
    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(Integer, ForeignKey("resellers.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True)
    assigned_date = Column(Date, server_default=func.current_date())
    commission_rate = Column(DECIMAL(5,2))
    markup_rate = Column(DECIMAL(5,2))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reseller = relationship("Reseller", back_populates="customers")
    customer = relationship("Customer")

class ResellerCommission(Base):
    __tablename__ = "reseller_commissions"
    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(Integer, ForeignKey("resellers.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    payment_id = Column(Integer, ForeignKey("payments.id"))
    commission_type = Column(String(50), nullable=False)
    base_amount = Column(DECIMAL(12,4), nullable=False)
    commission_rate = Column(DECIMAL(5,2), nullable=False)
    commission_amount = Column(DECIMAL(12,4), nullable=False)
    period_start = Column(Date)
    period_end = Column(Date)
    status = Column(String(20), default='pending')
    paid_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    reseller = relationship("Reseller", back_populates="commissions")
    customer = relationship("Customer")
    invoice = relationship("Invoice")
    payment = relationship("Payment", back_populates="commissions")

class ResellerPricing(Base):
    __tablename__ = "reseller_pricing"
    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(Integer, ForeignKey("resellers.id", ondelete="CASCADE"), nullable=False)
    service_type = Column(String(50), nullable=False)
    tariff_id = Column(Integer, nullable=False)
    markup_type = Column(String(20), default='percent')
    markup_value = Column(DECIMAL(10,4), nullable=False)
    min_price = Column(DECIMAL(10,4))
    max_price = Column(DECIMAL(10,4))
    effective_from = Column(Date, server_default=func.current_date())
    effective_to = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    reseller = relationship("Reseller", back_populates="pricing_rules")

class ResellerUser(Base):
    __tablename__ = "reseller_users"
    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(Integer, ForeignKey("resellers.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50))
    status = Column(String(20), default='active')
    role = Column(String(50), default='user')
    last_login = Column(DateTime(timezone=True))
    created_by = Column(Integer, ForeignKey("reseller_users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    reseller = relationship("Reseller", back_populates="portal_users")
    creator = relationship("ResellerUser", remote_side=[id])

class Role(Base):
    __tablename__ = "roles"

    # ResellerUser: Comprehensive fields from previous context
    password_salt = Column(String(255))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime(timezone=True))
    
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    email_verification_expires = Column(DateTime(timezone=True))
    
    permissions = Column(JSON, default=[]) # Specific permissions array
    allowed_customer_ids = Column(ARRAY(Integer), default=[]) # Restrict to specific customers
    ip_whitelist = Column(ARRAY(INET), default=[]) # IP restrictions
    
    last_login_ip = Column(INET)
    current_session_id = Column(String(255))
    session_expires = Column(DateTime(timezone=True))
    concurrent_sessions_allowed = Column(Integer, default=1)
    
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    force_password_change = Column(Boolean, default=False)
    
    timezone = Column(String(100), default='UTC')
    language = Column(String(10), default='en')
    date_format = Column(String(20), default='YYYY-MM-DD')
    notifications_enabled = Column(Boolean, default=True)

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
    business_context = Column(String(255))
    risk_level = Column(String(20), default='low')
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


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


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String(50), default="new")
    converted_to_opportunity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    customer_id = Column(BigInteger, ForeignKey("customers.id"), nullable=True)
    amount = Column(DECIMAL(10, 2))
    stage = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead")

class Administrator(Base):
    __tablename__ = "administrators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True) # Link to new User model
    partner_id = Column(Integer, ForeignKey("partners.id"))
    phone = Column(String)
    timeout = Column(Integer, default=1200)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    custom_permissions = Column(JSON, default={})
    ui_preferences = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="administrator_profile")
    partner = relationship("Partner", back_populates="administrators")
    assigned_tickets = relationship("Ticket", back_populates="assignee", foreign_keys="Ticket.assign_to")


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

# --- Billing ---
class TransactionCategory(Base):
    __tablename__ = "transaction_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_base = Column(Boolean, default=False)
    category_config = Column(JSON, default={})
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Tax(Base):
    __tablename__ = "taxes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rate = Column(DECIMAL(5, 4), nullable=False)
    type = Column(String(20), default='percentage')  # percentage, fixed_amount, compound, exempted
    archived = Column(Boolean, server_default=text('false'), nullable=False)
    
    # Multi-jurisdiction support
    applicable_locations = Column(ARRAY(Integer))
    jurisdiction_code = Column(String(10))  # Tax jurisdiction code
    tax_authority = Column(String(255))  # Tax collecting authority
    
    # Advanced tax configuration
    calculation_rules = Column(JSON, default={})
    minimum_taxable_amount = Column(DECIMAL(10, 4), default=0)
    maximum_tax_amount = Column(DECIMAL(10, 4))  # Optional cap on tax amount
    
    # Tax periods and validity
    effective_date = Column(Date)
    expiry_date = Column(Date)
    
    # Service type applicability
    applicable_service_types = Column(ARRAY(String))  # internet, voice, recurring, bundle
    exempt_service_types = Column(ARRAY(String))
    
    # Customer category applicability
    applicable_customer_categories = Column(ARRAY(String))
    exempt_customer_categories = Column(ARRAY(String))
    
    # Compound tax configuration
    compound_with_tax_ids = Column(ARRAY(Integer))  # Other tax IDs to compound with
    compound_order = Column(Integer, default=1)  # Order of tax calculation
    
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    number = Column(String(50), unique=True, nullable=False)
    date_created = Column(Date, nullable=False, server_default=func.current_date())
    date_updated = Column(Date, onupdate=func.current_date())
    date_till = Column(Date)
    date_payment = Column(Date)
    note = Column(Text)
    memo = Column(Text)
    status = Column(String(20), default='not_paid', index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"))
    total = Column(DECIMAL(10, 4), default=0)
    due = Column(DECIMAL(10, 4), default=0)
    real_create_datetime = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(String(20), default='admin')
    added_by_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", foreign_keys="Payment.invoice_id")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(DECIMAL(10, 4), nullable=False)
    tax = Column(DECIMAL(5, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("Invoice", back_populates="items")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    price = Column(DECIMAL(10,4), nullable=False)
    total = Column(DECIMAL(10,4), nullable=False)
    date = Column(Date, nullable=False)
    category_id = Column("category", Integer, ForeignKey("transaction_categories.id"), nullable=False)
    description = Column(Text)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="transactions")
    category = relationship("TransactionCategory")
    payment = relationship("Payment", back_populates="transaction")

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    name_1 = Column(String(255))
    name_2 = Column(String(255))
    name_3 = Column(String(255))
    name_4 = Column(String(255))
    name_5 = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payments = relationship("Payment", back_populates="payment_method_rel")

class PaymentGateway(Base):
    __tablename__ = "payment_gateways"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    api_key = Column(String(255), nullable=False)
    api_secret = Column(String(255), nullable=False)
    config = Column(JSON, default={})
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id"))
    request_id = Column(Integer) # proforma invoice
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    payment_statement_id = Column(Integer)
    payment_type_id = Column("payment_type", Integer, ForeignKey("payment_methods.id"), nullable=False)
    receipt_number = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(DECIMAL(10,4), nullable=False)
    comment = Column(Text)
    is_sent = Column(Boolean, default=False)
    field_1 = Column(Text) # Custom fields for payment method
    field_2 = Column(Text)
    field_3 = Column(Text)
    field_4 = Column(Text)
    field_5 = Column(Text)
    note = Column(Text)
    memo = Column(Text)
    remind_amount = Column(DECIMAL(10,4), default=0)
    real_create_datetime = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(String(20), default='admin')
    added_by_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="payments")
    payment_method_rel = relationship("PaymentMethod", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments", foreign_keys=[invoice_id])
    credit_note = relationship(
        "CreditNote",
        back_populates="payment",
        uselist=False,
        primaryjoin="Payment.id == foreign(CreditNote.payment_id)",
    )
    transaction = relationship("Transaction", back_populates="payment", uselist=False)
    commissions = relationship("ResellerCommission", back_populates="payment")
    proforma_invoice = relationship("ProformaInvoice", back_populates="payment", uselist=False)

# --- Tariffs (Service Plans) ---
class InternetTariff(Base):
    __tablename__ = "internet_tariffs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    service_name = Column(String, unique=True)
    partners_ids = Column(ARRAY(Integer), nullable=False)
    price = Column(DECIMAL(10, 4), default=0)
    
    # Speed Configuration
    speed_download = Column(Integer, nullable=False)
    speed_upload = Column(Integer, nullable=False)
    speed_limit_at = Column(Integer, default=10)
    aggregation = Column(Integer, default=1)
    
    # Burst Configuration
    burst_limit = Column(Integer, default=0)
    burst_limit_fixed_down = Column(Integer, default=0)
    burst_limit_fixed_up = Column(Integer, default=0)
    burst_threshold = Column(Integer, default=0)
    burst_threshold_fixed_down = Column(Integer, default=0)
    burst_threshold_fixed_up = Column(Integer, default=0)
    burst_time = Column(Integer, default=0)
    burst_type = Column(String(20), default='none')
    
    # Speed Limit Configuration
    speed_limit_type = Column(String(20), default='none')
    speed_limit_fixed_down = Column(Integer, default=0)
    speed_limit_fixed_up = Column(Integer, default=0)
    
    # Billing Configuration
    billing_types = Column(ARRAY(String))
    billing_days_count = Column(Integer, default=1)
    custom_period = Column(Boolean, default=False)
    
    # Availability
    customer_categories = Column(ARRAY(String))
    available_for_services = Column(Boolean, default=True)
    available_for_locations = Column(ARRAY(Integer))
    hide_on_admin_portal = Column(Boolean, default=False)
    show_on_customer_portal = Column(Boolean, default=False)
    priority = Column(String(20), default='normal')
    
    # Financial
    tax_id = Column(Integer, ForeignKey("taxes.id"))
    transaction_category_id = Column(Integer, ForeignKey("transaction_categories.id"))
    
    # Framework Integration
    pricing_rules = Column(JSON, default={})
    service_rules = Column(JSON, default={})
    custom_fields = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tax = relationship("Tax")
    transaction_category = relationship("TransactionCategory")

class VoiceTariff(Base):
    __tablename__ = "voice_tariffs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    service_name = Column(String, unique=True)
    type = Column(String(20), default='voip')
    partners_ids = Column(ARRAY(Integer), nullable=False)
    price = Column(DECIMAL(10, 4), default=0)
    billing_types = Column(ARRAY(String))
    billing_days_count = Column(Integer, default=1)
    custom_period = Column(Boolean, default=False)
    customer_categories = Column(ARRAY(String))
    available_for_services = Column(Boolean, default=True)
    available_for_locations = Column(ARRAY(Integer))
    hide_on_admin_portal = Column(Boolean, default=False)
    show_on_customer_portal = Column(Boolean, default=False)
    tax_id = Column(Integer, ForeignKey("taxes.id"))
    transaction_category_id = Column(Integer, ForeignKey("transaction_categories.id"))
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RecurringTariff(Base):
    __tablename__ = "recurring_tariffs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    service_name = Column(String, unique=True)
    partners_ids = Column(ARRAY(Integer), nullable=False)
    price = Column(DECIMAL(10, 4), default=0)
    billing_types = Column(ARRAY(String))
    billing_days_count = Column(Integer, default=1)
    custom_period = Column(Boolean, default=False)
    customer_categories = Column(ARRAY(String))
    available_for_services = Column(Boolean, default=True)
    available_for_locations = Column(ARRAY(Integer))
    hide_on_admin_portal = Column(Boolean, default=False)
    show_on_customer_portal = Column(Boolean, default=False)
    tax_id = Column(Integer, ForeignKey("taxes.id"))
    transaction_category_id = Column(Integer, ForeignKey("transaction_categories.id"))
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class OneTimeTariff(Base):
    __tablename__ = "one_time_tariffs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    service_description = Column(Text)
    price = Column(DECIMAL(10, 4), default=0)
    partners_ids = Column(ARRAY(Integer), nullable=False)
    customer_categories = Column(ARRAY(String))
    available_for_locations = Column(ARRAY(Integer))
    enabled = Column(Boolean, default=True)
    hide_on_admin_portal = Column(Boolean, default=False)
    show_on_customer_portal = Column(Boolean, default=False)
    tax_id = Column(Integer, ForeignKey("taxes.id"))
    transaction_category_id = Column(Integer, ForeignKey("transaction_categories.id"))
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BundleTariff(Base):
    __tablename__ = "bundle_tariffs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    service_description = Column(Text)
    partners_ids = Column(ARRAY(Integer), nullable=False)
    price = Column(DECIMAL(10, 4), default=0)
    activation_fee = Column(DECIMAL(10, 4), default=0)
    cancellation_fee = Column(DECIMAL(10, 4), default=0)
    prior_cancellation_fee = Column(DECIMAL(10, 4), default=0)
    change_to_other_bundle_fee = Column(DECIMAL(10, 4), default=0)
    contract_duration = Column(Integer, default=0)
    get_activation_fee_when = Column(String(30), default='create_service')
    automatic_renewal = Column(Boolean, default=False)
    auto_reactivate = Column(Boolean, default=False)
    issue_invoice_while_service_creation = Column(Boolean, default=False)
    discount_period = Column(Integer, default=0)
    discount_type = Column(String(20), default='percent')
    discount_value = Column(DECIMAL(10, 4), default=0)
    internet_tariffs = Column(ARRAY(Integer))
    voice_tariffs = Column(ARRAY(Integer))
    custom_tariffs = Column(ARRAY(Integer))
    billing_types = Column(ARRAY(String))
    billing_days_count = Column(Integer, default=1)
    custom_period = Column(Boolean, default=False)
    available_for_services = Column(Boolean, default=True)
    hide_on_admin_portal = Column(Boolean, default=False)
    show_on_customer_portal = Column(Boolean, default=False)
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# --- Services (Customer Subscriptions) ---
class InternetService(Base):
    __tablename__ = "internet_services"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("internet_tariffs.id"), nullable=False)
    status = Column(String(20), default='active') # active, stopped, disabled, hidden, pending, terminated
    description = Column(Text, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(DECIMAL(10, 4))
    
    # Service Dates
    # Service Dates
    start_date = Column(Date, nullable=False, server_default=func.now())
    end_date = Column(Date, server_default=text("'9999-12-31'"))
    
    # Discount
    discount = Column(DECIMAL(10, 4), default=0)
    discount_type = Column(String(20), default='percent')
    discount_value = Column(DECIMAL(10, 4), default=0)
    discount_start_date = Column(Date)
    discount_end_date = Column(Date)
    discount_text = Column(Text)
    
    # Network Configuration
    router_id = Column(Integer, ForeignKey("routers.id"))
    sector_id = Column(Integer)
    login = Column(String(255), nullable=False)
    password = Column(String(255))
    taking_ipv4 = Column(Integer, default=0)
    ipv4 = Column(INET)
    ipv4_route = Column(String(100))
    ipv4_pool_id = Column(Integer)
    ipv6 = Column(INET)
    ipv6_delegated = Column(String(100))
    ipv6_pool_id = Column(Integer)
    mac = Column(String(100))
    port_id = Column(Integer)
    
    # Relationships
    bundle_service_id = Column(Integer, default=0)
    parent_id = Column(Integer, default=0)
    access_device = Column(Integer, default=0)
    
    # Configuration
    on_approve = Column(Boolean, default=False)
    period = Column(Integer, default=-1)
    status_new = Column(String(20), default='')
    top_up_tariff_id = Column(Integer, default=0)
    
    # Framework Integration
    service_rules = Column(JSON, default={})
    custom_fields = Column(JSON, default={})
    workflow_state = Column(JSON, default={})
    automation_config = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="services")
    tariff = relationship("InternetTariff")

class VoiceService(Base):
    __tablename__ = "voice_services"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("voice_tariffs.id"), nullable=False)
    status = Column(String(20), default='active')
    description = Column(Text, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(DECIMAL(10, 4))
    start_date = Column(Date, nullable=False, server_default=func.now())
    end_date = Column(Date, server_default=text("'9999-12-31'"))
    discount = Column(DECIMAL(10, 4), default=0)
    discount_type = Column(String(20), default='percent')
    discount_value = Column(DECIMAL(10, 4), default=0)
    discount_start_date = Column(Date)
    discount_end_date = Column(Date)
    discount_text = Column(Text)
    voice_device_id = Column(Integer)
    phone = Column(String(50), nullable=False)
    direction = Column(String(20), default='outgoing')
    bundle_service_id = Column(Integer, default=0)
    parent_id = Column(Integer, default=0)
    on_approve = Column(Boolean, default=False)
    period = Column(Integer, default=-1)
    status_new = Column(String(20), default='')
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")
    tariff = relationship("VoiceTariff")

class RecurringService(Base):
    __tablename__ = "recurring_services"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("recurring_tariffs.id"), nullable=False)
    status = Column(String(20), default='active')
    description = Column(Text, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(DECIMAL(10, 4))
    start_date = Column(Date, nullable=False, server_default=func.now())
    end_date = Column(Date, server_default=text("'9999-12-31'"))
    discount = Column(DECIMAL(10, 4), default=0)
    discount_type = Column(String(20), default='percent')
    discount_value = Column(DECIMAL(10, 4), default=0)
    discount_start_date = Column(Date)
    discount_end_date = Column(Date)
    discount_text = Column(Text)
    bundle_service_id = Column(Integer, default=0)
    parent_id = Column(Integer, default=0)
    on_approve = Column(Boolean, default=False)
    period = Column(Integer, default=-1)
    status_new = Column(String(20), default='')
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")
    tariff = relationship("RecurringTariff")

class BundleService(Base):
    __tablename__ = "bundle_services"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    bundle_id = Column(Integer, ForeignKey("bundle_tariffs.id"), nullable=False)
    status = Column(String(20), default='active')
    description = Column(Text, nullable=False)
    unit_price = Column(DECIMAL(10, 4))
    start_date = Column(Date, nullable=False, server_default=func.now())
    end_date = Column(Date, server_default=text("'9999-12-31'"))
    discount = Column(DECIMAL(10, 4), default=0)
    discount_type = Column(String(20), default='percent')
    discount_value = Column(DECIMAL(10, 4), default=0)
    discount_start_date = Column(Date)
    discount_end_date = Column(Date)
    discount_text = Column(Text)
    automatic_renewal = Column(Boolean, default=False)
    activation_fee = Column(DECIMAL(10, 4), default=0)
    auto_reactivate = Column(Boolean, default=False)
    get_activation_fee_when = Column(String(30), default='create_service')
    issue_invoice_while_service_creation = Column(Boolean, default=False)
    cancellation_fee = Column(DECIMAL(10, 4), default=0)
    prior_cancellation_fee = Column(DECIMAL(10, 4), default=0)
    activation_fee_transaction_id = Column(Integer)
    cancellation_fee_transaction_id = Column(Integer)
    prior_cancellation_fee_transaction_id = Column(Integer)
    custom_fields = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")
    bundle = relationship("BundleTariff")

# =============================================================================
# USAGE & FUP (FAIR USAGE POLICY)
# =============================================================================

class FUPPolicy(Base):
    __tablename__ = "fup_policies"
    id = Column(Integer, primary_key=True, index=True)
    tariff_id = Column(Integer, ForeignKey("internet_tariffs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    fixed_up = Column(BigInteger, default=0)
    fixed_down = Column(BigInteger, default=0)
    accounting_traffic = Column(Boolean, default=False)
    accounting_online = Column(Boolean, default=False)
    action = Column(String(20), default='block')
    percent = Column(Integer, default=0)
    conditions = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tariff = relationship("InternetTariff")

class CapTariff(Base):
    __tablename__ = "cap_tariffs"
    id = Column(Integer, primary_key=True, index=True)
    tariff_id = Column(Integer, ForeignKey("internet_tariffs.id"))
    title = Column(String(255), nullable=False)
    amount = Column(DECIMAL(10, 4), nullable=False)
    amount_in = Column(String(10), default='mb')
    price = Column(DECIMAL(10, 4), default=0)
    type = Column(String(20), default='manual')
    validity = Column(String(50), nullable=False)
    to_invoice = Column(Boolean, default=False)
    transaction_category_id = Column(Integer, ForeignKey("transaction_categories.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tariff = relationship("InternetTariff")
    transaction_category = relationship("TransactionCategory")

class FUPLimit(Base):
    __tablename__ = "fup_limits"
    tariff_id = Column(Integer, ForeignKey("internet_tariffs.id"), primary_key=True)
    cap_tariff_id = Column(Integer, ForeignKey("cap_tariffs.id"))
    traffic_from = Column(Time, server_default=text("'00:00:00'"))
    online_from = Column(Time, server_default=text("'00:00:00'"))
    traffic_to = Column(Time, server_default=text("'24:00:00'"))
    online_to = Column(Time, server_default=text("'24:00:00'"))
    traffic_days = Column(ARRAY(Integer), server_default='{1,2,3,4,5,6,7}')
    online_days = Column(ARRAY(Integer), server_default='{1,2,3,4,5,6,7}')
    action = Column(String(20), default='block')
    percent = Column(Integer, default=0)
    traffic_amount = Column(BigInteger, default=0)
    traffic_direction = Column(String(20), default='up_down')
    traffic_in = Column(String(10), default='gb')
    override_traffic = Column(Boolean, default=False)
    online_amount = Column(Integer, default=0)
    online_in = Column(String(20), default='hours')
    override_online = Column(Boolean, default=False)
    rollover_data = Column(Boolean, default=False)
    rollover_time = Column(Boolean, default=False)
    bonus_is_unlimited = Column(Boolean, default=True)
    bonus_traffic = Column(DECIMAL(10, 4), default=0)
    bonus_traffic_in = Column(String(10))
    fixed_up = Column(BigInteger, default=0)
    fixed_down = Column(BigInteger, default=0)
    top_up_over_usage = Column(Boolean, default=False)
    top_up_trigger_percent = Column(Integer, default=0)
    use_bonus_when_normal_ended = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tariff = relationship("InternetTariff", backref="fup_limit", uselist=False)
    cap_tariff = relationship("CapTariff")

class FUPCounter(Base):
    __tablename__ = "fup_counters"
    service_id = Column(Integer, ForeignKey("internet_services.id", ondelete="CASCADE"), primary_key=True)
    day_up = Column(BigInteger, default=0)
    day_down = Column(BigInteger, default=0)
    day_time = Column(Integer, default=0)
    day_bonus_up = Column(BigInteger, default=0)
    day_bonus_down = Column(BigInteger, default=0)
    week_up = Column(BigInteger, default=0)
    week_down = Column(BigInteger, default=0)
    week_bonus_up = Column(BigInteger, default=0)
    week_bonus_down = Column(BigInteger, default=0)
    week_time = Column(Integer, default=0)
    month_up = Column(BigInteger, default=0)
    month_down = Column(BigInteger, default=0)
    month_bonus_up = Column(BigInteger, default=0)
    month_bonus_down = Column(BigInteger, default=0)
    month_time = Column(Integer, default=0)
    cap_amount = Column(BigInteger, default=0)
    cap_used = Column(BigInteger, default=0)
    over_usage = Column(BigInteger, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    service = relationship("InternetService", backref="fup_counter", uselist=False)

class CappedData(Base):
    __tablename__ = "capped_data"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("internet_services.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(BigInteger, default=0)
    quantity_remind = Column(BigInteger, default=0)
    tariff_id = Column(Integer, ForeignKey("cap_tariffs.id"))
    over_usage = Column(BigInteger, default=0)
    valid_till = Column(DateTime(timezone=True))
    end_of_period = Column(DateTime(timezone=True))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    price = Column(DECIMAL(10, 4), default=0)
    added_by = Column(String(20), default='system')
    type = Column(String(50), default='admin_top_up')
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    service = relationship("InternetService", backref="capped_data")
    cap_tariff = relationship("CapTariff")
    transaction = relationship("Transaction")

class CustomerTrafficCounter(Base):
    __tablename__ = "customer_traffic_counters"
    service_id = Column(Integer, ForeignKey("internet_services.id", ondelete="CASCADE"), primary_key=True)
    date = Column(Date, primary_key=True)
    up = Column(BigInteger, default=0)
    down = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    service = relationship("InternetService")

class CustomerBonusTrafficCounter(Base):
    __tablename__ = "customer_bonus_traffic_counters"
    service_id = Column(Integer, ForeignKey("internet_services.id", ondelete="CASCADE"), primary_key=True)
    date = Column(Date, primary_key=True)
    up = Column(BigInteger, default=0)
    down = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    service = relationship("InternetService")

class CreditNote(Base):
    __tablename__ = "credit_notes"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    number = Column(String(50), unique=True, nullable=False)
    date_created = Column(Date, nullable=False, server_default=func.current_date())
    date_updated = Column(Date, onupdate=func.current_date())
    date_payment = Column(Date)
    status = Column(String(20), default='not_refunded')
    payment_id = Column(Integer, ForeignKey("payments.id"))
    note = Column(Text)
    is_sent = Column(Boolean, default=False)
    total = Column(DECIMAL(10, 4), default=0)
    remind_amount = Column(DECIMAL(10, 4), default=0)
    real_create_datetime = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(String(20), default='system')
    added_by_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # This line was missing in the original diff, but present in the original file.

    customer = relationship("Customer")
    items = relationship("CreditNoteItem", back_populates="credit_note", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="credit_note", foreign_keys=[payment_id], uselist=False, remote_side=[Payment.id])

class CreditNoteItem(Base):
    __tablename__ = "credit_note_items"
    id = Column(Integer, primary_key=True, index=True)
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, default=1)
    unit = Column(Integer)
    price = Column(DECIMAL(10, 4), nullable=False)
    tax = Column(DECIMAL(5, 2), default=0)
    sub_account_id = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    credit_note = relationship("CreditNote", back_populates="items")

# Enhanced Billing Configuration and Scheduling
class BillingCycle(Base):
    __tablename__ = "billing_cycles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    cycle_type = Column(String(20), nullable=False)  # monthly, quarterly, semi_annual, annual, custom
    frequency_days = Column(Integer)  # For custom cycles
    
    # Billing day configuration
    billing_day_type = Column(String(20), default='fixed')  # fixed, end_of_month, custom
    billing_day = Column(Integer)  # Day of month for billing (1-31)
    
    # Pro-rating configuration
    prorate_first_bill = Column(Boolean, default=True)
    prorate_last_bill = Column(Boolean, default=True)
    proration_method = Column(String(20), default='daily')  # daily, monthly
    
    # Due date configuration
    payment_terms_days = Column(Integer, default=14)
    due_date_type = Column(String(20), default='fixed')  # fixed, end_of_month
    
    # Grace period and late fees
    grace_period_days = Column(Integer, default=0)
    late_fee_type = Column(String(20))  # percentage, fixed, none
    late_fee_amount = Column(DECIMAL(10, 4), default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CustomerBillingConfig(Base):
    __tablename__ = "customer_billing_configs"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, unique=True)
    billing_cycle_id = Column(Integer, ForeignKey("billing_cycles.id"), nullable=False)
    
    # Custom billing day override
    custom_billing_day = Column(Integer)  # Override the default billing cycle day
    
    # Invoice preferences
    invoice_delivery_method = Column(String(20), default='email')  # email, postal, portal
    invoice_format = Column(String(20), default='pdf')  # pdf, html
    currency = Column(String(3), default='USD')
    
    # Payment preferences
    preferred_payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    auto_payment_enabled = Column(Boolean, default=False)
    
    # Credit and collections
    credit_limit = Column(DECIMAL(12, 4), default=0)
    dunning_enabled = Column(Boolean, default=True)
    
    # Taxation
    tax_exempt = Column(Boolean, default=False)
    tax_exempt_reason = Column(String(255))
    tax_exempt_certificate = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    customer = relationship("Customer", back_populates="billing_config")
    billing_cycle = relationship("BillingCycle")
    preferred_payment_method = relationship("PaymentMethod")

class BillingEvent(Base):
    __tablename__ = "billing_events"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # invoice_generated, payment_received, etc.
    event_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Related entities
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    payment_id = Column(Integer, ForeignKey("payments.id"))
    
    # Event details
    amount = Column(DECIMAL(12, 4))
    description = Column(Text)
    event_metadata = Column(JSON, default={})  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    
    # Processing status
    status = Column(String(20), default='processed')  # processed, failed, pending
    error_message = Column(Text)
    
    created_by = Column(String(50), default='system')  # system, admin, api
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    customer = relationship("Customer")
    invoice = relationship("Invoice")
    payment = relationship("Payment")

class UsageTracking(Base):
    __tablename__ = "usage_tracking"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_type = Column(String(20), nullable=False)  # internet, voice, data
    service_id = Column(Integer, nullable=False)  # ID of the specific service
    
    # Usage metrics
    usage_date = Column(Date, nullable=False)
    usage_type = Column(String(20), nullable=False)  # data_transfer, call_minutes, sms_count
    usage_amount = Column(DECIMAL(15, 6), nullable=False)
    usage_unit = Column(String(10), nullable=False)  # MB, GB, minutes, count
    
    # Billing relevance
    billable = Column(Boolean, default=True)
    rate_per_unit = Column(DECIMAL(10, 6))
    billing_period = Column(String(7))  # YYYY-MM format
    
    # Geographic and technical details
    location_id = Column(Integer, ForeignKey("locations.id"))
    device_info = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    customer = relationship("Customer")
    
    # Composite index for efficient querying
    __table_args__ = (
        Index('idx_usage_customer_date', 'customer_id', 'usage_date'),
        Index('idx_usage_service', 'service_type', 'service_id'),
        Index('idx_usage_billing_period', 'billing_period'),
    )

class ProformaInvoice(Base):
    __tablename__ = "proforma_invoices"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    number = Column(String(50), unique=True, nullable=False)
    date_created = Column(Date, nullable=False, server_default=func.current_date())
    date_updated = Column(Date, onupdate=func.current_date())
    date_till = Column(Date)
    date_payment = Column(Date)
    status = Column(String(20), default='not_paid')
    payment_id = Column(Integer, ForeignKey("payments.id"))
    total = Column(DECIMAL(10, 4), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")
    items = relationship("ProformaInvoiceItem", back_populates="proforma_invoice", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="proforma_invoice", foreign_keys=[payment_id], uselist=False, remote_side=[Payment.id])

class ProformaInvoiceItem(Base):
    __tablename__ = "proforma_invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    proforma_invoice_id = Column(Integer, ForeignKey("proforma_invoices.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, default=1)
    unit = Column(Integer)
    price = Column(DECIMAL(10, 4), nullable=False)
    tax = Column(DECIMAL(5, 2), default=0)
    period_from = Column(Date)
    period_to = Column(Date)
    sub_account_id = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    proforma_invoice = relationship("ProformaInvoice", back_populates="items")

class AdditionalDiscount(Base):
    __tablename__ = "additional_discounts"
    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(String(20), nullable=False)
    service_id = Column(Integer, nullable=False)
    enabled = Column(Boolean, default=True)
    percent = Column(DECIMAL(5, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# =============================================================================
# INTEGRATED SUPPORT SYSTEM
# =============================================================================

class TicketStatus(Base):
    __tablename__ = "ticket_statuses"
    id = Column(Integer, primary_key=True, index=True)
    title_for_agent = Column(String(255), nullable=False)
    title_for_customer = Column(String(255), nullable=False)
    label = Column(String(50), default='default') # For UI coloring (e.g., primary, success, warning)
    mark = Column(ARRAY(String), default=['open', 'unresolved']) # open, unresolved, closed
    icon = Column(String(50), default='fa-tasks')
    view_on_dashboard = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TicketGroup(Base):
    __tablename__ = "ticket_groups"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TicketType(Base):
    __tablename__ = "ticket_types"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, unique=True)
    background_color = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    reporter_user_id = Column(BigInteger, ForeignKey("users.id")) # Can be admin user or customer user
    assign_to = Column(Integer, ForeignKey("administrators.id")) # admin ID
    status_id = Column(Integer, ForeignKey("ticket_statuses.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("ticket_groups.id"))
    type_id = Column(Integer, ForeignKey("ticket_types.id"))
    subject = Column(Text, nullable=False)
    priority = Column(String(20), default='medium') # low, medium, high, urgent
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="tickets")
    reporter = relationship("User")
    status = relationship("TicketStatus")
    group = relationship("TicketGroup")
    ticket_type = relationship("TicketType")
    assignee = relationship("Administrator", back_populates="assigned_tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    author_user_id = Column(BigInteger, ForeignKey("users.id")) # Author if admin or customer user
    message = Column(Text, nullable=False)
    is_internal_note = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="messages")
    attachments = relationship("TicketAttachment", back_populates="message", cascade="all, delete-orphan")
    author = relationship("User", back_populates="authored_ticket_messages")

# =============================================================================
# ACCOUNTING SYSTEM
# =============================================================================

class AccountingCategory(Base):
    __tablename__ = "accounting_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("accounting_categories.id"))
    type = Column(String(50), nullable=False) # income, expense, asset, liability, equity
    code = Column(String(50), unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent = relationship("AccountingCategory", remote_side=[id], backref="children")

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    reference_type = Column(String(50)) # invoice, payment, adjustment, etc.
    reference_id = Column(Integer)
    status = Column(String(20), default='posted') # draft, posted, voided
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    created_by_admin = relationship("Administrator")
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")

class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"
    id = Column(Integer, primary_key=True, index=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_category_id = Column(Integer, ForeignKey("accounting_categories.id"), nullable=False)
    debit = Column(DECIMAL(12,4), default=0)
    credit = Column(DECIMAL(12,4), default=0)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    journal_entry = relationship("JournalEntry", back_populates="lines")
    account_category = relationship("AccountingCategory")

# =============================================================================
# VOICE CDR SYSTEM
# =============================================================================

class VoiceCDR(Base):
    __tablename__ = "voice_cdr"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    service_id = Column(Integer, ForeignKey("voice_services.id"))
    call_date = Column(DateTime(timezone=True), nullable=False)
    call_type = Column(String(20), nullable=False) # inbound, outbound, internal
    source = Column(String(50), nullable=False)
    destination = Column(String(50), nullable=False)
    duration = Column(Integer, nullable=False) # seconds
    billable_duration = Column(Integer, nullable=False) # seconds
    cost = Column(DECIMAL(10,4), default=0)
    rate_per_minute = Column(DECIMAL(10,4), default=0)
    destination_type = Column(String(50)) # local, national, international, mobile
    termination_cause = Column(String(100))
    quality_score = Column(DECIMAL(3,2)) # 0.00 to 5.00
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer")
    service = relationship("VoiceService")

class VoiceCDRSummary(Base):
    __tablename__ = "voice_cdr_summary"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("voice_services.id"))
    summary_date = Column(Date, nullable=False)
    total_calls = Column(Integer, default=0)
    total_duration = Column(Integer, default=0) # seconds
    total_cost = Column(DECIMAL(10,4), default=0)
    inbound_calls = Column(Integer, default=0)
    outbound_calls = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint('customer_id', 'service_id', 'summary_date'),)
    customer = relationship("Customer")

# =============================================================================
# TICKET ATTACHMENTS
# =============================================================================

class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("ticket_messages.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), default='ticket_attachment')
    filename_original = Column(String(255), nullable=False)
    filename_uploaded = Column(String(255), nullable=False)
    content_type = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("TicketMessage", back_populates="attachments")

# =============================================================================
# SLA MANAGEMENT
# =============================================================================

class SLAViolation(Base):
    __tablename__ = "sla_violations"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer) # No FK specified in SQL, keep as Integer
    service_type = Column(String(20)) # internet, voice, custom
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    violation_type = Column(String(50), nullable=False) # response_time, resolution_time, uptime
    violation_start = Column(DateTime(timezone=True), nullable=False)
    violation_end = Column(DateTime(timezone=True))
    sla_target = Column(Integer) # target in minutes or percentage
    actual_value = Column(Integer) # actual value
    credit_amount = Column(DECIMAL(10,4), default=0)
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id"))
    status = Column(String(20), default='pending') # pending, processed, ignored
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")
    ticket = relationship("Ticket")
    credit_note = relationship("CreditNote")
    reviews = relationship("SLACreditReview", back_populates="violation", cascade="all, delete-orphan")

class SLACreditReview(Base):
    __tablename__ = "sla_credit_reviews"
    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("sla_violations.id", ondelete="CASCADE"), nullable=False)
    review_status = Column(String(20), default='pending') # pending, approved, rejected, requires_info
    
    # Review Details
    assigned_reviewer = Column(Integer, ForeignKey("administrators.id"))
    review_priority = Column(String(20), default='normal') # low, normal, high, urgent
    auto_calculated_credit = Column(DECIMAL(10,4), nullable=False)
    reviewer_recommended_credit = Column(DECIMAL(10,4))
    final_approved_credit = Column(DECIMAL(10,4))
    
    # Review Process
    review_notes = Column(Text)
    rejection_reason = Column(Text)
    requires_manager_approval = Column(Boolean, default=False)
    manager_approved_by = Column(Integer, ForeignKey("administrators.id"))
    manager_approval_notes = Column(Text)
    
    # Customer Communication
    customer_notified = Column(Boolean, default=False)
    customer_dispute = Column(Boolean, default=False)
    customer_dispute_notes = Column(Text)
    
    # Workflow Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    review_started_at = Column(DateTime(timezone=True))
    review_completed_at = Column(DateTime(timezone=True))
    credit_applied_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    violation = relationship("SLAViolation", back_populates="reviews")
    assigned_reviewer_admin = relationship("Administrator", foreign_keys=[assigned_reviewer])
    manager_approver_admin = relationship("Administrator", foreign_keys=[manager_approved_by])

class SLACreditWorkflow(Base):
    __tablename__ = "sla_credit_workflows"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Trigger Conditions
    min_credit_amount = Column(DECIMAL(10,4), default=0) # Auto-approve below this amount
    max_auto_approve_amount = Column(DECIMAL(10,4), default=0)
    violation_types = Column(ARRAY(String(100))) # Which violation types this applies to
    customer_tiers = Column(ARRAY(String(50))) # Which customer tiers this applies to
    
    # Approval Requirements
    requires_l1_approval = Column(Boolean, default=False)
    requires_l2_approval = Column(Boolean, default=False)
    requires_manager_approval = Column(Boolean, default=False)
    
    # Reviewers
    default_reviewer_group = Column(Integer, ForeignKey("ticket_groups.id"))
    escalation_reviewer_group = Column(Integer, ForeignKey("ticket_groups.id"))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    default_group = relationship("TicketGroup", foreign_keys=[default_reviewer_group])
    escalation_group = relationship("TicketGroup", foreign_keys=[escalation_reviewer_group])


# =============================================================================
# SCHEDULING & JOBS SYSTEM
# =============================================================================

class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(255), nullable=False)
    job_type = Column(String(100), nullable=False)
    description = Column(Text)
    schedule_cron = Column(String(100))
    next_run = Column(DateTime(timezone=True))
    last_run = Column(DateTime(timezone=True))
    last_duration_seconds = Column(Integer)
    status = Column(String(50), default='active')
    configuration = Column(JSON, default={})
    retry_on_failure = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("Administrator")
    history = relationship("JobExecutionHistory", back_populates="job", cascade="all, delete-orphan")

class JobExecutionHistory(Base):
    __tablename__ = "job_execution_history"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scheduled_jobs.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False) # e.g., running, completed, failed, cancelled
    output = Column(Text)
    error_message = Column(Text)
    records_processed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ScheduledJob", back_populates="history")

# =============================================================================
# WEBHOOKS SYSTEM
# =============================================================================

class WebhookConfig(Base):
    __tablename__ = "webhook_configs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret = Column(String(255))
    headers = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    retry_count = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    events = relationship("WebhookEvent", back_populates="config", cascade="all, delete-orphan")

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id = Column(Integer, primary_key=True, index=True)
    webhook_config_id = Column(Integer, ForeignKey("webhook_configs.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True))
    next_retry_at = Column(DateTime(timezone=True))
    status = Column(String(50), default='pending', index=True)
    response_status = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    config = relationship("WebhookConfig", back_populates="events")



# =============================================================================
# COMMUNICATIONS SYSTEM
# =============================================================================

class CommunicationTemplate(Base):
    __tablename__ = "communication_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_code = Column(String(100), unique=True, nullable=False)
    
    # Template Type & Category
    template_type = Column(String(50), nullable=False) # email, sms, whatsapp, push, letter
    category = Column(String(100), nullable=False) # billing, service, outage, marketing, etc.
    subcategory = Column(String(100)) # payment_reminder, service_activation, etc.
    
    # Content
    subject_template = Column(Text) # For email/push notifications
    body_template = Column(Text, nullable=False)
    html_template = Column(Text) # Rich HTML version for emails
    
    # Template Variables
    available_variables = Column(JSON, default=[]) # List of available variables
    required_variables = Column(JSON, default=[]) # Variables that must be provided
    variable_descriptions = Column(JSON, default={}) # Help text for variables
    
    # Localization
    language = Column(String(10), default='en')
    is_default_language = Column(Boolean, default=False)
    parent_template_id = Column(Integer, ForeignKey("communication_templates.id")) # For translations
    
    # Targeting & Conditions
    customer_segments = Column(JSON, default=[]) # Which customer segments this applies to
    trigger_conditions = Column(JSON, default={}) # When this template should be used
    priority = Column(Integer, default=0) # Higher priority templates are preferred
    
    # Formatting & Delivery
    format_type = Column(String(50), default='text') # text, html, markdown
    delivery_timing = Column(String(50), default='immediate') # immediate, scheduled, digest
    throttle_limit = Column(Integer, default=0) # Max sends per hour (0 = unlimited)
    
    # A/B Testing
    is_ab_test = Column(Boolean, default=False)
    ab_test_group = Column(String(50)) # A, B, C, etc.
    ab_test_weight = Column(Integer, default=100) # Percentage weight
    ab_test_ends_at = Column(DateTime(timezone=True))
    
    # Approval Workflow
    status = Column(String(50), default='draft') # draft, pending_approval, approved, rejected, archived
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("administrators.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    
    # Usage Tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    success_rate = Column(DECIMAL(5,2), default=0) # Delivery success rate
    open_rate = Column(DECIMAL(5,2), default=0) # Email open rate
    click_rate = Column(DECIMAL(5,2), default=0) # Click-through rate
    
    # Version Control
    version_number = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    replaced_by = Column(Integer, ForeignKey("communication_templates.id"))
    
    # Compliance
    gdpr_compliant = Column(Boolean, default=True)
    retention_period = Column(Integer, default=365) # Days to retain sending logs
    
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("Administrator", foreign_keys=[created_by])
    approver = relationship("Administrator", foreign_keys=[approved_by])
    parent_template = relationship("CommunicationTemplate", remote_side=[id], foreign_keys=[parent_template_id])
    replaced_by_template = relationship("CommunicationTemplate", remote_side=[id], foreign_keys=[replaced_by])


class MessageQueue(Base):
    __tablename__ = "message_queue"
    id = Column(Integer, primary_key=True, index=True)
    recipient_type = Column(String(50), nullable=False)
    recipient_id = Column(Integer, nullable=False)
    generated_file_id = Column(Integer, ForeignKey("file_storage.id"), nullable=True)
    channel = Column(String(50), nullable=False)
    template_id = Column(Integer, ForeignKey("communication_templates.id"))
    subject = Column(Text)
    body = Column(Text, nullable=False)
    variables = Column(JSON, default={})
    priority = Column(Integer, default=5)
    scheduled_for = Column(DateTime(timezone=True))
    status = Column(String(50), default='queued', index=True)
    attempts = Column(Integer, default=0)
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    provider_message_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    template = relationship("CommunicationTemplate")
    generated_file = relationship("FileStorage")

# =============================================================================
# FREERADIUS STANDARD MODELS
# =============================================================================
class RadAcct(Base):
    __tablename__ = 'radacct'
    
    radacctid = Column(BigInteger, primary_key=True)
    acctsessionid = Column(String(64), nullable=False, index=True)
    acctuniqueid = Column(String(32), nullable=False, unique=True)
    username = Column(String(64), nullable=False, index=True)
    realm = Column(String(64), default='', nullable=True)
    nasipaddress = Column(INET, nullable=False)
    nasportid = Column(String(50), nullable=True)
    nasporttype = Column(String(50), nullable=True)
    acctstarttime = Column(DateTime(timezone=True))
    acctupdatetime = Column(DateTime(timezone=True))
    acctstoptime = Column(DateTime(timezone=True))
    acctsessiontime = Column(Integer)
    acctauthentic = Column(String(50), nullable=True)
    connectinfo_start = Column(Text, nullable=True)
    connectinfo_stop = Column(Text, nullable=True)
    acctinputoctets = Column(BigInteger)
    acctoutputoctets = Column(BigInteger)
    calledstationid = Column(Text, nullable=True)
    callingstationid = Column(Text, nullable=True)
    acctterminatecause = Column(String(32))
    servicetype = Column(Text, nullable=True)
    framedprotocol = Column(Text, nullable=True)
    framedipaddress = Column(INET)
    framedipv6address = Column(INET, nullable=True)
    framedipv6prefix = Column(INET, nullable=True)
    framedinterfaceid = Column(Text, nullable=True)
    delegatedipv6prefix = Column(INET, nullable=True)
    class_ = Column('class', Text, nullable=True)

    __table_args__ = (
        Index('radacct_active_session_idx', 'acctuniqueid', postgresql_where=text('acctstoptime IS NULL')),
    )

class RadCheck(Base):
    __tablename__ = 'radcheck'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, default='', index=True)
    attribute = Column(String(64), nullable=False, default='')
    op = Column(String(2), nullable=False, default='==')
    value = Column(String(253), nullable=False, default='')

class RadGroupCheck(Base):
    __tablename__ = 'radgroupcheck'
    
    id = Column(Integer, primary_key=True)
    groupname = Column(String(64), nullable=False, default='', index=True)
    attribute = Column(String(64), nullable=False, default='')
    op = Column(String(2), nullable=False, default='==')
    value = Column(String(253), nullable=False, default='')

class RadGroupReply(Base):
    __tablename__ = 'radgroupreply'
    
    id = Column(Integer, primary_key=True)
    groupname = Column(String(64), nullable=False, default='', index=True)
    attribute = Column(String(64), nullable=False, default='')
    op = Column(String(2), nullable=False, default='=')
    value = Column(String(253), nullable=False, default='')

class RadReply(Base):
    __tablename__ = 'radreply'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, default='', index=True)
    attribute = Column(String(64), nullable=False, default='')
    op = Column(String(2), nullable=False, default='=')
    value = Column(String(253), nullable=False, default='')

class RadUserGroup(Base):
    __tablename__ = 'radusergroup'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, default='', index=True)
    groupname = Column(String(64), nullable=False, default='')
    priority = Column(Integer, nullable=False, default=0)

class RadPostAuth(Base):
    __tablename__ = 'radpostauth'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, index=True)
    pass_ = Column('pass', String(64), nullable=False)
    reply = Column(String(32), nullable=False)
    authdate = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class Nas(Base):
    __tablename__ = 'nas'
    
    id = Column(Integer, primary_key=True)
    nasname = Column(String(128), nullable=False)
    shortname = Column(String(32), nullable=False, unique=True)
    type = Column(String(30), nullable=False, default='other')
    ports = Column(Integer)
    secret = Column(String(60), nullable=False)
    server = Column(String(64))
    community = Column(String(50))
    description = Column(String(200))
    
    __table_args__ = (Index('nas_nasname', 'nasname'),)


# =============================================================================
# BULK OPERATIONS SYSTEM
# =============================================================================

class BulkOperation(Base):
    __tablename__ = "bulk_operations"
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), nullable=False)
    operation_name = Column(String(255), nullable=False)
    initiated_by = Column(Integer, ForeignKey("administrators.id"))
    
    # Input Data
    input_source = Column(String(50))
    input_file_path = Column(String(500))
    input_data = Column(JSON)
    
    # Operation Configuration
    target_table = Column(String(100))
    operation_mode = Column(String(50))
    validation_rules = Column(JSON, default={})
    dry_run = Column(Boolean, default=False)
    
    # Progress Tracking
    status = Column(String(20), default='queued', index=True)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    skipped_records = Column(Integer, default=0)
    
    # Results
    success_data = Column(JSON, default=[])
    error_data = Column(JSON, default=[])
    validation_errors = Column(JSON, default=[])
    warnings = Column(JSON, default=[])
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    estimated_completion = Column(DateTime(timezone=True))
    
    # Options
    rollback_on_failure = Column(Boolean, default=False)
    send_completion_notification = Column(Boolean, default=True)
    notification_email = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    initiator = relationship("Administrator")
    details = relationship("BulkOperationDetail", back_populates="operation", cascade="all, delete-orphan")

class BulkOperationDetail(Base):
    __tablename__ = "bulk_operation_details"
    id = Column(Integer, primary_key=True, index=True)
    bulk_operation_id = Column(Integer, ForeignKey("bulk_operations.id", ondelete="CASCADE"), nullable=False)
    record_index = Column(Integer, nullable=False)
    record_identifier = Column(String(255))
    operation_action = Column(String(50))
    status = Column(String(20))
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    warning_message = Column(Text)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

    operation = relationship("BulkOperation", back_populates="details")

# =============================================================================
# INFRASTRUCTURE DEPENDENCY MAPPING
# =============================================================================

class CustomerInfrastructureDependency(Base):
    __tablename__ = "customer_infrastructure_dependencies"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Network Dependencies
    primary_router_id = Column(Integer, ForeignKey("routers.id"))
    backup_router_id = Column(Integer, ForeignKey("routers.id"))
    primary_monitoring_device_id = Column(Integer, ForeignKey("monitoring_devices.id"))
    network_site_id = Column(Integer, ForeignKey("network_sites.id"))
    
    # Service Dependencies
    service_id = Column(Integer)
    service_type = Column(String(20))
    
    # Physical Dependencies
    ipv4_pool_id = Column(Integer, ForeignKey("ipv4_networks.id"))
    ipv6_pool_id = Column(Integer, ForeignKey("ipv6_networks.id"))
    static_ip_id = Column(Integer, ForeignKey("ipv4_ips.id"))
    
    # Circuit/Connection Info
    circuit_id = Column(String(100))
    port_number = Column(String(50))
    vlan_id = Column(Integer)
    
    # Dependency Type
    dependency_type = Column(String(50), nullable=False)
    criticality = Column(String(20), default='medium')
    
    # Status
    is_active = Column(Boolean, default=True)
    last_verified = Column(DateTime(timezone=True))
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")
    primary_router = relationship("Router", foreign_keys=[primary_router_id])
    backup_router = relationship("Router", foreign_keys=[backup_router_id])
    primary_monitoring_device = relationship("MonitoringDevice")
    network_site = relationship("NetworkSite")
    ipv4_pool = relationship("IPv4Network")
    ipv6_pool = relationship("IPv6Network")
    static_ip = relationship("IPv4IP")

class InfrastructureImpactAnalysis(Base):
    __tablename__ = "infrastructure_impact_analysis"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer)
    device_type = Column(String(50))
    
    # Impact Scope
    total_customers_impacted = Column(Integer, default=0)
    business_customers_impacted = Column(Integer, default=0)
    residential_customers_impacted = Column(Integer, default=0)
    services_impacted = Column(JSON, default=[])
    
    # Financial Impact
    estimated_revenue_impact_hourly = Column(DECIMAL(10,4), default=0)
    estimated_sla_credits_required = Column(DECIMAL(10,4), default=0)
    
    # Analysis Date
    analysis_date = Column(Date, server_default=func.current_date())
    analyzed_by = Column(Integer, ForeignKey("administrators.id"))
    
    # Cache status
    needs_refresh = Column(Boolean, default=False)
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    analyzed_by_admin = relationship("Administrator")

    __table_args__ = (UniqueConstraint('device_id', 'device_type', 'analysis_date'),)

# =============================================================================
# NETWORK & DEVICE MANAGEMENT
# =============================================================================

class NetworkSite(Base):
    __tablename__ = "network_sites"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(Text)
    gps = Column(String(100))
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    partners_ids = Column(ARRAY(Integer), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    location = relationship("Location")
    monitoring_devices = relationship("MonitoringDevice", back_populates="network_site")

class NetworkCategory(Base):
    __tablename__ = "network_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IPv4Network(Base):
    __tablename__ = "ipv4_networks"
    id = Column(Integer, primary_key=True, index=True)
    network = Column(INET, nullable=False)
    mask = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    comment = Column(Text)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    network_category = Column(Integer, ForeignKey("network_categories.id"), nullable=False)
    network_type = Column(String(20), default='endnet')
    type_of_usage = Column(String(20), default='management')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    location = relationship("Location")
    category = relationship("NetworkCategory")

class IPv4IP(Base):
    __tablename__ = "ipv4_ips"
    id = Column(Integer, primary_key=True, index=True)
    ipv4_networks_id = Column(Integer, ForeignKey("ipv4_networks.id", ondelete="CASCADE"), nullable=False)
    ip = Column(INET, nullable=False)
    hostname = Column(String(255))
    location_id = Column(Integer, ForeignKey("locations.id"))
    title = Column(String(255))
    comment = Column(Text)
    host_category = Column(Integer)
    is_used = Column(Boolean, default=False)
    status = Column(Integer, default=9)
    last_check = Column(BigInteger, default=0)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    card_id = Column(Integer)
    module = Column(String(100))
    module_item_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    network = relationship("IPv4Network")
    location = relationship("Location")
    customer = relationship("Customer")

    __table_args__ = (UniqueConstraint('ipv4_networks_id', 'ip'),)

class IPv6Network(Base):
    __tablename__ = "ipv6_networks"
    id = Column(Integer, primary_key=True, index=True)
    network = Column(INET, nullable=False)
    prefix = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    comment = Column(Text)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    network_category = Column(Integer, ForeignKey("network_categories.id"), nullable=False)
    network_type = Column(String(20), default='endnet')
    type_of_usage = Column(String(20), default='static')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    location = relationship("Location")
    category = relationship("NetworkCategory")

class IPv6IP(Base):
    __tablename__ = "ipv6_ips"
    id = Column(Integer, primary_key=True, index=True)
    ipv6_networks_id = Column(Integer, ForeignKey("ipv6_networks.id", ondelete="CASCADE"), nullable=False)
    ip = Column(INET, nullable=False)
    ip_end = Column(INET)
    prefix = Column(Integer)
    location_id = Column(Integer, ForeignKey("locations.id"))
    title = Column(String(255))
    comment = Column(Text)
    host_category = Column(Integer)
    is_used = Column(Boolean, default=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    service_id = Column(Integer)
    card_id = Column(Integer)
    module = Column(String(100))
    module_item_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    network = relationship("IPv6Network")
    location = relationship("Location")
    customer = relationship("Customer")

class MonitoringDeviceType(Base):
    __tablename__ = "monitoring_device_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)

class MonitoringGroup(Base):
    __tablename__ = "monitoring_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)

class MonitoringProducer(Base):
    __tablename__ = "monitoring_producers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)

class MonitoringDevice(Base):
    __tablename__ = "monitoring_devices"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    network_site_id = Column(Integer, ForeignKey("network_sites.id"))
    producer_id = Column(Integer, ForeignKey("monitoring_producers.id"), nullable=False)
    model = Column(String(255))
    ip = Column(INET, nullable=False, unique=True)
    active = Column(Boolean, default=True)
    type_id = Column(Integer, ForeignKey("monitoring_device_types.id"), nullable=False)
    monitoring_group_id = Column(Integer, ForeignKey("monitoring_groups.id"), nullable=False)
    partners_ids = Column(ARRAY(Integer), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    ping_state = Column(String(20), default='unknown')
    snmp_state = Column(String(20), default='unknown')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    network_site = relationship("NetworkSite", back_populates="monitoring_devices")
    producer = relationship("MonitoringProducer")
    device_type = relationship("MonitoringDeviceType")
    monitoring_group = relationship("MonitoringGroup")
    location = relationship("Location")

class Router(Base):
    __tablename__ = "routers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), unique=True, nullable=False) # Added title column
    model = Column(String(255))
    partners_ids = Column(ARRAY(Integer), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    ip = Column(INET, unique=True, nullable=False)
    address = Column(Text)
    gps = Column(Text) # area coordinates
    gps_point = Column(String(100)) # point coordinates
    authorization_method = Column(String(50), default='none')
    accounting_method = Column(String(50), default='none')
    nas_type = Column(Integer, nullable=False) # e.g., 1 for MikroTik, 2 for Cisco
    nas_ip = Column(INET)
    radius_secret = Column(String(255))
    status = Column(String(20), default='unknown')
    pool_ids = Column(ARRAY(Integer))
    
    # Mikrotik API Configuration
    api_login = Column(String(100))
    api_password = Column(String(255))
    api_port = Column(Integer, default=8728)
    api_enable = Column(Boolean, default=False)
    api_status = Column(String(20), default='unknown')
    shaper = Column(Boolean, default=False)
    shaper_id = Column(Integer)
    shaping_type = Column(String(20), default='simple')
    
    # Status tracking
    last_status = Column(DateTime(timezone=True))
    cpu_usage = Column(Integer, default=0)
    platform = Column(String(100))
    version = Column(String(100))
    board_name = Column(String(100))
    connection_error = Column(Integer, default=0)
    last_api_error = Column(Boolean, default=False)
    is_used = Column(Boolean, default=False)
    pid = Column(Integer)
    used_date_time = Column(DateTime(timezone=True))
    change_status = Column(Boolean, default=False)
    change_authorization = Column(Boolean, default=False)
    change_shaping = Column(Boolean, default=False)
    last_connect = Column(DateTime(timezone=True))
    last_accounting = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    location = relationship("Location")

class RouterSector(Base):
    __tablename__ = "router_sectors"
    id = Column(Integer, primary_key=True, index=True)
    router_id = Column(Integer, ForeignKey("routers.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    speed_down = Column(Integer, nullable=False) # kbps
    speed_up = Column(Integer, nullable=False) # kbps
    limit_at = Column(Integer, default=95) # percentage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    router = relationship("Router", backref="sectors")

# =============================================================================
# ANALYTICS & SYSTEM CONFIG
# =============================================================================

class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(Integer, primary_key=True, index=True)
    module = Column(String(100), nullable=False)
    path = Column(String(100), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    partner = relationship("Partner")

    __table_args__ = (UniqueConstraint('module', 'path', 'key', 'partner_id'),)

# =============================================================================
# COMMUNICATION TEMPLATES SYSTEM
# =============================================================================


class TemplateUsageLog(Base):
    __tablename__ = "template_usage_logs"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("communication_templates.id", ondelete="CASCADE"), nullable=False)
    delivery_type = Column(String(50), nullable=False)
    recipient_type = Column(String(50))
    recipient_id = Column(Integer)
    recipient_address = Column(String(255))
    final_subject = Column(Text)
    final_body = Column(Text)
    variables_used = Column(JSON)
    delivery_status = Column(String(50), default='pending')
    delivery_provider = Column(String(100))
    delivery_provider_id = Column(String(255))
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    bounced_at = Column(DateTime(timezone=True))
    complaint_at = Column(DateTime(timezone=True))
    delivery_attempts = Column(Integer, default=0)
    failure_reason = Column(Text)
    provider_response = Column(JSON)
    triggered_by = Column(String(100))
    business_context = Column(JSON)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("CommunicationTemplate")

class TemplateABTestResult(Base):
    __tablename__ = "template_ab_test_results"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("communication_templates.id", ondelete="CASCADE"), nullable=False)
    test_group = Column(String(50), nullable=False)
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_bounced = Column(Integer, default=0)
    total_complaints = Column(Integer, default=0)
    delivery_rate = Column(DECIMAL(5,2), default=0)
    open_rate = Column(DECIMAL(5,2), default=0)
    click_rate = Column(DECIMAL(5,2), default=0)
    bounce_rate = Column(DECIMAL(5,2), default=0)
    complaint_rate = Column(DECIMAL(5,2), default=0)
    is_statistically_significant = Column(Boolean, default=False)
    confidence_level = Column(DECIMAL(5,2), default=0)
    winner_declared = Column(Boolean, default=False)
    test_period_start = Column(DateTime(timezone=True))
    test_period_end = Column(DateTime(timezone=True))
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("CommunicationTemplate")

    __table_args__ = (UniqueConstraint('template_id', 'test_group'),)

# =============================================================================
# CONTACT VERIFICATION & PREFERENCES
# =============================================================================

class ContactVerification(Base):
    __tablename__ = "contact_verifications"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    verification_type = Column(String(50), nullable=False)
    verification_method = Column(String(50), nullable=False)
    
    # Verification Details
    verification_token = Column(String(255), unique=True, nullable=False)
    verification_code = Column(String(20))
    verification_target = Column(String(255), nullable=False)
    
    # Status
    status = Column(String(50), default='pending')
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Timing
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True))
    
    # Metadata
    verification_ip = Column(INET)
    verification_user_agent = Column(Text)
    failure_reason = Column(Text)
    
    # Security
    rate_limit_key = Column(String(255))
    suspicious_activity = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact")

class CustomerContactPreference(Base):
    __tablename__ = "customer_contact_preferences"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"))
    
    # Communication Channels
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    phone_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    postal_enabled = Column(Boolean, default=False)
    push_notifications_enabled = Column(Boolean, default=False)
    
    # Communication Types
    billing_notifications = Column(Boolean, default=True)
    service_notifications = Column(Boolean, default=True)
    outage_notifications = Column(Boolean, default=True)
    maintenance_notifications = Column(Boolean, default=True)
    marketing_communications = Column(Boolean, default=False)
    newsletter = Column(Boolean, default=False)
    product_updates = Column(Boolean, default=False)
    security_alerts = Column(Boolean, default=True)
    
    # Frequency Preferences
    notification_frequency = Column(String(50), default='immediate')
    digest_time = Column(Time, server_default=text("'09:00:00'"))
    timezone = Column(String(100), default='UTC')
    
    # Quiet Hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(Time, server_default=text("'22:00:00'"))
    quiet_hours_end = Column(Time, server_default=text("'08:00:00'"))
    quiet_hours_timezone = Column(String(100), default='UTC')
    
    # Language & Format
    preferred_language = Column(String(10), default='en')
    date_format = Column(String(20), default='YYYY-MM-DD')
    currency = Column(String(3), default='USD')
    
    # GDPR Compliance
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True))
    consent_ip = Column(INET)
    consent_method = Column(String(50))
    consent_evidence = Column(Text)
    data_processing_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    
    # Opt-out Management
    global_opt_out = Column(Boolean, default=False)
    opt_out_date = Column(DateTime(timezone=True))
    opt_out_reason = Column(Text)
    easy_unsubscribe_token = Column(UUID(as_uuid=True), server_default=text("gen_random_uuid()"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")
    contact = relationship("Contact")

    __table_args__ = (UniqueConstraint('customer_id', 'contact_id'),)

# =============================================================================
# FILE STORAGE SYSTEM
# =============================================================================

class StorageProvider(Base):
    __tablename__ = "storage_providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(String(50), nullable=False)
    endpoint_url = Column(String(500))
    region = Column(String(100))
    access_key_id = Column(String(255))
    secret_access_key_encrypted = Column(Text)
    bucket_name = Column(String(255), nullable=False)
    base_path = Column(String(500), default='')
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    server_side_encryption = Column(Boolean, default=True)
    versioning_enabled = Column(Boolean, default=False)
    lifecycle_rules = Column(JSON, default=[])
    cors_configuration = Column(JSON, default={})
    multipart_threshold = Column(BigInteger, default=67108864)
    max_concurrent_uploads = Column(Integer, default=10)
    upload_timeout = Column(Integer, default=300)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FileStorage(Base):
    __tablename__ = "file_storage"
    id = Column(Integer, primary_key=True, index=True)
    file_uuid = Column(UUID(as_uuid=True), default=func.gen_random_uuid(), unique=True, nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_extension = Column(String(20))
    mime_type = Column(String(255))
    file_size = Column(BigInteger, nullable=False)
    checksum_md5 = Column(String(32))
    checksum_sha256 = Column(String(64))
    storage_provider_id = Column(Integer, ForeignKey("storage_providers.id"), nullable=False)
    bucket_name = Column(String(255), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    storage_url = Column(String(1000))
    cdn_url = Column(String(1000))
    file_category = Column(String(100))
    file_purpose = Column(String(100))
    is_public = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    encryption_key_id = Column(String(255))
    owner_type = Column(String(50))
    owner_id = Column(Integer)
    access_level = Column(String(50), default='private')
    allowed_roles = Column(ARRAY(String(100)))
    expiry_date = Column(DateTime(timezone=True))
    archive_date = Column(DateTime(timezone=True))
    is_archived = Column(Boolean, default=False)
    archive_storage_class = Column(String(50))
    version_number = Column(Integer, default=1)
    parent_file_id = Column(Integer, ForeignKey("file_storage.id"))
    is_latest_version = Column(Boolean, default=True)
    download_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True))
    access_log_enabled = Column(Boolean, default=False)
    retention_period = Column(Integer)
    legal_hold = Column(Boolean, default=False)
    compliance_tags = Column(ARRAY(String(100)))
    uploaded_by_type = Column(String(50))
    uploaded_by_id = Column(Integer)
    upload_session_id = Column(String(255))
    upload_ip = Column(INET)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    storage_provider = relationship("StorageProvider")
    parent_file = relationship("FileStorage", remote_side=[id])

class FileAccessLog(Base):
    __tablename__ = "file_access_logs"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_storage.id", ondelete="CASCADE"), nullable=False)
    access_type = Column(String(50), nullable=False)
    access_method = Column(String(50))
    accessor_type = Column(String(50))
    accessor_id = Column(Integer)
    accessor_name = Column(String(255))
    session_id = Column(String(255))
    ip_address = Column(INET)
    user_agent = Column(Text)
    referer_url = Column(Text)
    request_headers = Column(JSON)
    response_status = Column(Integer)
    bytes_transferred = Column(BigInteger)
    response_time_ms = Column(Integer)
    security_level = Column(String(50))
    authentication_method = Column(String(100))
    access_granted = Column(Boolean, default=True)
    denial_reason = Column(Text)
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())

    file = relationship("FileStorage")

class FileShare(Base):
    __tablename__ = "file_shares"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_storage.id", ondelete="CASCADE"), nullable=False)
    share_token = Column(UUID(as_uuid=True), default=func.gen_random_uuid(), unique=True, nullable=False)
    share_type = Column(String(50), default='temporary')
    password_hash = Column(String(255))
    max_downloads = Column(Integer, default=1)
    current_downloads = Column(Integer, default=0)
    allowed_ips = Column(ARRAY(INET))
    allowed_domains = Column(ARRAY(String(255)))
    expires_at = Column(DateTime(timezone=True))
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    created_by_type = Column(String(50))
    created_by_id = Column(Integer)
    last_accessed = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    file = relationship("FileStorage")

class DocumentTemplate(Base):
    __tablename__ = "document_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(100), nullable=False)
    template_file_id = Column(Integer, ForeignKey("file_storage.id"))
    variables = Column(JSON, default=[])
    required_variables = Column(JSON, default=[])
    default_values = Column(JSON, default={})
    output_format = Column(String(50), default='pdf')
    paper_size = Column(String(20), default='A4')
    orientation = Column(String(20), default='portrait')
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    template_file = relationship("FileStorage")

class GeneratedDocument(Base):
    __tablename__ = "generated_documents"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("document_templates.id"))
    generated_file_id = Column(Integer, ForeignKey("file_storage.id"))
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    generated_for_type = Column(String(50))
    generated_for_id = Column(Integer)
    template_variables = Column(JSON)
    generation_status = Column(String(50), default='completed')
    error_message = Column(Text)
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("DocumentTemplate")
    generated_file = relationship("FileStorage")

# =============================================================================
# DATA MIGRATION SUPPORT
# =============================================================================

class MigrationStatus(Base):
    __tablename__ = "migration_status"
    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(50), nullable=False)
    migration_type = Column(String(50), nullable=False)
    status = Column(String(20), default='pending')
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    error_log = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    mappings = relationship("MigrationMapping", back_populates="migration", cascade="all, delete-orphan")

class MigrationMapping(Base):
    __tablename__ = "migration_mappings"
    id = Column(Integer, primary_key=True, index=True)
    migration_id = Column(Integer, ForeignKey("migration_status.id", ondelete="CASCADE"), nullable=False)
    source_table = Column(String(100), nullable=False)
    source_id = Column(String(100), nullable=False)
    target_table = Column(String(100), nullable=False)
    target_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    migration = relationship("MigrationStatus", back_populates="mappings")

# =============================================================================
# FRAMEWORK - DYNAMIC ENTITY BUILDER
# =============================================================================

class FrameworkEntity(Base):
    __tablename__ = "framework_entities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Dynamic Schema Definition
    schema_ = Column('schema', JSON, nullable=False)
    ui_configuration = Column(JSON, default={})
    api_configuration = Column(JSON, default={})
    
    # Table Management
    table_name = Column(String(100), unique=True)
    auto_create_table = Column(Boolean, default=True)
    
    # Framework Settings
    is_system_entity = Column(Boolean, default=False)
    is_template_entity = Column(Boolean, default=False)
    is_customizable = Column(Boolean, default=True)
    
    # Access Control
    permissions = Column(JSON, default={})
    field_permissions = Column(JSON, default={})
    
    # Entity Relationships
    parent_entity_id = Column(Integer, ForeignKey("framework_entities.id"))
    related_entities = Column(JSON, default=[])
    
    # Versioning & Change Management
    version_number = Column(Integer, default=1)
    change_log = Column(JSON, default=[])
    
    # Metadata
    icon = Column(String(100), default='fa-table')
    color = Column(String(7), default='#357bf2')
    sort_order = Column(Integer, default=0)
    
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("Administrator")
    parent_entity = relationship("FrameworkEntity", remote_side=[id])
    fields = relationship(
        "FrameworkField",
        foreign_keys="[FrameworkField.entity_id]",
        back_populates="entity",
        cascade="all, delete-orphan"
    )
    # This relationship finds all fields in OTHER entities that REFERENCE this one.
    # This is useful for impact analysis, e.g., "what fields reference the Customer entity?"
    referencing_fields = relationship(
        "FrameworkField",
        foreign_keys="[FrameworkField.reference_entity_id]",
        back_populates="reference_entity"
    )
class FrameworkField(Base):
    __tablename__ = "framework_fields"
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("framework_entities.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    field_type = Column(String(50), nullable=False)
    field_config = Column(JSON, default={})
    validation_rules = Column(JSON, default={})
    default_value = Column(Text)
    ui_component = Column(String(100), default='input')
    ui_config = Column(JSON, default={})
    display_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    is_editable = Column(Boolean, default=True)
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    is_system_field = Column(Boolean, default=False)
    is_computed = Column(Boolean, default=False)
    computation_formula = Column(Text)
    reference_entity_id = Column(Integer, ForeignKey("framework_entities.id"))
    reference_display_field = Column(String(100))
    cascade_delete = Column(Boolean, default=False)
    field_permissions = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship back to the FrameworkEntity that owns this field.
    entity = relationship(
        "FrameworkEntity",
        foreign_keys=[entity_id],
        back_populates="fields"
    )

    # Relationship to the FrameworkEntity that this field references (if it's a reference type).
    reference_entity = relationship(
        "FrameworkEntity",
        foreign_keys=[reference_entity_id],
        back_populates="referencing_fields"
    )

    __table_args__ = (UniqueConstraint('entity_id', 'field_name'),)

class FrameworkEntityData(Base):
    __tablename__ = "framework_entity_data"
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("framework_entities.id"), nullable=False)
    record_id = Column(Integer, nullable=False)
    field_id = Column(Integer, ForeignKey("framework_fields.id"), nullable=False)
    value_text = Column(Text)
    value_number = Column(DECIMAL(20,6))
    value_date = Column(Date)
    value_datetime = Column(DateTime(timezone=True))
    value_boolean = Column(Boolean)
    value_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    entity = relationship("FrameworkEntity")
    field = relationship("FrameworkField")

    __table_args__ = (UniqueConstraint('entity_id', 'record_id', 'field_id'),)

# =============================================================================
# ENHANCED NETWORK MANAGEMENT MODELS
# =============================================================================

# SNMP Monitoring Models
class SNMPMonitoringProfile(Base):
    """SNMP monitoring configuration profiles for different device types"""
    __tablename__ = "snmp_monitoring_profiles"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("monitoring_devices.id"), nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    device_type = Column(String(100), nullable=False)  # router, switch, ap, server
    snmp_version = Column(String(10), default='2c')  # 1, 2c, 3
    community_string = Column(String(100), default='public')
    
    # SNMP v3 specific
    security_level = Column(String(20))  # noAuthNoPriv, authNoPriv, authPriv
    auth_protocol = Column(String(20))   # MD5, SHA
    auth_password = Column(String(255))
    priv_protocol = Column(String(20))   # DES, AES
    priv_password = Column(String(255))
    username = Column(String(100))
    
    # Monitoring settings
    polling_interval = Column(Integer, default=300)  # seconds
    timeout = Column(Integer, default=10)  # seconds
    retries = Column(Integer, default=3)
    
    # OID configurations
    oid_configurations = Column(JSON, default={})
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    device = relationship("MonitoringDevice")

class SNMPMonitoringData(Base):
    """Historical SNMP monitoring data"""
    __tablename__ = "snmp_monitoring_data"
    id = Column(BigInteger, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("monitoring_devices.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(Integer, ForeignKey("snmp_monitoring_profiles.id"), nullable=False)
    
    # SNMP response data
    system_uptime = Column(BigInteger)  # timeticks
    system_name = Column(String(255))
    system_description = Column(Text)
    system_contact = Column(String(255))
    system_location = Column(String(255))
    
    # Interface data (stored as JSON for flexibility)
    interfaces_data = Column(JSON, default={})
    
    # Performance metrics
    cpu_usage = Column(DECIMAL(5,2))
    memory_usage = Column(DECIMAL(5,2))
    temperature = Column(DECIMAL(5,2))
    
    # Custom OID values
    custom_oids = Column(JSON, default={})
    
    # Collection metadata
    collection_time = Column(DateTime(timezone=True), nullable=False)
    response_time = Column(Integer)  # ms
    collection_status = Column(String(20), default='success')  # success, timeout, error
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    device = relationship("MonitoringDevice")
    profile = relationship("SNMPMonitoringProfile")

# Bandwidth Management and QoS Models
class QoSPolicy(Base):
    """Quality of Service policies"""
    __tablename__ = "qos_policies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    
    # Policy configuration
    policy_type = Column(String(50), nullable=False)  # bandwidth_limit, traffic_shaping, priority
    direction = Column(String(20), default='both')  # upload, download, both
    
    # Bandwidth limits
    max_upload_rate = Column(BigInteger)  # bits per second
    max_download_rate = Column(BigInteger)  # bits per second
    guaranteed_upload_rate = Column(BigInteger)
    guaranteed_download_rate = Column(BigInteger)
    
    # Traffic shaping
    burst_size = Column(BigInteger)
    burst_threshold = Column(BigInteger)
    burst_time = Column(Integer)
    
    # Priority settings
    priority_level = Column(Integer, default=1)  # 1-8, lower is higher priority
    dscp_marking = Column(Integer)  # DSCP value
    
    # Advanced settings
    queue_type = Column(String(50))  # fifo, sfq, fq_codel
    parent_policy_id = Column(Integer, ForeignKey("qos_policies.id"))
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    parent_policy = relationship("QoSPolicy", remote_side=[id], back_populates="child_policies")
    child_policies = relationship("QoSPolicy", back_populates="parent_policy")

class DeviceQoSAssignment(Base):
    """QoS policy assignments to devices/services"""
    __tablename__ = "device_qos_assignments"
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("qos_policies.id"), nullable=False)
    
    # Assignment target
    target_type = Column(String(50), nullable=False)  # device, service, customer, interface
    target_id = Column(Integer, nullable=False)
    
    # Router/device specific
    router_id = Column(Integer, ForeignKey("routers.id"))
    interface_name = Column(String(100))
    
    # Service specific
    service_id = Column(Integer)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    
    # Assignment settings
    is_active = Column(Boolean, default=True)
    activation_date = Column(DateTime(timezone=True))
    deactivation_date = Column(DateTime(timezone=True))
    
    # Status tracking
    deployment_status = Column(String(20), default='pending')  # pending, deployed, failed
    last_deployed_at = Column(DateTime(timezone=True))
    deployment_error = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    policy = relationship("QoSPolicy")
    router = relationship("Router")
    customer = relationship("Customer")

class BandwidthUsageLog(Base):
    """Historical bandwidth usage tracking"""
    __tablename__ = "bandwidth_usage_logs"
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Target identification
    target_type = Column(String(50), nullable=False)  # customer, service, interface
    target_id = Column(Integer, nullable=False)
    router_id = Column(Integer, ForeignKey("routers.id"))
    interface_name = Column(String(100))
    
    # Usage data
    upload_bytes = Column(BigInteger, default=0)
    download_bytes = Column(BigInteger, default=0)
    total_bytes = Column(BigInteger, default=0)
    
    # Rates (calculated)
    upload_rate = Column(BigInteger)  # bits per second
    download_rate = Column(BigInteger)  # bits per second
    
    # Time tracking
    measurement_start = Column(DateTime(timezone=True), nullable=False)
    measurement_end = Column(DateTime(timezone=True), nullable=False)
    interval_seconds = Column(Integer, default=300)
    
    # Quality metrics
    packet_loss = Column(DECIMAL(5,2))
    latency = Column(DECIMAL(8,2))  # milliseconds
    jitter = Column(DECIMAL(8,2))   # milliseconds
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    router = relationship("Router")

# Network Topology Models
class NetworkTopology(Base):
    """Network topology mapping"""
    __tablename__ = "network_topologies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    topology_type = Column(String(50), default='layer2')  # layer2, layer3, physical
    
    # Discovery settings
    auto_discovery = Column(Boolean, default=True)
    discovery_method = Column(String(50))  # snmp_cdp, snmp_lldp, manual
    last_discovery = Column(DateTime(timezone=True))
    next_discovery = Column(DateTime(timezone=True))
    
    # Geographic bounds (for mapping)
    map_bounds = Column(JSON)  # {"north": lat, "south": lat, "east": lng, "west": lng}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
class NetworkConnection(Base):
    """Network connections between devices"""
    __tablename__ = "network_connections"
    id = Column(Integer, primary_key=True, index=True)
    topology_id = Column(Integer, ForeignKey("network_topologies.id"), nullable=False)
    
    # Connection endpoints
    source_device_id = Column(Integer, ForeignKey("monitoring_devices.id"), nullable=False)
    source_interface = Column(String(100))
    target_device_id = Column(Integer, ForeignKey("monitoring_devices.id"), nullable=False)
    target_interface = Column(String(100))
    
    # Connection properties
    connection_type = Column(String(50))  # ethernet, fiber, wireless, virtual
    link_speed = Column(BigInteger)  # bits per second
    duplex_mode = Column(String(20))  # full, half, auto
    
    # Discovery info
    discovered_via = Column(String(50))  # cdp, lldp, manual, ping
    discovery_protocol_data = Column(JSON)
    
    # Status
    status = Column(String(20), default='active')  # active, inactive, down
    last_seen = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    topology = relationship("NetworkTopology")
    source_device = relationship("MonitoringDevice", foreign_keys=[source_device_id])
    target_device = relationship("MonitoringDevice", foreign_keys=[target_device_id])

# Fault Management Models
class NetworkIncident(Base):
    """Network incidents and faults"""
    __tablename__ = "network_incidents"
    id = Column(Integer, primary_key=True, index=True)
    
    # Incident identification
    incident_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Incident classification
    incident_type = Column(String(50), nullable=False)  # outage, degradation, planned
    severity = Column(String(20), default='medium')  # low, medium, high, critical
    priority = Column(String(20), default='medium')   # low, medium, high, urgent
    category = Column(String(50))  # hardware, software, connectivity, performance
    
    # Affected resources
    affected_devices = Column(ARRAY(Integer))
    affected_services = Column(ARRAY(Integer))
    affected_customers = Column(ARRAY(Integer))
    impact_scope = Column(String(50))  # local, regional, global
    
    # Status tracking
    status = Column(String(20), default='open')  # open, investigating, resolved, closed
    resolution_status = Column(String(50))  # fixed, workaround, duplicate, not_reproducible
    
    # Timeline
    detected_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("administrators.id"))
    assigned_team = Column(String(100))
    
    # Resolution details
    root_cause = Column(Text)
    resolution_notes = Column(Text)
    preventive_actions = Column(Text)
    
    # SLA tracking
    sla_deadline = Column(DateTime(timezone=True))
    sla_breached = Column(Boolean, default=False)
    response_time_minutes = Column(Integer)
    resolution_time_minutes = Column(Integer)
    
    # External references
    external_ticket_id = Column(String(100))
    vendor_case_id = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    assigned_admin = relationship("Administrator")

class IncidentUpdate(Base):
    """Updates/comments on network incidents"""
    __tablename__ = "incident_updates"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("network_incidents.id", ondelete="CASCADE"), nullable=False)
    
    update_type = Column(String(50), default='comment')  # comment, status_change, assignment
    title = Column(String(255))
    content = Column(Text, nullable=False)
    
    # Change tracking
    field_changes = Column(JSON)  # {"field": {"old": value, "new": value}}
    
    # Author
    created_by = Column(Integer, ForeignKey("administrators.id"))
    
    # Visibility
    is_internal = Column(Boolean, default=False)
    is_customer_visible = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    incident = relationship("NetworkIncident")
    author = relationship("Administrator")

class AutomatedAlert(Base):
    """Automated network alerts and monitoring rules"""
    __tablename__ = "automated_alerts"
    id = Column(Integer, primary_key=True, index=True)
    
    # Alert definition
    name = Column(String(255), nullable=False)
    description = Column(Text)
    alert_type = Column(String(50), nullable=False)  # threshold, state_change, pattern
    
    # Monitoring target
    target_type = Column(String(50), nullable=False)  # device, interface, service, customer
    target_id = Column(Integer)
    metric_name = Column(String(100), nullable=False)
    
    # Threshold conditions
    condition_operator = Column(String(10))  # >, <, >=, <=, ==, !=
    threshold_value = Column(DECIMAL(20,6))
    threshold_duration = Column(Integer)  # seconds
    
    # Advanced conditions
    condition_script = Column(Text)  # Python script for complex conditions
    
    # Alert settings
    severity = Column(String(20), default='medium')
    cooldown_period = Column(Integer, default=300)  # seconds before re-alerting
    max_alerts_per_hour = Column(Integer, default=10)
    
    # Notification settings
    notification_channels = Column(JSON, default=[])  # email, sms, webhook, slack
    notification_recipients = Column(JSON, default=[])
    
    # Auto-incident creation
    create_incident = Column(Boolean, default=False)
    incident_template = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime(timezone=True))
    trigger_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AlertHistory(Base):
    """History of triggered alerts"""
    __tablename__ = "alert_history"
    id = Column(BigInteger, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("automated_alerts.id"), nullable=False)
    
    # Trigger details
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    trigger_value = Column(DECIMAL(20,6))
    condition_met = Column(Text)
    
    # Context data
    context_data = Column(JSON)  # Additional data at time of trigger
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True))
    resolution_value = Column(DECIMAL(20,6))
    auto_resolved = Column(Boolean, default=False)
    
    # Associated incident
    incident_id = Column(Integer, ForeignKey("network_incidents.id"))
    
    # Notification status
    notifications_sent = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    alert = relationship("AutomatedAlert")
    incident = relationship("NetworkIncident")

# Performance Analytics Models
class PerformanceMetric(Base):
    """Performance metrics definitions"""
    __tablename__ = "performance_metrics"
    id = Column(Integer, primary_key=True, index=True)
    
    # Metric definition
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Metric properties
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    data_type = Column(String(20), default='numeric')  # numeric, boolean, text
    unit = Column(String(50))  # bytes, packets, percent, ms, etc.
    
    # Collection settings
    collection_method = Column(String(50))  # snmp, api, calculation
    collection_frequency = Column(Integer, default=300)  # seconds
    retention_period = Column(Integer, default=2592000)  # seconds (30 days default)
    
    # Calculation settings (for derived metrics)
    calculation_formula = Column(Text)
    source_metrics = Column(JSON, default=[])
    
    # Display settings
    chart_type = Column(String(50), default='line')  # line, bar, area, gauge
    color = Column(String(7), default='#357bf2')
    
    # Thresholds for visualization
    warning_threshold = Column(DECIMAL(20,6))
    critical_threshold = Column(DECIMAL(20,6))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PerformanceData(Base):
    """Time-series performance data"""
    __tablename__ = "performance_data"
    id = Column(BigInteger, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("performance_metrics.id"), nullable=False)
    
    # Target identification
    target_type = Column(String(50), nullable=False)  # device, interface, service, customer
    target_id = Column(Integer, nullable=False)
    
    # Data point
    timestamp = Column(DateTime(timezone=True), nullable=False)
    value_numeric = Column(DECIMAL(20,6))
    value_text = Column(String(255))
    value_boolean = Column(Boolean)
    
    # Data quality
    quality_score = Column(DECIMAL(3,2))  # 0.00 to 1.00
    collection_method = Column(String(50))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    metric = relationship("PerformanceMetric")
    
    # Index for time-series queries
    __table_args__ = (
        Index('idx_performance_data_target_time', 'target_type', 'target_id', 'timestamp'),
        Index('idx_performance_data_metric_time', 'metric_id', 'timestamp'),
    )

class PerformanceDashboard(Base):
    """Custom performance dashboards"""
    __tablename__ = "performance_dashboards"
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Dashboard configuration
    layout_config = Column(JSON, default={})
    widgets = Column(JSON, default=[])  # Widget configurations
    
    # Access control
    is_public = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("administrators.id"))
    shared_with = Column(JSON, default=[])  # User/role IDs with access
    
    # Settings
    auto_refresh = Column(Boolean, default=True)
    refresh_interval = Column(Integer, default=60)  # seconds
    time_range_default = Column(String(20), default='1h')  # 15m, 1h, 6h, 24h, 7d
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("Administrator")
