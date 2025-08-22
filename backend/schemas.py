from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import enum

# Enums for RBAC (mirroring models.py)
class UserKind(str, enum.Enum):
    staff = "staff"
    customer = "customer"
    reseller = "reseller"

class RoleScope(str, enum.Enum):
    system = "system"
    customer = "customer"
    reseller = "reseller"

# New RBAC Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    kind: UserKind = UserKind.staff
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    kind: Optional[UserKind] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None # For password change

class UserInDB(UserBase):
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserProfileBase(BaseModel):
    customer_id: Optional[int] = None
    reseller_id: Optional[int] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class PermissionBase(BaseModel):
    code: str
    description: str
    module: str

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    module: Optional[str] = None

class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    scope: RoleScope = RoleScope.system
    parent_role_id: Optional[int] = None

class RoleCreate(RoleBase):
    permission_codes: List[str] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[RoleScope] = None
    parent_role_id: Optional[int] = None
    permission_codes: Optional[List[str]] = None

class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    permissions: List[PermissionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class UserRoleBase(BaseModel):
    user_id: int
    role_id: int
    customer_id: Optional[int] = None
    reseller_id: Optional[int] = None

class UserRoleCreate(UserRoleBase):
    pass

class UserRolesSync(BaseModel):
    role_ids: List[int]

class UserRoleResponse(UserRoleBase):
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Audit Log Schemas
class AuditLogBase(BaseModel):
    user_type: str
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action: str
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    before_values: Optional[dict] = None
    after_values: Optional[dict] = None
    changed_fields: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_url: Optional[str] = None
    request_method: Optional[str] = None
    risk_level: str = 'low'

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaginatedAuditLogResponse(BaseModel):
    total: int
    items: List[AuditLogResponse]

class CustomerBillingBase(BaseModel):
    enabled: bool = True
    billing_date: int = 1
    billing_due: int = 14
    grace_period: int = 3

class CustomerBillingResponse(CustomerBillingBase):
    customer_id: int
    model_config = ConfigDict(from_attributes=True)

class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: str = "active"
    category: str = "person" # person or company

class CustomerCreate(CustomerBase):
    login: str
    partner_id: int
    location_id: int
    billing_config: Optional[CustomerBillingBase] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    partner_id: Optional[int] = None
    location_id: Optional[int] = None
    billing_config: Optional[CustomerBillingBase] = None

class CustomerResponse(CustomerBase):
    id: int
    login: str
    created_at: datetime
    partner_id: int
    location_id: int
    billing_config: Optional[CustomerBillingResponse] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedCustomerResponse(BaseModel):
    total: int
    items: List[CustomerResponse]

# Location Schemas
class LocationBase(BaseModel):
    name: str
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = 'Nigeria'
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    timezone: Optional[str] = 'Africa/Lagos'
    custom_fields: Optional[Dict[str, Any]] = {}

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    timezone: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class LocationResponse(LocationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Existing Schemas (modified or renamed)
class PartnerBase(BaseModel):
    name: str
    framework_config: Optional[dict] = {}
    ui_customizations: Optional[dict] = {}
    branding_config: Optional[dict] = {}

class PartnerCreate(PartnerBase):
    pass

class Partner(PartnerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AdministratorBase(BaseModel):
    # Removed: login, name, email, role, framework_roles
    phone: Optional[str] = None
    timeout: Optional[int] = 1200
    is_active: Optional[bool] = True
    custom_permissions: Optional[dict] = {}
    ui_preferences: Optional[dict] = {}

class AdministratorCreate(AdministratorBase):
    user_id: int # Link to an existing user

class AdministratorUpdate(AdministratorBase):
    pass # All fields are optional for update

class Administrator(AdministratorBase):
    id: int
    user_id: int
    partner_id: int
    last_login: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    partner: Partner
    user: UserResponse # Include the associated User object

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class SettingBase(BaseModel):
    config_key: str
    config_value: dict
    config_type: Optional[str] = 'json'
    description: Optional[str] = None

class SettingCreate(SettingBase):
    pass

class SettingUpdate(BaseModel):
    config_key: Optional[str] = None
    config_value: Optional[dict] = None
    config_type: Optional[str] = None
    description: Optional[str] = None

class Setting(SettingBase):
    id: int
    is_system: bool
    is_encrypted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Tariff Schemas ---
class InternetTariffBase(BaseModel):
    title: str
    price: Decimal
    speed_download: int
    speed_upload: int

class InternetTariffCreate(InternetTariffBase):
    pass

class InternetTariffUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[Decimal] = None
    speed_download: Optional[int] = None
    speed_upload: Optional[int] = None

class InternetTariffResponse(InternetTariffBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PaginatedInternetTariffResponse(BaseModel):
    total: int
    items: List[InternetTariffResponse]

# --- Service Schemas ---
class InternetServiceBase(BaseModel):
    customer_id: int
    tariff_id: int
    status: str = 'active'
    description: str
    login: str
    password: Optional[str] = None
    ipv4: Optional[str] = None
    mac: Optional[str] = None

class InternetServiceCreate(InternetServiceBase):
    pass

class InternetServiceUpdate(BaseModel):
    tariff_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    password: Optional[str] = None
    ipv4: Optional[str] = None
    mac: Optional[str] = None

class InternetServiceResponse(InternetServiceBase):
    id: int
    start_date: datetime
    customer: CustomerResponse
    tariff: InternetTariffResponse
    model_config = ConfigDict(from_attributes=True)

class PaginatedInternetServiceResponse(BaseModel):
    total: int
    items: List[InternetServiceResponse]

# --- Billing Schemas ---
class InvoiceItemBase(BaseModel):
    description: str
    quantity: int = 1
    price: Decimal
    tax: Decimal = Decimal("0.00")

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemResponse(InvoiceItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class InvoiceBase(BaseModel):
    customer_id: int
    status: str = 'not_paid'

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]
    # These fields are calculated by the billing engine and passed for creation.
    number: str
    total: Decimal
    due: Decimal
    date_till: Optional[datetime] = None

# New schema for manual creation from the UI/API
class ManualInvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: int
    number: str
    date_created: datetime
    total: Decimal
    due: Decimal
    items: List[InvoiceItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

class PaginatedInvoiceResponse(BaseModel):
    total: int
    items: List[InvoiceResponse]

class PaymentBase(BaseModel):
    customer_id: int
    invoice_id: Optional[int] = None
    payment_type_id: int
    receipt_number: str
    amount: Decimal
    comment: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    date: datetime
    model_config = ConfigDict(from_attributes=True)

class PaginatedPaymentResponse(BaseModel):
    total: int
    items: List[PaymentResponse]

class PaymentMethodResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class TaxResponse(BaseModel):
    id: int
    name: str
    rate: Decimal

    model_config = ConfigDict(from_attributes=True)


class SetupData(BaseModel):
    partner_name: str
    admin_email: EmailStr # Changed from admin_login
    admin_password: str
    admin_full_name: str # Changed from admin_name

# =============================================================================
# INTEGRATED SUPPORT SYSTEM SCHEMAS
# =============================================================================

# --- Ticket Status Schemas ---
class TicketStatusBase(BaseModel):
    title_for_agent: str
    title_for_customer: str
    label: Optional[str] = 'default'
    mark: Optional[List[str]] = ['open', 'unresolved']
    icon: Optional[str] = 'fa-tasks'
    view_on_dashboard: Optional[bool] = True

class TicketStatusCreate(TicketStatusBase):
    pass

class TicketStatusUpdate(BaseModel):
    title_for_agent: Optional[str] = None
    title_for_customer: Optional[str] = None
    label: Optional[str] = None
    mark: Optional[List[str]] = None
    icon: Optional[str] = None
    view_on_dashboard: Optional[bool] = None

class TicketStatusResponse(TicketStatusBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Ticket Group Schemas ---
class TicketGroupBase(BaseModel):
    title: str
    description: Optional[str] = None

class TicketGroupCreate(TicketGroupBase):
    pass

class TicketGroupUpdate(TicketGroupBase):
    title: Optional[str] = None

class TicketGroupResponse(TicketGroupBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Ticket Type Schemas ---
class TicketTypeBase(BaseModel):
    title: str
    background_color: Optional[str] = None

class TicketTypeCreate(TicketTypeBase):
    pass

class TicketTypeUpdate(TicketTypeBase):
    title: Optional[str] = None

class TicketTypeResponse(TicketTypeBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Ticket Message & Attachment Schemas ---
class TicketMessageBase(BaseModel):
    message: str
    is_internal_note: bool = False

class TicketMessageCreate(TicketMessageBase):
    pass # author_user_id will be set from the current user

class TicketMessageResponse(TicketMessageBase):
    id: int
    author: UserResponse # The user who wrote the message
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Ticket Schemas ---
class TicketBase(BaseModel):
    subject: str
    priority: str = 'medium'

class TicketCreate(TicketBase):
    customer_id: int
    type_id: int
    status_id: int
    group_id: Optional[int] = None
    assign_to: Optional[int] = None
    initial_message: str # The first message when creating a ticket

class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    priority: Optional[str] = None
    status_id: Optional[int] = None
    group_id: Optional[int] = None
    assign_to: Optional[int] = None
    type_id: Optional[int] = None

class TicketResponse(TicketBase):
    id: int
    customer: Optional[CustomerResponse] = None
    reporter: UserResponse
    assignee: Optional[Administrator] = None
    status: TicketStatusResponse
    group: Optional[TicketGroupResponse] = None
    ticket_type: Optional[TicketTypeResponse] = None
    messages: List[TicketMessageResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TicketSummaryResponse(TicketBase):
    """A leaner response for ticket list views, omitting heavy fields like messages."""
    id: int
    customer: Optional[CustomerResponse] = None
    reporter: UserResponse
    assignee: Optional[Administrator] = None
    status: TicketStatusResponse
    group: Optional[TicketGroupResponse] = None
    ticket_type: Optional[TicketTypeResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PaginatedTicketResponse(BaseModel):
    total: int
    items: List[TicketSummaryResponse] 
class LeadBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None

class LeadResponse(LeadBase):
    id: int
    status: str
    converted_to_opportunity_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaginatedLeadResponse(BaseModel):
    total: int
    items: List[LeadResponse]

class OpportunityBase(BaseModel):
    name: str
    lead_id: int
    amount: Decimal
    stage: str

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    lead_id: Optional[int] = None
    amount: Optional[Decimal] = None
    stage: Optional[str] = None

class OpportunityResponse(OpportunityBase):
    id: int
    customer_id: Optional[int] = None
    lead: Optional[LeadResponse] = None
    model_config = ConfigDict(from_attributes=True)

class PaginatedOpportunityResponse(BaseModel):
    total: int
    items: List[OpportunityResponse]

class OpportunityConvert(BaseModel):
    """Schema for converting an opportunity to a customer."""
    # We can reuse the CustomerCreate schema but might want to simplify it
    # for the conversion process, as some data comes from the lead.
    login: str
    partner_id: int
    location_id: int
    billing_config: Optional[CustomerBillingBase] = None