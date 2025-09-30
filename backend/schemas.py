from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime, date, time
from decimal import Decimal
import enum
from uuid import UUID

# Define a TypeVar for generic types
T = TypeVar('T')

# Define the generic PaginatedResponse schema
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    model_config = ConfigDict(from_attributes=True)

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
    business_context: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IPv4NetworkBase(BaseModel):
    network: str
    mask: int
    title: str
    comment: Optional[str] = None
    location_id: int
    network_category: int
    network_type: str = 'endnet'
    type_of_usage: str = 'management'

class IPv4NetworkCreate(IPv4NetworkBase):
    pass

class IPv4NetworkResponse(IPv4NetworkBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# CONTACT VERIFICATION & PREFERENCES SCHEMAS
# =============================================================================

class ContactVerificationBase(BaseModel):
    contact_id: int
    verification_type: str
    verification_method: str
    verification_target: str
    expires_at: datetime

class ContactVerificationCreate(ContactVerificationBase):
    pass

class ContactVerificationResponse(ContactVerificationBase):
    id: int
    verification_token: str
    status: str
    attempts: int
    sent_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CustomerContactPreferenceBase(BaseModel):
    customer_id: int
    contact_id: Optional[int] = None
    email_enabled: bool = True
    sms_enabled: bool = False
    billing_notifications: bool = True
    service_notifications: bool = True
    outage_notifications: bool = True
    maintenance_notifications: bool = True
    marketing_communications: bool = False
    preferred_language: str = 'en'
    marketing_consent: bool = False

class CustomerContactPreferenceCreate(CustomerContactPreferenceBase):
    pass

class CustomerContactPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    billing_notifications: Optional[bool] = None
    service_notifications: Optional[bool] = None
    outage_notifications: Optional[bool] = None
    marketing_communications: Optional[bool] = None
    preferred_language: Optional[str] = None
    marketing_consent: Optional[bool] = None

class CustomerContactPreferenceResponse(CustomerContactPreferenceBase):
    id: int
    whatsapp_enabled: bool
    push_notifications_enabled: bool
    newsletter: bool
    security_alerts: bool
    easy_unsubscribe_token: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class IPv4IPBase(BaseModel):
    ipv4_networks_id: int
    ip: str
    hostname: Optional[str] = None
    location_id: Optional[int] = None
    title: Optional[str] = None
    comment: Optional[str] = None
    is_used: bool = False
    customer_id: Optional[int] = None

class IPv4IPCreate(IPv4IPBase):
    pass

class IPv4IPResponse(IPv4IPBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class IPv4IPRangeGenerate(BaseModel):
    start_ip: str
    end_ip: str
    title: Optional[str] = None
    comment: Optional[str] = None

class NextAvailableIPResponse(BaseModel):
    ip: Optional[str] = None

class IPv6IPRangeGenerate(BaseModel):
    start_ip: str
    end_ip: str
    prefix: int
    title: Optional[str] = None
    comment: Optional[str] = None

class IPv6NetworkBase(BaseModel):
    network: str
    prefix: int
    title: str
    comment: Optional[str] = None
    location_id: int
    network_category: int
    network_type: str = 'endnet'
    type_of_usage: str = 'static'

class IPv6NetworkCreate(IPv6NetworkBase):
    pass

class IPv6NetworkResponse(IPv6NetworkBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class IPv6IPBase(BaseModel):
    ipv6_networks_id: int
    ip: str
    ip_end: Optional[str] = None
    prefix: Optional[int] = None
    location_id: Optional[int] = None
    title: Optional[str] = None
    comment: Optional[str] = None
    is_used: bool = False
    customer_id: Optional[int] = None

class IPv6IPCreate(IPv6IPBase):
    pass

class IPv6IPResponse(IPv6IPBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# SLA MANAGEMENT SCHEMAS
# =============================================================================
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
    # Add missing address fields to allow them during creation
    street_1: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None

class CustomerCreate(CustomerBase):
    login: str
    partner_id: int
    location_id: int
    password: Optional[str] = None
    billing_config: Optional[CustomerBillingBase] = None

class CustomerUpdate(BaseModel):
    # Core Info
    name: Optional[str] = None
    login: Optional[str] = None  # For changing customer login
    password: Optional[str] = None  # For setting/changing customer portal password
    email: Optional[EmailStr] = None
    billing_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None

    # Relationships
    partner_id: Optional[int] = None
    location_id: Optional[int] = None
    parent_id: Optional[int] = None

    # Address
    street_1: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    subdivision_id: Optional[int] = None

    # Financial
    billing_type: Optional[str] = None
    
    # Metadata
    gps: Optional[str] = None
    conversion_date: Optional[datetime] = None

    # Framework
    custom_fields: Optional[Dict[str, Any]] = None
    workflow_state: Optional[Dict[str, Any]] = None

    # Nested Billing Config
    billing_config: Optional[CustomerBillingBase] = None

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

# Partner Schemas
class PartnerBase(BaseModel):
    name: str
    framework_config: Optional[dict] = {}
    ui_customizations: Optional[dict] = {}
    branding_config: Optional[dict] = {}

class PartnerCreate(PartnerBase):
    pass

class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    framework_config: Optional[dict] = None
    ui_customizations: Optional[dict] = None
    branding_config: Optional[dict] = None

class Partner(PartnerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedPartnerResponse(BaseModel):
    total: int
    items: List[Partner]

# =============================================================================
# CONTACTS & LABELS SCHEMAS
# =============================================================================

class ContactTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False

class ContactTypeCreate(ContactTypeBase):
    pass

class ContactTypeResponse(ContactTypeBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# INFRASTRUCTURE DEPENDENCY SCHEMAS
# =============================================================================

class CustomerInfrastructureDependencyBase(BaseModel):
    customer_id: int
    primary_router_id: Optional[int] = None
    backup_router_id: Optional[int] = None
    primary_monitoring_device_id: Optional[int] = None
    network_site_id: Optional[int] = None
    service_id: Optional[int] = None
    service_type: Optional[str] = None
    ipv4_pool_id: Optional[int] = None
    ipv6_pool_id: Optional[int] = None
    static_ip_id: Optional[int] = None
    circuit_id: Optional[str] = None
    port_number: Optional[str] = None
    vlan_id: Optional[int] = None
    dependency_type: str
    criticality: str = 'medium'
    is_active: bool = True
    notes: Optional[str] = None

class CustomerInfrastructureDependencyCreate(CustomerInfrastructureDependencyBase):
    pass

class CustomerInfrastructureDependencyResponse(CustomerInfrastructureDependencyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class InfrastructureImpactAnalysisBase(BaseModel):
    device_id: Optional[int] = None
    device_type: Optional[str] = None
    total_customers_impacted: int = 0
    business_customers_impacted: int = 0
    residential_customers_impacted: int = 0
    services_impacted: List[Any] = []
    estimated_revenue_impact_hourly: Decimal = Decimal('0.00')
    estimated_sla_credits_required: Decimal = Decimal('0.00')
    analysis_date: Optional[date] = None
    analyzed_by: Optional[int] = None
    needs_refresh: bool = False

class InfrastructureImpactAnalysisResponse(InfrastructureImpactAnalysisBase):
    id: int
    last_calculated: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class CustomerContactBase(BaseModel):
    contact_id: int
    contact_type_id: int
    is_primary: bool = False
    receives_billing: bool = False
    receives_technical: bool = False
    receives_marketing: bool = False
    receives_outage_notifications: bool = False
    notes: Optional[str] = None

class CustomerContactCreate(CustomerContactBase):
    pass

class CustomerContactResponse(CustomerContactBase):
    id: int
    customer_id: int
    contact: ContactResponse
    contact_type: ContactTypeResponse
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class CustomerLabelBase(BaseModel):
    label: str
    color: str = '#357bf2'
    icon: Optional[str] = None
    description: Optional[str] = None
    custom_properties: Dict[str, Any] = {}

class CustomerLabelCreate(CustomerLabelBase):
    pass

class CustomerLabelResponse(CustomerLabelBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CustomerResponse(CustomerBase):
    id: int
    login: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    partner_id: int
    location_id: int
    parent_id: Optional[int] = None

    # Address
    street_1: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    subdivision_id: Optional[int] = None

    # Financial
    billing_email: Optional[EmailStr] = None
    billing_type: Optional[str] = None

    # Metadata
    gps: Optional[str] = None

    # Relationships
    partner: Partner
    location: LocationResponse

    billing_config: Optional[CustomerBillingResponse] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedCustomerResponse(BaseModel):
    total: int
    items: List[CustomerResponse]

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

# --- Transaction Category Schemas ---
class TransactionCategoryBase(BaseModel):
    name: str
    is_base: bool = False
    category_config: Optional[Dict[str, Any]] = {}
    custom_fields: Optional[Dict[str, Any]] = {}

class TransactionCategoryCreate(TransactionCategoryBase):
    pass

class TransactionCategoryResponse(TransactionCategoryBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Tax Schemas ---
class TaxBase(BaseModel):
    name: str
    rate: Decimal
    type: str = 'single'
    archived: bool = False
    applicable_locations: Optional[List[int]] = None
    calculation_rules: Optional[Dict[str, Any]] = {}
    custom_fields: Optional[Dict[str, Any]] = {}

class TaxCreate(TaxBase):
    pass

class TaxUpdate(BaseModel):
    name: Optional[str] = None
    rate: Optional[Decimal] = None
    type: Optional[str] = None
    archived: Optional[bool] = None
    applicable_locations: Optional[List[int]] = None
    calculation_rules: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class TaxResponse(TaxBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Enhanced Billing Configuration Schemas
class BillingCycleBase(BaseModel):
    name: str
    cycle_type: str  # monthly, quarterly, semi_annual, annual, custom
    frequency_days: Optional[int] = None
    billing_day_type: str = 'fixed'  # fixed, end_of_month, custom
    billing_day: Optional[int] = None
    prorate_first_bill: bool = True
    prorate_last_bill: bool = True
    proration_method: str = 'daily'  # daily, monthly
    payment_terms_days: int = 14
    due_date_type: str = 'fixed'  # fixed, end_of_month
    grace_period_days: int = 0
    late_fee_type: Optional[str] = None  # percentage, fixed, none
    late_fee_amount: Decimal = Decimal('0.00')
    is_active: bool = True

class BillingCycleCreate(BillingCycleBase):
    pass

class BillingCycleUpdate(BaseModel):
    name: Optional[str] = None
    cycle_type: Optional[str] = None
    frequency_days: Optional[int] = None
    billing_day_type: Optional[str] = None
    billing_day: Optional[int] = None
    prorate_first_bill: Optional[bool] = None
    prorate_last_bill: Optional[bool] = None
    proration_method: Optional[str] = None
    payment_terms_days: Optional[int] = None
    due_date_type: Optional[str] = None
    grace_period_days: Optional[int] = None
    late_fee_type: Optional[str] = None
    late_fee_amount: Optional[Decimal] = None
    is_active: Optional[bool] = None

class BillingCycleResponse(BillingCycleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class CustomerBillingConfigBase(BaseModel):
    customer_id: int
    billing_cycle_id: int
    custom_billing_day: Optional[int] = None
    invoice_delivery_method: str = 'email'  # email, postal, portal
    invoice_format: str = 'pdf'  # pdf, html
    currency: str = 'USD'
    preferred_payment_method_id: Optional[int] = None
    auto_payment_enabled: bool = False
    credit_limit: Decimal = Decimal('0.00')
    dunning_enabled: bool = True
    tax_exempt: bool = False
    tax_exempt_reason: Optional[str] = None
    tax_exempt_certificate: Optional[str] = None

class CustomerBillingConfigCreate(CustomerBillingConfigBase):
    pass

class CustomerBillingConfigUpdate(BaseModel):
    billing_cycle_id: Optional[int] = None
    custom_billing_day: Optional[int] = None
    invoice_delivery_method: Optional[str] = None
    invoice_format: Optional[str] = None
    currency: Optional[str] = None
    preferred_payment_method_id: Optional[int] = None
    auto_payment_enabled: Optional[bool] = None
    credit_limit: Optional[Decimal] = None
    dunning_enabled: Optional[bool] = None
    tax_exempt: Optional[bool] = None
    tax_exempt_reason: Optional[str] = None
    tax_exempt_certificate: Optional[str] = None

class CustomerBillingConfigResponse(CustomerBillingConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    billing_cycle: Optional[BillingCycleResponse] = None
    model_config = ConfigDict(from_attributes=True)

class BillingEventBase(BaseModel):
    customer_id: int
    event_type: str
    invoice_id: Optional[int] = None
    payment_id: Optional[int] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    event_metadata: Optional[Dict] = None  # Renamed from 'metadata' to match model
    status: str = 'processed'
    error_message: Optional[str] = None
    created_by: str = 'system'

class BillingEventCreate(BillingEventBase):
    pass

class BillingEventResponse(BillingEventBase):
    id: int
    event_date: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UsageTrackingBase(BaseModel):
    customer_id: int
    service_type: str  # internet, voice, data
    service_id: int
    usage_date: date
    usage_type: str  # data_transfer, call_minutes, sms_count
    usage_amount: Decimal
    usage_unit: str  # MB, GB, minutes, count
    billable: bool = True
    rate_per_unit: Optional[Decimal] = None
    billing_period: Optional[str] = None  # YYYY-MM format
    location_id: Optional[int] = None
    device_info: Optional[Dict] = None

class UsageTrackingCreate(UsageTrackingBase):
    pass

class UsageTrackingUpdate(BaseModel):
    usage_amount: Optional[Decimal] = None
    billable: Optional[bool] = None
    rate_per_unit: Optional[Decimal] = None
    billing_period: Optional[str] = None
    device_info: Optional[Dict] = None

class UsageTrackingResponse(UsageTrackingBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Billing Analytics Schemas
class BillingAnalyticsRequest(BaseModel):
    start_date: date
    end_date: date
    report_type: str  # revenue_summary, aging_report, payment_analysis, tax_summary
    customer_ids: Optional[List[int]] = None
    service_types: Optional[List[str]] = None

class RevenueAnalyticsResponse(BaseModel):
    period: Dict[str, date]  # start and end dates
    total_revenue: Decimal
    total_tax: Decimal
    net_revenue: Decimal
    invoice_count: int
    revenue_by_service_type: Dict[str, Decimal]
    revenue_by_month: Dict[str, Decimal]

class AgingAnalyticsResponse(BaseModel):
    report_date: date
    aging_buckets: Dict[str, Decimal]  # current, 1_30_days, 31_60_days, etc.
    total_outstanding: Decimal
    customer_count_by_bucket: Dict[str, int]

class PaymentAnalyticsResponse(BaseModel):
    period: Dict[str, date]
    total_payments: Decimal
    payment_count: int
    payments_by_method: Dict[str, Decimal]
    average_payment_amount: Decimal
    payment_success_rate: float

# --- Tariff Schemas ---
class InternetTariffBase(BaseModel):
    title: str
    service_name: Optional[str] = None
    partners_ids: List[int]
    price: Decimal = Decimal('0.0')
    
    # Speed Configuration
    speed_download: int
    speed_upload: int
    speed_limit_at: int = 10
    aggregation: int = 1
    
    # Burst Configuration
    burst_limit: int = 0
    burst_limit_fixed_down: int = 0
    burst_limit_fixed_up: int = 0
    burst_threshold: int = 0
    burst_threshold_fixed_down: int = 0
    burst_threshold_fixed_up: int = 0
    burst_time: int = 0
    burst_type: str = 'none'
    
    # Speed Limit Configuration
    speed_limit_type: str = 'none'
    speed_limit_fixed_down: int = 0
    speed_limit_fixed_up: int = 0
    
    # Billing Configuration
    billing_types: Optional[List[str]] = None
    billing_days_count: int = 1
    custom_period: bool = False
    
    # Availability
    customer_categories: Optional[List[str]] = None
    available_for_services: bool = True
    available_for_locations: Optional[List[int]] = None
    hide_on_admin_portal: bool = False
    show_on_customer_portal: bool = False
    priority: str = 'normal'
    
    # Financial
    tax_id: Optional[int] = None
    transaction_category_id: Optional[int] = None
    
    # Framework Integration
    pricing_rules: Optional[Dict[str, Any]] = {}
    service_rules: Optional[Dict[str, Any]] = {}
    custom_fields: Optional[Dict[str, Any]] = {}

class InternetTariffCreate(InternetTariffBase):
    pass

class InternetTariffUpdate(BaseModel):
    title: Optional[str] = None
    service_name: Optional[str] = None
    partners_ids: Optional[List[int]] = None
    price: Optional[Decimal] = None
    speed_download: Optional[int] = None
    speed_upload: Optional[int] = None
    speed_limit_at: Optional[int] = None
    aggregation: Optional[int] = None
    burst_limit: Optional[int] = None
    burst_limit_fixed_down: Optional[int] = None
    burst_limit_fixed_up: Optional[int] = None
    burst_threshold: Optional[int] = None
    burst_threshold_fixed_down: Optional[int] = None
    burst_threshold_fixed_up: Optional[int] = None
    burst_time: Optional[int] = None
    burst_type: Optional[str] = None
    speed_limit_type: Optional[str] = None
    speed_limit_fixed_down: Optional[int] = None
    speed_limit_fixed_up: Optional[int] = None
    billing_types: Optional[List[str]] = None
    billing_days_count: Optional[int] = None
    custom_period: Optional[bool] = None
    customer_categories: Optional[List[str]] = None
    available_for_services: Optional[bool] = None
    available_for_locations: Optional[List[int]] = None
    hide_on_admin_portal: Optional[bool] = None
    show_on_customer_portal: Optional[bool] = None
    priority: Optional[str] = None
    tax_id: Optional[int] = None
    transaction_category_id: Optional[int] = None
    pricing_rules: Optional[Dict[str, Any]] = None
    service_rules: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class InternetTariffResponse(InternetTariffBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PaginatedInternetTariffResponse(BaseModel):
    total: int
    items: List[InternetTariffResponse]

class VoiceTariffBase(BaseModel):
    title: str
    service_name: Optional[str] = None
    type: str = 'voip'
    partners_ids: List[int]
    price: Decimal = Decimal('0.0')
    tax_id: Optional[int] = None
    transaction_category_id: Optional[int] = None

class VoiceTariffCreate(VoiceTariffBase):
    pass

class VoiceTariffUpdate(BaseModel):
    title: Optional[str] = None
    service_name: Optional[str] = None
    type: Optional[str] = None
    partners_ids: Optional[List[int]] = None
    price: Optional[Decimal] = None
    tax_id: Optional[int] = None
    transaction_category_id: Optional[int] = None
    billing_types: Optional[List[str]] = None
    billing_days_count: Optional[int] = None
    custom_period: Optional[bool] = None
    customer_categories: Optional[List[str]] = None
    available_for_services: Optional[bool] = None
    available_for_locations: Optional[List[int]] = None
    hide_on_admin_portal: Optional[bool] = None
    show_on_customer_portal: Optional[bool] = None
    custom_fields: Optional[Dict[str, Any]] = None

class VoiceTariffResponse(VoiceTariffBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PaginatedVoiceTariffResponse(BaseModel):
    total: int
    items: List[VoiceTariffResponse]

# --- Recurring Tariff Schemas ---
class RecurringTariffBase(BaseModel):
    title: str
    service_name: Optional[str] = None
    partners_ids: List[int]
    price: Decimal = Decimal('0.0')
    
    # Billing Configuration
    billing_types: Optional[List[str]] = None
    billing_days_count: int = 1
    custom_period: bool = False
    
    # Availability
    customer_categories: Optional[List[str]] = None
    available_for_services: bool = True
    available_for_locations: Optional[List[int]] = None
    hide_on_admin_portal: bool = False
    show_on_customer_portal: bool = False
    
    # Financial
    tax_id: Optional[int] = None
    transaction_category_id: Optional[int] = None
    
    # Framework Integration
    custom_fields: Optional[Dict[str, Any]] = {}

class RecurringTariffCreate(RecurringTariffBase):
    pass

class RecurringTariffUpdate(BaseModel):
    title: Optional[str] = None
    service_name: Optional[str] = None
    partners_ids: Optional[List[int]] = None
    price: Optional[Decimal] = None
    billing_types: Optional[List[str]] = None
    billing_days_count: Optional[int] = None
    custom_period: Optional[bool] = None
    customer_categories: Optional[List[str]] = None
    available_for_services: Optional[bool] = None
    available_for_locations: Optional[List[int]] = None
    hide_on_admin_portal: Optional[bool] = None
    show_on_customer_portal: Optional[bool] = None
    tax_id: Optional[int] = None
    transaction_category_id: Optional[int] = None
    custom_fields: Optional[Dict[str, Any]] = None

class RecurringTariffResponse(RecurringTariffBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PaginatedRecurringTariffResponse(BaseModel):
    total: int
    items: List[RecurringTariffResponse]

# --- OneTimeTariff Schemas ---
class OneTimeTariffBase(BaseModel):
    title: str
    service_description: Optional[str] = None
    price: Decimal = Decimal('0.0')
    partners_ids: List[int]
    customer_categories: Optional[List[str]] = None
    available_for_locations: Optional[List[int]] = None
    enabled: bool = True
    hide_on_admin_portal: bool = False
    show_on_customer_portal: bool = False
    tax_id: Optional[int] = None
    transaction_category_id: Optional[int] = None
    custom_fields: Optional[Dict[str, Any]] = {}

class OneTimeTariffCreate(OneTimeTariffBase):
    pass

class OneTimeTariffUpdate(BaseModel):
    title: Optional[str] = None
    service_description: Optional[str] = None
    price: Optional[Decimal] = None
    partners_ids: Optional[List[int]] = None
    customer_categories: Optional[List[str]] = None
    available_for_locations: Optional[List[int]] = None
    enabled: Optional[bool] = None
    hide_on_admin_portal: Optional[bool] = None
    show_on_customer_portal: Optional[bool] = None
    tax_id: Optional[int] = None
    transaction_category_id: Optional[int] = None
    custom_fields: Optional[Dict[str, Any]] = None

class OneTimeTariffResponse(OneTimeTariffBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaginatedOneTimeTariffResponse(BaseModel):
    total: int
    items: List[OneTimeTariffResponse]

# --- BundleTariff Schemas ---
class BundleTariffBase(BaseModel):
    title: str
    service_description: Optional[str] = None
    partners_ids: List[int]
    price: Decimal = Decimal('0.0')
    activation_fee: Decimal = Decimal('0.0')
    cancellation_fee: Decimal = Decimal('0.0')
    prior_cancellation_fee: Decimal = Decimal('0.0')
    change_to_other_bundle_fee: Decimal = Decimal('0.0')
    contract_duration: int = 0
    automatic_renewal: bool = False
    internet_tariffs: Optional[List[int]] = None
    voice_tariffs: Optional[List[int]] = None
    custom_tariffs: Optional[List[int]] = None
    custom_fields: Optional[Dict[str, Any]] = {}

class BundleTariffCreate(BundleTariffBase):
    pass

class BundleTariffUpdate(BaseModel):
    title: Optional[str] = None
    service_description: Optional[str] = None
    partners_ids: Optional[List[int]] = None
    price: Optional[Decimal] = None
    activation_fee: Optional[Decimal] = None
    cancellation_fee: Optional[Decimal] = None
    prior_cancellation_fee: Optional[Decimal] = None
    change_to_other_bundle_fee: Optional[Decimal] = None
    contract_duration: Optional[int] = None
    automatic_renewal: Optional[bool] = None
    internet_tariffs: Optional[List[int]] = None
    voice_tariffs: Optional[List[int]] = None
    custom_tariffs: Optional[List[int]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class BundleTariffResponse(BundleTariffBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaginatedBundleTariffResponse(BaseModel):
    total: int
    items: List[BundleTariffResponse]

# --- Service Schemas ---
class InternetServiceBase(BaseModel):
    customer_id: int
    tariff_id: int
    status: str = 'active'
    description: str
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    
    # Discount
    discount: Decimal = Decimal('0.0')
    discount_type: str = 'percent'
    discount_value: Decimal = Decimal('0.0')
    discount_start_date: Optional[date] = None
    discount_end_date: Optional[date] = None
    discount_text: Optional[str] = None
    
    # Network Configuration
    router_id: Optional[int] = None
    login: str
    password: Optional[str] = None
    taking_ipv4: int = 0
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = None
    
    # Framework Integration
    custom_fields: Optional[Dict[str, Any]] = {}

class InternetServiceCreate(InternetServiceBase):
    start_date: date
    end_date: Optional[date] = None

class InternetServiceUpdate(BaseModel):
    tariff_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    start_date: Optional[date] = None # Allow updating the service start date
    end_date: Optional[date] = None # Allow updating the service end date
    discount_value: Optional[Decimal] = None
    discount_text: Optional[str] = None
    router_id: Optional[int] = None
    password: Optional[str] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class InternetServiceResponse(InternetServiceBase):
    id: int
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: Optional[datetime] = None
    customer: CustomerResponse
    tariff: InternetTariffResponse
    model_config = ConfigDict(from_attributes=True)

class PaginatedInternetServiceResponse(BaseModel):
    total: int
    items: List[InternetServiceResponse]

# --- Voice Service Schemas ---
class VoiceServiceBase(BaseModel):
    customer_id: int
    tariff_id: int
    status: str = 'active'
    description: str
    phone: str

class VoiceServiceCreate(VoiceServiceBase):
    start_date: date

class VoiceServiceUpdate(BaseModel):
    tariff_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    start_date: Optional[date] = None

class VoiceServiceResponse(VoiceServiceBase):
    id: int
    start_date: date
    created_at: datetime
    customer: CustomerResponse
    tariff: VoiceTariffResponse
    model_config = ConfigDict(from_attributes=True)

class PaginatedVoiceServiceResponse(BaseModel):
    total: int
    items: List[VoiceServiceResponse]

# --- Recurring Service Schemas ---
class RecurringServiceBase(BaseModel):
    customer_id: int
    tariff_id: int
    status: str = 'active'
    description: str
    unit_price: Optional[Decimal] = None

class RecurringServiceCreate(RecurringServiceBase):
    start_date: date

class RecurringServiceUpdate(BaseModel):
    tariff_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    unit_price: Optional[Decimal] = None

class RecurringServiceResponse(RecurringServiceBase):
    id: int
    start_date: date
    created_at: datetime
    customer: CustomerResponse
    tariff: RecurringTariffResponse
    model_config = ConfigDict(from_attributes=True)

class PaginatedRecurringServiceResponse(BaseModel):
    total: int
    items: List[RecurringServiceResponse]

# --- Bundle Service Schemas ---
class BundleServiceBase(BaseModel):
    customer_id: int
    bundle_id: int
    status: str = 'active'
    description: str
    unit_price: Optional[Decimal] = None

class BundleServiceCreate(BundleServiceBase):
    start_date: date

class BundleServiceUpdate(BaseModel):
    bundle_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class BundleServiceResponse(BundleServiceBase):
    id: int
    start_date: date
    end_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    customer: CustomerResponse
    bundle: BundleTariffResponse
    model_config = ConfigDict(from_attributes=True)

class PaginatedBundleServiceResponse(BaseModel):
    total: int
    items: List[BundleServiceResponse]

# =============================================================================
# USAGE & FUP SCHEMAS
# =============================================================================

class FUPPolicyBase(BaseModel):
    tariff_id: int
    name: str
    fixed_up: int = 0
    fixed_down: int = 0
    accounting_traffic: bool = False
    accounting_online: bool = False
    action: str = 'block'
    percent: int = 0
    conditions: Optional[str] = None

class FUPPolicyCreate(FUPPolicyBase):
    pass

class FUPPolicyResponse(FUPPolicyBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CapTariffBase(BaseModel):
    title: str
    amount: Decimal
    amount_in: str = 'mb'
    price: Decimal = Decimal('0.0')
    type: str = 'manual'
    validity: str
    to_invoice: bool = False
    tariff_id: Optional[int] = None
    transaction_category_id: Optional[int] = None

class CapTariffCreate(CapTariffBase):
    pass

class CapTariffResponse(CapTariffBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FUPLimitBase(BaseModel):
    tariff_id: int
    cap_tariff_id: Optional[int] = None
    traffic_from: Optional[time] = None
    online_from: Optional[time] = None
    traffic_to: Optional[time] = None
    online_to: Optional[time] = None
    traffic_days: List[int] = [1,2,3,4,5,6,7]
    online_days: List[int] = [1,2,3,4,5,6,7]
    action: str = 'block'
    percent: int = 0
    traffic_amount: int = 0
    traffic_direction: str = 'up_down'
    traffic_in: str = 'gb'
    override_traffic: bool = False
    online_amount: int = 0
    online_in: str = 'hours'
    override_online: bool = False
    rollover_data: bool = False
    rollover_time: bool = False
    bonus_is_unlimited: bool = True
    bonus_traffic: Decimal = Decimal('0.0')
    bonus_traffic_in: Optional[str] = None
    fixed_up: int = 0
    fixed_down: int = 0
    top_up_over_usage: bool = False
    top_up_trigger_percent: int = 0
    use_bonus_when_normal_ended: bool = False

class FUPLimitResponse(FUPLimitBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FUPCounterBase(BaseModel):
    service_id: int
    day_up: int = 0
    day_down: int = 0
    day_time: int = 0
    day_bonus_up: int = 0
    day_bonus_down: int = 0
    week_up: int = 0
    week_down: int = 0
    week_bonus_up: int = 0
    week_bonus_down: int = 0
    week_time: int = 0
    month_up: int = 0
    month_down: int = 0
    month_bonus_up: int = 0
    month_bonus_down: int = 0
    month_time: int = 0
    cap_amount: int = 0
    cap_used: int = 0
    over_usage: int = 0

class FUPCounterResponse(FUPCounterBase):
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CappedDataBase(BaseModel):
    service_id: int
    quantity: int
    valid_till: Optional[datetime] = None

class CappedDataCreate(CappedDataBase):
    pass

class CappedDataResponse(CappedDataBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CustomerTrafficCounterResponse(BaseModel):
    service_id: int
    date: date
    up: int
    down: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# NETWORK & DEVICE MANAGEMENT SCHEMAS
# =============================================================================

# --- Generic Lookup Schemas for Network Config ---
class NetworkLookupBase(BaseModel):
    name: str

class NetworkLookupCreate(NetworkLookupBase):
    pass

class NetworkLookupResponse(NetworkLookupBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Network Site Schemas ---
class NetworkSiteBase(BaseModel):
    title: str
    description: Optional[str] = None
    address: Optional[str] = None
    gps: Optional[str] = None
    location_id: int
    partners_ids: List[int]

class NetworkSiteCreate(NetworkSiteBase):
    pass

class NetworkSiteUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    gps: Optional[str] = None
    location_id: Optional[int] = None
    partners_ids: Optional[List[int]] = None

class NetworkSiteResponse(NetworkSiteBase):
    id: int
    location: LocationResponse
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PaginatedNetworkSiteResponse(BaseModel):
    total: int
    items: List[NetworkSiteResponse]

# --- Monitoring Device Schemas ---
class MonitoringDeviceBase(BaseModel):
    title: str
    ip: str
    network_site_id: Optional[int] = None
    producer_id: int
    model: Optional[str] = None
    active: bool = True
    type_id: int
    monitoring_group_id: int
    partners_ids: List[int]
    location_id: int

class MonitoringDeviceCreate(MonitoringDeviceBase):
    pass

class MonitoringDeviceUpdate(BaseModel):
    title: Optional[str] = None
    ip: Optional[str] = None
    network_site_id: Optional[int] = None
    producer_id: Optional[int] = None
    model: Optional[str] = None
    active: Optional[bool] = None
    type_id: Optional[int] = None
    monitoring_group_id: Optional[int] = None
    partners_ids: Optional[List[int]] = None
    location_id: Optional[int] = None
    snmp_port: Optional[int] = None
    is_ping: Optional[bool] = None
    snmp_community: Optional[str] = None
    snmp_version: Optional[int] = None
    send_notifications: Optional[bool] = None
    delay_timer: Optional[int] = None
    access_device: Optional[bool] = None

class MonitoringDeviceResponse(MonitoringDeviceBase):
    id: int
    ping_state: str
    snmp_state: str
    network_site: Optional[NetworkSiteResponse] = None
    producer: NetworkLookupResponse
    device_type: NetworkLookupResponse
    monitoring_group: NetworkLookupResponse
    location: LocationResponse
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PaginatedMonitoringDeviceResponse(BaseModel):
    total: int
    items: List[MonitoringDeviceResponse]

# --- Router (NAS) Schemas ---

class RouterBase(BaseModel):
    title: str
    ip: str
    location_id: int
    nas_type: int
    partners_ids: List[int] = []
    model: Optional[str] = None
    radius_secret: Optional[str] = None
    api_login: Optional[str] = None
    api_password: Optional[str] = None
    api_port: Optional[int] = 8728
    api_enable: Optional[bool] = False

class RouterCreate(RouterBase):
    pass

class RouterUpdate(BaseModel):
    title: Optional[str] = None
    ip: Optional[str] = None
    location_id: Optional[int] = None
    nas_type: Optional[int] = None
    partners_ids: Optional[List[int]] = None
    model: Optional[str] = None
    radius_secret: Optional[str] = None
    api_login: Optional[str] = None
    api_password: Optional[str] = None
    api_port: Optional[int] = None
    api_enable: Optional[bool] = None
    address: Optional[str] = None
    gps: Optional[str] = None
    gps_point: Optional[str] = None
    authorization_method: Optional[str] = None
    accounting_method: Optional[str] = None
    nas_ip: Optional[str] = None
    pool_ids: Optional[List[int]] = None
    shaper: Optional[bool] = None
    shaper_id: Optional[int] = None
    shaping_type: Optional[str] = None
    version: Optional[str] = None
    board_name: Optional[str] = None

class RouterResponse(RouterBase):
    id: int
    status: str
    version: Optional[str] = None
    board_name: Optional[str] = None
    cpu_usage: Optional[int] = None
    last_connect: Optional[datetime] = None
    location: LocationResponse
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedRouterResponse(BaseModel):
    total: int
    items: List[RouterResponse]

# --- RADIUS Session Schemas (unchanged) ---
class RadiusSessionResponse(BaseModel):
    id: int
    session_id: Optional[str] = None
    login: str
    username_real: Optional[str] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = None
    in_bytes: int
    out_bytes: int
    start_session: datetime
    end_session: Optional[datetime] = None
    session_status: str
    terminate_cause: Optional[str] = None
    time_on: Optional[int] = 0
    price: Optional[Decimal] = Decimal('0.0')
    customer: Optional[CustomerResponse] = None
    service: Optional[InternetServiceResponse] = None
    nas: Optional[RouterResponse] = None
    model_config = ConfigDict(from_attributes=True)

class PaginatedRadiusSessionResponse(BaseModel):
    total: int
    items: List[RadiusSessionResponse]

class CustomerOnlineBase(BaseModel):
    customer_id: int
    service_id: Optional[int] = None
    tariff_id: Optional[int] = None
    partner_id: Optional[int] = None
    nas_id: Optional[int] = None
    login: str
    username_real: Optional[str] = None
    in_bytes: int = 0
    out_bytes: int = 0
    start_session: datetime
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = None
    session_id: Optional[str] = None

class CustomerOnlineResponse(CustomerOnlineBase):
    id: int
    last_change: datetime
    model_config = ConfigDict(from_attributes=True)

class CustomerOnlineStatus(BaseModel):
    customer_id: int
    customer_name: str
    service_description: Optional[str] = None
    login: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    session_start_time: datetime
    session_time: float
    data_uploaded_mb: float
    data_downloaded_mb: float


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
    note: Optional[str] = None

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
    date_created: date
    total: Decimal
    due: Decimal
    items: List[InvoiceItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

class PaginatedInvoiceResponse(BaseModel):
    total: int
    items: List[InvoiceResponse]

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    memo: Optional[str] = None
    items: Optional[List[InvoiceItemCreate]] = None

class PaymentUpdate(BaseModel):
    receipt_number: Optional[str] = None
    date: Optional[date] = None
    comment: Optional[str] = None

class PaymentBase(BaseModel):
    customer_id: int
    invoice_id: Optional[int] = None
    payment_type_id: int
    receipt_number: str
    amount: Decimal
    date: date
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
class PaymentMethodBase(BaseModel):
    name: str
    is_active: bool = True
    name_1: Optional[str] = None
    name_2: Optional[str] = None
    name_3: Optional[str] = None
    name_4: Optional[str] = None
    name_5: Optional[str] = None

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class PaymentMethodResponse(PaymentMethodBase):
    id: int
    created_at: datetime
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

class TicketGroupUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

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

class TicketTypeUpdate(BaseModel):
    title: Optional[str] = None
    background_color: Optional[str] = None

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
    attachments: List['TicketFileAttachmentResponse'] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Ticket File Attachment Schemas ---
class TicketFileAttachmentBase(BaseModel):
    ticket_id: int
    message_id: Optional[int] = None
    file_id: int
    attachment_type: str = 'customer_upload'
    is_internal: bool = False

class TicketFileAttachmentCreate(TicketFileAttachmentBase):
    pass

class TicketFileAttachmentResponse(TicketFileAttachmentBase):
    id: int
    created_at: datetime
    file: 'FileStorageResponse'
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

# =============================================================================
# SLA MANAGEMENT SCHEMAS
# =============================================================================

class SLAViolationBase(BaseModel):
    customer_id: int
    service_id: Optional[int] = None
    service_type: Optional[str] = None
    ticket_id: Optional[int] = None
    violation_type: str
    violation_start: datetime
    violation_end: Optional[datetime] = None
    sla_target: Optional[int] = None
    actual_value: Optional[int] = None
    credit_amount: Decimal = Decimal('0.00')
    credit_note_id: Optional[int] = None
    status: str = 'pending'

class SLAViolationCreate(SLAViolationBase):
    pass

class SLAViolationResponse(SLAViolationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SLACreditReviewBase(BaseModel):
    violation_id: int
    review_status: str = 'pending'
    assigned_reviewer: Optional[int] = None
    review_priority: str = 'normal'
    auto_calculated_credit: Decimal
    reviewer_recommended_credit: Optional[Decimal] = None
    final_approved_credit: Optional[Decimal] = None
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    requires_manager_approval: bool = False
    manager_approved_by: Optional[int] = None
    manager_approval_notes: Optional[str] = None
    customer_notified: bool = False
    customer_dispute: bool = False
    customer_dispute_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    review_started_at: Optional[datetime] = None
    review_completed_at: Optional[datetime] = None
    credit_applied_at: Optional[datetime] = None

class SLACreditReviewCreate(SLACreditReviewBase):
    pass

class SLACreditReviewResponse(SLACreditReviewBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SLACreditWorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    min_credit_amount: Decimal = Decimal('0.00')
    max_auto_approve_amount: Decimal = Decimal('0.00')
    violation_types: Optional[List[str]] = None
    customer_tiers: Optional[List[str]] = None
    requires_l1_approval: bool = False
    requires_l2_approval: bool = False
    requires_manager_approval: bool = False
    default_reviewer_group: Optional[int] = None
    escalation_reviewer_group: Optional[int] = None
    is_active: bool = True

class SLACreditWorkflowCreate(SLACreditWorkflowBase):
    pass

class SLACreditWorkflowResponse(SLACreditWorkflowBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# BILLING & FINANCIAL SCHEMAS
# =============================================================================

class TransactionBase(BaseModel):
    type: str
    customer_id: int
    price: Decimal
    total: Decimal
    date: date
    category_id: int
    description: Optional[str] = None
    quantity: int = 1
    unit: Optional[str] = None
    tax_id: Optional[int] = None
    service_id: Optional[int] = None
    service_type: Optional[str] = None
    invoice_id: Optional[int] = None
    comment: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CreditNoteItemBase(BaseModel):
    description: str
    quantity: int = 1
    price: Decimal
    tax: Decimal = Decimal("0.00")

class CreditNoteItemCreate(CreditNoteItemBase):
    pass

class CreditNoteItemResponse(CreditNoteItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CreditNoteBase(BaseModel):
    customer_id: int
    status: str = 'not_refunded'
    note: Optional[str] = None

class CreditNoteCreate(CreditNoteBase):
    items: List[CreditNoteItemCreate]

class CreditNoteResponse(CreditNoteBase):
    id: int
    number: str
    date_created: date
    total: Decimal
    items: List[CreditNoteItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

class ProformaInvoiceItemBase(BaseModel):
    description: str
    quantity: int = 1
    price: Decimal
    tax: Decimal = Decimal("0.00")

class ProformaInvoiceItemCreate(ProformaInvoiceItemBase):
    pass

class ProformaInvoiceItemResponse(ProformaInvoiceItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ProformaInvoiceBase(BaseModel):
    customer_id: int
    status: str = 'not_paid'

class ProformaInvoiceCreate(ProformaInvoiceBase):
    items: List[ProformaInvoiceItemCreate]

class ProformaInvoiceResponse(ProformaInvoiceBase):
    id: int
    number: str
    date_created: date
    total: Decimal
    items: List[ProformaInvoiceItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

class AdditionalDiscountBase(BaseModel):
    service_type: str
    service_id: int
    enabled: bool = True
    percent: Decimal
    start_date: date
    end_date: Optional[date] = None
    message: Optional[str] = None

class AdditionalDiscountCreate(AdditionalDiscountBase):
    pass

class AdditionalDiscountResponse(AdditionalDiscountBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

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

# =============================================================================
# ACCOUNTING SCHEMAS
# =============================================================================

class AccountingCategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    type: str
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True

class AccountingCategoryCreate(AccountingCategoryBase):
    pass

class AccountingCategoryResponse(AccountingCategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class JournalEntryLineBase(BaseModel):
    account_category_id: int
    debit: Decimal = Decimal('0.00')
    credit: Decimal = Decimal('0.00')
    description: Optional[str] = None

class JournalEntryLineCreate(JournalEntryLineBase):
    pass

class JournalEntryLineResponse(JournalEntryLineBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class JournalEntryBase(BaseModel):
    entry_date: date
    description: str
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    status: str = 'posted'
    created_by: Optional[int] = None # Administrator ID

class JournalEntryCreate(JournalEntryBase):
    lines: List[JournalEntryLineCreate]

class JournalEntryResponse(JournalEntryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    lines: List[JournalEntryLineResponse] = []
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# VOICE CDR SCHEMAS
# =============================================================================

class VoiceCDRBase(BaseModel):
    customer_id: Optional[int] = None
    service_id: Optional[int] = None
    call_date: datetime
    call_type: str
    source: str
    destination: str
    duration: int
    billable_duration: int
    cost: Decimal = Decimal('0.00')
    rate_per_minute: Decimal = Decimal('0.00')
    destination_type: Optional[str] = None
    termination_cause: Optional[str] = None
    quality_score: Optional[Decimal] = None

class VoiceCDRCreate(VoiceCDRBase):
    pass

class VoiceCDRResponse(VoiceCDRBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VoiceCDRSummaryBase(BaseModel):
    customer_id: int
    service_id: Optional[int] = None
    summary_date: date
    total_calls: int = 0
    total_duration: int = 0
    total_cost: Decimal = Decimal('0.00')
    inbound_calls: int = 0
    outbound_calls: int = 0

class VoiceCDRSummaryCreate(VoiceCDRSummaryBase):
    pass

class VoiceCDRSummaryResponse(VoiceCDRSummaryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# SCHEDULING & JOBS SCHEMAS
# =============================================================================

class JobExecutionHistoryBase(BaseModel):
    job_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    output: Optional[str] = None
    error_message: Optional[str] = None
    records_processed: int = 0

class JobExecutionHistoryResponse(JobExecutionHistoryBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ScheduledJobBase(BaseModel):
    job_name: str
    job_type: str
    description: Optional[str] = None
    schedule_cron: Optional[str] = None
    status: str = 'active'
    configuration: Dict[str, Any] = {}
    retry_on_failure: bool = True
    max_retries: int = 3

class ScheduledJobCreate(ScheduledJobBase):
    pass

class ScheduledJobUpdate(BaseModel):
    job_name: Optional[str] = None
    description: Optional[str] = None
    schedule_cron: Optional[str] = None
    status: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    retry_on_failure: Optional[bool] = None
    max_retries: Optional[int] = None

class ScheduledJobResponse(ScheduledJobBase):
    id: int
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    last_duration_seconds: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    history: List[JobExecutionHistoryResponse] = []
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# RESELLER MANAGEMENT SCHEMAS
# =============================================================================

class ResellerBase(BaseModel):
    code: str
    name: str
    parent_reseller_id: Optional[int] = None
    status: str = 'active'
    contact_person: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    default_markup_percent: Decimal = Decimal('0.00')
    commission_percent: Decimal = Decimal('0.00')
    credit_limit: Decimal = Decimal('0.00')
    payment_terms: int = 30
    currency: str = 'USD'
    allowed_services: List[Any] = []
    max_customers: int = 0
    can_create_sub_resellers: bool = False
    white_label_enabled: bool = False
    logo_url: Optional[str] = None
    brand_name: Optional[str] = None
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = None

class ResellerCreate(ResellerBase):
    pass

class ResellerUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    commission_percent: Optional[Decimal] = None
    white_label_enabled: Optional[bool] = None

class ResellerResponse(ResellerBase):
    id: int
    level: int
    current_balance: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ResellerCustomerBase(BaseModel):
    reseller_id: int
    customer_id: int
    commission_rate: Optional[Decimal] = None
    markup_rate: Optional[Decimal] = None
    notes: Optional[str] = None

class ResellerCustomerCreate(ResellerCustomerBase):
    pass

class ResellerCustomerResponse(ResellerCustomerBase):
    id: int
    assigned_date: date
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResellerPricingBase(BaseModel):
    reseller_id: int
    service_type: str
    tariff_id: int
    markup_type: str = 'percent'
    markup_value: Decimal
    is_active: bool = True

class ResellerPricingCreate(ResellerPricingBase):
    pass

class ResellerPricingResponse(ResellerPricingBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResellerUserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    status: str = 'active'
    password_hash: Optional[str] = None # Should not be exposed in typical responses
    password_salt: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    email_verified: Optional[bool] = None
    email_verification_token: Optional[str] = None
    email_verification_expires: Optional[datetime] = None
    permissions: Optional[List[Any]] = None # JSONB array
    allowed_customer_ids: Optional[List[int]] = None
    ip_whitelist: Optional[List[str]] = None # INET array
    last_login_ip: Optional[str] = None # INET
    current_session_id: Optional[str] = None
    session_expires: Optional[datetime] = None
    concurrent_sessions_allowed: Optional[int] = None
    two_factor_enabled: Optional[bool] = None
    two_factor_secret: Optional[str] = None
    failed_login_attempts: Optional[int] = None
    locked_until: Optional[datetime] = None
    role: str = 'user'

class ResellerUserCreate(ResellerUserBase):
    password: str
    reseller_id: int

class ResellerUserResponse(ResellerUserBase):
    id: int
    reseller_id: int
    force_password_change: Optional[bool] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    date_format: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    created_by: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# WEBHOOKS SCHEMAS
# =============================================================================

class WebhookEventBase(BaseModel):
    webhook_config_id: int
    event_type: str
    payload: Dict[str, Any]
    status: str = 'pending'
    attempt_count: int = 0
    last_attempt_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None

class WebhookEventCreate(WebhookEventBase):
    pass

class WebhookEventResponse(WebhookEventBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WebhookConfigBase(BaseModel):
    name: str
    event_type: str
    url: str
    secret: Optional[str] = None
    headers: Dict[str, Any] = {}
    is_active: bool = True
    retry_count: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 30

class WebhookConfigCreate(WebhookConfigBase):
    pass

class WebhookConfigUpdate(BaseModel):
    name: Optional[str] = None
    event_type: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class WebhookConfigResponse(WebhookConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# COMMUNICATIONS SCHEMAS
# =============================================================================

class CommunicationTemplateBase(BaseModel):
    name: str
    template_code: str
    template_type: str
    category: str
    description: Optional[str] = None
    subcategory: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: str
    html_template: Optional[str] = None

class CommunicationTemplateCreate(CommunicationTemplateBase):
    pass

class CommunicationTemplateResponse(CommunicationTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class MessageQueueBase(BaseModel):
    recipient_type: str
    recipient_id: int
    channel: str
    template_id: Optional[int] = None
    subject: Optional[str] = None
    body: str
    variables: Dict[str, Any] = {}
    priority: int = 5
    scheduled_for: Optional[datetime] = None
    status: str = 'queued'

class MessageQueueCreate(MessageQueueBase):
    pass

class MessageQueueResponse(MessageQueueBase):
    id: int
    attempts: int
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    provider_message_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# BULK OPERATIONS SCHEMAS
# =============================================================================

class BulkOperationDetailBase(BaseModel):
    record_index: int
    record_identifier: Optional[str] = None
    operation_action: Optional[str] = None
    status: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    warning_message: Optional[str] = None

class BulkOperationDetailResponse(BulkOperationDetailBase):
    id: int
    bulk_operation_id: int
    processed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BulkOperationBase(BaseModel):
    operation_type: str
    operation_name: str
    target_table: Optional[str] = None
    operation_mode: Optional[str] = None
    dry_run: bool = False
    rollback_on_failure: bool = False
    send_completion_notification: bool = True
    notification_email: Optional[EmailStr] = None

class BulkOperationCreate(BulkOperationBase):
    input_source: Optional[str] = None
    input_file_path: Optional[str] = None
    input_data: Optional[List[Dict[str, Any]]] = None
    validation_rules: Dict[str, Any] = {}

class BulkOperationUpdate(BaseModel):
    status: Optional[str] = None

class BulkOperationResponse(BulkOperationBase):
    id: int
    initiated_by: Optional[int] = None
    status: str
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    skipped_records: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
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

class CustomerStatisticBase(BaseModel):
    customer_id: int
    service_id: Optional[int] = None
    tariff_id: Optional[int] = None
    partner_id: Optional[int] = None
    nas_id: Optional[int] = None
    login: Optional[str] = None
    in_bytes: int = 0
    out_bytes: int = 0
    start_date: Optional[date] = None
    start_time: Optional[time] = None
    end_date: Optional[date] = None
    end_time: Optional[time] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = None
    call_to: Optional[str] = None
    port: Optional[str] = None
    error: int = 0
    error_repeat: int = 0
    price: Decimal = Decimal('0.0')
    session_id: Optional[str] = None
    terminate_cause: Optional[str] = None

class CustomerStatisticResponse(CustomerStatisticBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SystemConfigBase(BaseModel):
    module: str
    path: str
    key: str
    value: Optional[str] = None
    partner_id: Optional[int] = None

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: Optional[str] = None

class SystemConfigResponse(SystemConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# COMMUNICATION TEMPLATES SCHEMAS
# =============================================================================

class CommunicationTemplateBase(BaseModel):
    name: str
    template_code: str
    template_type: str
    category: str
    description: Optional[str] = None
    subcategory: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: str
    html_template: Optional[str] = None
    available_variables: List[Any] = []
    required_variables: List[Any] = []
    variable_descriptions: Dict[str, Any] = {}
    language: str = 'en'
    is_default_language: bool = False
    parent_template_id: Optional[int] = None
    customer_segments: List[Any] = []
    trigger_conditions: Dict[str, Any] = {}
    priority: int = 0
    format_type: str = 'text'
    delivery_timing: str = 'immediate'
    throttle_limit: int = 0
    is_ab_test: bool = False
    ab_test_group: Optional[str] = None
    ab_test_weight: int = 100
    ab_test_ends_at: Optional[datetime] = None
    status: str = 'draft'
    requires_approval: bool = False
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    usage_count: int = 0
    last_used: Optional[datetime] = None
    success_rate: Decimal = Decimal('0.00')
    open_rate: Decimal = Decimal('0.00')
    click_rate: Decimal = Decimal('0.00')
    version_number: int = 1
    is_active: bool = True
    replaced_by: Optional[int] = None
    gdpr_compliant: bool = True
    retention_period: int = 365

class CommunicationTemplateCreate(CommunicationTemplateBase):
    pass

class CommunicationTemplateResponse(CommunicationTemplateBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# FILE STORAGE SYSTEM SCHEMAS
# =============================================================================

class StorageProviderBase(BaseModel):
    name: str
    provider_type: str
    endpoint_url: Optional[str] = None
    region: Optional[str] = None
    access_key_id: Optional[str] = None
    bucket_name: str
    base_path: str = ''
    is_default: bool = False
    is_active: bool = True

class StorageProviderCreate(StorageProviderBase):
    secret_access_key_encrypted: Optional[str] = None # Should be handled securely

class StorageProviderResponse(StorageProviderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class FileStorageBase(BaseModel):
    original_filename: str
    stored_filename: str
    mime_type: Optional[str] = None
    file_size: int
    storage_provider_id: int
    bucket_name: str
    storage_path: str
    file_category: Optional[str] = None
    file_purpose: Optional[str] = None
    owner_type: Optional[str] = None
    owner_id: Optional[int] = None

class FileStorageCreate(FileStorageBase):
    pass

class FileStorageResponse(FileStorageBase):
    id: int
    file_uuid: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    storage_url: Optional[str] = None
    cdn_url: Optional[str] = None
    is_public: bool
    download_count: int
    last_accessed: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class FileAccessLogBase(BaseModel):
    file_id: int
    access_type: str
    accessor_type: Optional[str] = None
    accessor_id: Optional[int] = None
    ip_address: Optional[str] = None

class FileAccessLogCreate(FileAccessLogBase):
    pass

class FileAccessLogResponse(FileAccessLogBase):
    id: int
    accessed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FileShareBase(BaseModel):
    file_id: int
    share_type: str = 'temporary'
    expires_at: Optional[datetime] = None
    max_downloads: int = 1

class FileShareCreate(FileShareBase):
    password: Optional[str] = None # For password_protected type

class FileShareResponse(FileShareBase):
    id: int
    share_token: UUID
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentTemplateBase(BaseModel):
    name: str
    template_type: str
    description: Optional[str] = None
    template_file_id: Optional[int] = None
    variables: List[Any] = []
    output_format: str = 'pdf'
    is_active: bool = True

class DocumentTemplateCreate(DocumentTemplateBase):
    pass

class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class GeneratedDocumentBase(BaseModel):
    template_id: Optional[int] = None
    generated_file_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

class GeneratedDocumentCreate(GeneratedDocumentBase):
    pass

class GeneratedDocumentResponse(GeneratedDocumentBase):
    id: int
    generation_status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# SPECIFIC FILE ASSOCIATIONS SCHEMAS
# =============================================================================

class CustomerDocumentBase(BaseModel):
    customer_id: int
    file_id: int
    document_type: str
    title: str
    description: Optional[str] = None
    status: str = 'uploaded'
    visible_to_customer: bool = True

class CustomerDocumentCreate(CustomerDocumentBase):
    pass

class CustomerDocumentResponse(CustomerDocumentBase):
    id: int
    file: FileStorageResponse
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class FinancialDocumentFileBase(BaseModel):
    document_type: str
    document_id: int
    file_id: int
    is_original: bool = True

class FinancialDocumentFileCreate(FinancialDocumentFileBase):
    pass

class FinancialDocumentFileResponse(FinancialDocumentFileBase):
    id: int
    file: FileStorageResponse
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Rebuild forward-referencing models
FileStorageResponse.model_rebuild()
TicketFileAttachmentResponse.model_rebuild()
DocumentTemplateResponse.model_rebuild()
GeneratedDocumentResponse.model_rebuild()
CustomerDocumentResponse.model_rebuild()
FinancialDocumentFileResponse.model_rebuild()

TicketMessageResponse.model_rebuild()
# =============================================================================
# DATA MIGRATION SCHEMAS
# =============================================================================

class MigrationMappingBase(BaseModel):
    migration_id: int
    source_table: str
    source_id: str
    target_table: str
    target_id: int

class MigrationMappingCreate(MigrationMappingBase):
    pass

class MigrationMappingResponse(MigrationMappingBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MigrationStatusBase(BaseModel):
    source_system: str
    migration_type: str
    status: str = 'pending'
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    error_log: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class MigrationStatusCreate(MigrationStatusBase):
    pass

class MigrationStatusResponse(MigrationStatusBase):
    id: int
    created_at: datetime
    mappings: List[MigrationMappingResponse] = []
    model_config = ConfigDict(from_attributes=True)

MigrationStatusResponse.model_rebuild()


# =============================================================================
# FRAMEWORK - DYNAMIC ENTITY BUILDER SCHEMAS
# =============================================================================

class FrameworkFieldBase(BaseModel):
    field_name: str
    display_name: str
    field_type: str
    field_config: Dict[str, Any] = {}
    validation_rules: Dict[str, Any] = {}
    default_value: Optional[str] = None
    is_required: bool = False
    is_unique: bool = False

class FrameworkFieldCreate(FrameworkFieldBase):
    pass

class FrameworkFieldResponse(FrameworkFieldBase):
    id: int
    entity_id: int
    model_config = ConfigDict(from_attributes=True)

class FrameworkEntityBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    table_name: Optional[str] = None
    icon: str = 'fa-table'
    color: str = '#357bf2'
    schema_: Dict[str, Any]

class FrameworkEntityCreate(FrameworkEntityBase):
    pass

class FrameworkEntityResponse(FrameworkEntityBase):
    id: int
    fields: List[FrameworkFieldResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class FrameworkEntityDataBase(BaseModel):
    entity_id: int
    record_id: int
    field_id: int
    value_text: Optional[str] = None
    value_number: Optional[Decimal] = None
    value_date: Optional[date] = None
    value_datetime: Optional[datetime] = None
    value_boolean: Optional[bool] = None
    value_json: Optional[Dict[str, Any]] = None

class FrameworkEntityDataCreate(FrameworkEntityDataBase):
    pass

class FrameworkEntityDataResponse(FrameworkEntityDataBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
class TemplateUsageLogBase(BaseModel):
    template_id: int
    delivery_type: str
    recipient_type: Optional[str] = None
    recipient_id: Optional[int] = None
    recipient_address: Optional[str] = None
    final_subject: Optional[str] = None
    final_body: Optional[str] = None
    variables_used: Optional[Dict[str, Any]] = None
    delivery_status: str = 'pending'
    delivery_provider: Optional[str] = None
    delivery_provider_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    complaint_at: Optional[datetime] = None
    delivery_attempts: int = 0
    failure_reason: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None
    business_context: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class TemplateUsageLogCreate(TemplateUsageLogBase):
    pass

class TemplateUsageLogResponse(TemplateUsageLogBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TemplateABTestResultBase(BaseModel):
    template_id: int
    test_group: str
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_complaints: int = 0
    delivery_rate: Decimal = Decimal('0.00')
    open_rate: Decimal = Decimal('0.00')
    click_rate: Decimal = Decimal('0.00')
    bounce_rate: Decimal = Decimal('0.00')
    complaint_rate: Decimal = Decimal('0.00')
    is_statistically_significant: bool = False
    confidence_level: Decimal = Decimal('0.00')
    winner_declared: bool = False
    test_period_start: Optional[datetime] = None
    test_period_end: Optional[datetime] = None
    last_calculated: Optional[datetime] = None

class TemplateABTestResultCreate(TemplateABTestResultBase):
    pass

class TemplateABTestResultResponse(TemplateABTestResultBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OpportunityConvert(BaseModel):
    """Schema for converting an opportunity to a customer."""
    # We can reuse the CustomerCreate schema but might want to simplify it
    # for the conversion process, as some data comes from the lead.
    login: str
    partner_id: int
    location_id: int
    billing_config: Optional[CustomerBillingBase] = None


# =============================================================================
# NETWORK MANAGEMENT SCHEMAS
# =============================================================================

# SNMP Monitoring Schemas
class SNMPMonitoringProfileBase(BaseModel):
    device_id: int
    snmp_version: str = '2c'
    community_string: Optional[str] = None
    username: Optional[str] = None
    auth_protocol: Optional[str] = None
    auth_password: Optional[str] = None
    priv_protocol: Optional[str] = None
    priv_password: Optional[str] = None
    polling_interval: int = 300  # seconds
    is_active: bool = True
    oids_to_monitor: Dict[str, Any] = {}
    thresholds: Dict[str, Any] = {}

class SNMPMonitoringProfileCreate(SNMPMonitoringProfileBase):
    pass

class SNMPMonitoringProfileUpdate(BaseModel):
    snmp_version: Optional[str] = None
    community_string: Optional[str] = None
    username: Optional[str] = None
    auth_protocol: Optional[str] = None
    auth_password: Optional[str] = None
    priv_protocol: Optional[str] = None
    priv_password: Optional[str] = None
    polling_interval: Optional[int] = None
    is_active: Optional[bool] = None
    oids_to_monitor: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None

class SNMPMonitoringProfileResponse(SNMPMonitoringProfileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SNMPMonitoringDataBase(BaseModel):
    profile_id: int
    oid: str
    value: str
    value_type: str = 'string'
    timestamp: datetime
    status: str = 'success'
    error_message: Optional[str] = None

class SNMPMonitoringDataCreate(SNMPMonitoringDataBase):
    pass

class SNMPMonitoringDataResponse(SNMPMonitoringDataBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Bandwidth Management & QoS Schemas
class QoSPolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    policy_type: str = 'rate_limit'  # rate_limit, priority, shaping
    upload_rate_kbps: Optional[int] = None
    download_rate_kbps: Optional[int] = None
    burst_upload_kbps: Optional[int] = None
    burst_download_kbps: Optional[int] = None
    priority: int = 0
    dscp_marking: Optional[str] = None
    traffic_class: Optional[str] = None
    policy_rules: Dict[str, Any] = {}
    is_active: bool = True

class QoSPolicyCreate(QoSPolicyBase):
    pass

class QoSPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    policy_type: Optional[str] = None
    upload_rate_kbps: Optional[int] = None
    download_rate_kbps: Optional[int] = None
    burst_upload_kbps: Optional[int] = None
    burst_download_kbps: Optional[int] = None
    priority: Optional[int] = None
    dscp_marking: Optional[str] = None
    traffic_class: Optional[str] = None
    policy_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class QoSPolicyResponse(QoSPolicyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class DeviceQoSAssignmentBase(BaseModel):
    device_id: int
    qos_policy_id: int
    applied_at: Optional[datetime] = None
    is_active: bool = True
    application_status: str = 'pending'  # pending, applied, failed
    error_message: Optional[str] = None

class DeviceQoSAssignmentCreate(DeviceQoSAssignmentBase):
    pass

class DeviceQoSAssignmentUpdate(BaseModel):
    qos_policy_id: Optional[int] = None
    is_active: Optional[bool] = None
    application_status: Optional[str] = None
    error_message: Optional[str] = None

class DeviceQoSAssignmentResponse(DeviceQoSAssignmentBase):
    id: int
    qos_policy: QoSPolicyResponse
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class BandwidthUsageLogBase(BaseModel):
    device_id: int
    timestamp: datetime
    upload_bytes: int = 0
    download_bytes: int = 0
    upload_packets: int = 0
    download_packets: int = 0
    session_duration: int = 0  # seconds
    peak_upload_rate: Optional[int] = None  # kbps
    peak_download_rate: Optional[int] = None  # kbps
    qos_violations: int = 0
    data_source: str = 'radius'  # radius, snmp, netflow, api

class BandwidthUsageLogCreate(BandwidthUsageLogBase):
    pass

class BandwidthUsageLogResponse(BandwidthUsageLogBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Network Topology Schemas
class NetworkTopologyBase(BaseModel):
    device_id: int
    device_name: str
    device_type: str = 'router'  # router, switch, ap, gateway
    ip_address: str
    mac_address: Optional[str] = None
    location: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None  # lat, lng for mapping
    vendor: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    status: str = 'unknown'  # online, offline, unreachable, maintenance
    last_seen: Optional[datetime] = None
    discovery_method: str = 'manual'  # manual, snmp, cdp, lldp
    parent_device_id: Optional[int] = None
    metadata: Dict[str, Any] = {}

class NetworkTopologyCreate(NetworkTopologyBase):
    pass

class NetworkTopologyUpdate(BaseModel):
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    location: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[str] = None
    last_seen: Optional[datetime] = None
    discovery_method: Optional[str] = None
    parent_device_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class NetworkTopologyResponse(NetworkTopologyBase):
    id: int
    connections: List['NetworkConnectionResponse'] = []
    child_devices: List['NetworkTopologyResponse'] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class NetworkConnectionBase(BaseModel):
    source_device_id: int
    target_device_id: int
    source_interface: Optional[str] = None
    target_interface: Optional[str] = None
    connection_type: str = 'ethernet'  # ethernet, fiber, wireless, vpn
    bandwidth_mbps: Optional[int] = None
    duplex: str = 'full'  # full, half
    vlan_id: Optional[int] = None
    status: str = 'up'  # up, down, degraded
    discovery_method: str = 'manual'  # manual, cdp, lldp, snmp
    connection_cost: int = 1  # for routing calculations
    metadata: Dict[str, Any] = {}

class NetworkConnectionCreate(NetworkConnectionBase):
    pass

class NetworkConnectionUpdate(BaseModel):
    source_interface: Optional[str] = None
    target_interface: Optional[str] = None
    connection_type: Optional[str] = None
    bandwidth_mbps: Optional[int] = None
    duplex: Optional[str] = None
    vlan_id: Optional[int] = None
    status: Optional[str] = None
    discovery_method: Optional[str] = None
    connection_cost: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class NetworkConnectionResponse(NetworkConnectionBase):
    id: int
    source_device: NetworkTopologyResponse
    target_device: NetworkTopologyResponse
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# Fault Management Schemas
class NetworkIncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = 'low'  # critical, high, medium, low
    status: str = 'open'  # open, investigating, resolved, closed
    incident_type: str = 'connectivity'  # connectivity, performance, security, configuration
    affected_devices: List[int] = []  # device IDs
    affected_services: List[str] = []  # service names
    source: str = 'manual'  # manual, monitoring, customer_report, automated
    assigned_to: Optional[int] = None  # user ID
    escalation_level: int = 0
    business_impact: str = 'low'  # critical, high, medium, low
    priority: int = 3  # 1 (highest) to 5 (lowest)
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    estimated_resolution: Optional[datetime] = None
    downtime_minutes: Optional[int] = None
    customer_impact: bool = False
    external_ticket_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class NetworkIncidentCreate(NetworkIncidentBase):
    pass

class NetworkIncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    incident_type: Optional[str] = None
    affected_devices: Optional[List[int]] = None
    affected_services: Optional[List[str]] = None
    assigned_to: Optional[int] = None
    escalation_level: Optional[int] = None
    business_impact: Optional[str] = None
    priority: Optional[int] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    estimated_resolution: Optional[datetime] = None
    downtime_minutes: Optional[int] = None
    customer_impact: Optional[bool] = None
    external_ticket_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class NetworkIncidentResponse(NetworkIncidentBase):
    id: int
    incident_number: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    updates: List['IncidentUpdateResponse'] = []
    alerts: List['AutomatedAlertResponse'] = []
    model_config = ConfigDict(from_attributes=True)

class IncidentUpdateBase(BaseModel):
    incident_id: int
    update_type: str = 'comment'  # comment, status_change, assignment, escalation
    content: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    is_internal: bool = False
    created_by: Optional[int] = None  # user ID
    notification_sent: bool = False

class IncidentUpdateCreate(IncidentUpdateBase):
    pass

class IncidentUpdateResponse(IncidentUpdateBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AutomatedAlertBase(BaseModel):
    alert_name: str
    alert_type: str = 'threshold'  # threshold, availability, performance, security
    trigger_condition: Dict[str, Any] = {}
    device_id: Optional[int] = None
    service_name: Optional[str] = None
    metric_name: Optional[str] = None
    threshold_value: Optional[Decimal] = None
    comparison_operator: str = 'greater_than'  # greater_than, less_than, equals, not_equals
    current_value: Optional[Decimal] = None
    severity: str = 'medium'  # critical, high, medium, low
    status: str = 'active'  # active, acknowledged, resolved, suppressed
    first_triggered: datetime
    last_triggered: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None  # user ID
    resolution_time: Optional[datetime] = None
    escalation_count: int = 0
    incident_id: Optional[int] = None
    notification_channels: List[str] = []  # email, sms, webhook, slack
    metadata: Dict[str, Any] = {}

class AutomatedAlertCreate(AutomatedAlertBase):
    pass

class AutomatedAlertUpdate(BaseModel):
    status: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    resolution_time: Optional[datetime] = None
    incident_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class AutomatedAlertResponse(AutomatedAlertBase):
    id: int
    alert_history: List['AlertHistoryResponse'] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AlertHistoryBase(BaseModel):
    alert_id: int
    action: str = 'triggered'  # triggered, acknowledged, resolved, escalated, suppressed
    performed_by: Optional[int] = None  # user ID
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    notes: Optional[str] = None
    notification_sent: bool = False
    notification_channels: List[str] = []

class AlertHistoryCreate(AlertHistoryBase):
    pass

class AlertHistoryResponse(AlertHistoryBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# Performance Analytics Schemas
class PerformanceMetricBase(BaseModel):
    metric_name: str
    metric_type: str = 'gauge'  # gauge, counter, histogram, summary
    description: Optional[str] = None
    unit: Optional[str] = None
    category: str = 'network'  # network, device, service, application
    collection_method: str = 'snmp'  # snmp, netflow, syslog, api
    collection_interval: int = 300  # seconds
    retention_days: int = 365
    aggregation_methods: List[str] = ['avg', 'min', 'max']  # avg, min, max, sum, count
    thresholds: Dict[str, Any] = {}  # warning, critical thresholds
    is_active: bool = True

class PerformanceMetricCreate(PerformanceMetricBase):
    pass

class PerformanceMetricUpdate(BaseModel):
    metric_name: Optional[str] = None
    metric_type: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    collection_method: Optional[str] = None
    collection_interval: Optional[int] = None
    retention_days: Optional[int] = None
    aggregation_methods: Optional[List[str]] = None
    thresholds: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class PerformanceMetricResponse(PerformanceMetricBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PerformanceDataBase(BaseModel):
    metric_id: int
    device_id: Optional[int] = None
    interface_name: Optional[str] = None
    service_name: Optional[str] = None
    timestamp: datetime
    value: Decimal
    aggregation_period: str = 'raw'  # raw, 1m, 5m, 15m, 1h, 1d
    tags: Dict[str, str] = {}  # additional dimensions
    quality: str = 'good'  # good, estimated, bad

class PerformanceDataCreate(PerformanceDataBase):
    pass

class PerformanceDataResponse(PerformanceDataBase):
    id: int
    metric: PerformanceMetricResponse
    model_config = ConfigDict(from_attributes=True)

class PerformanceDashboardBase(BaseModel):
    name: str
    description: Optional[str] = None
    dashboard_type: str = 'network_overview'  # network_overview, device_detail, service_health
    layout_config: Dict[str, Any] = {}  # widget positions, sizes, etc.
    widget_configs: List[Dict[str, Any]] = []  # chart configs, metric selections
    filters: Dict[str, Any] = {}  # default filters
    refresh_interval: int = 60  # seconds
    is_public: bool = False
    created_by: Optional[int] = None  # user ID
    shared_with: List[int] = []  # user IDs

class PerformanceDashboardCreate(PerformanceDashboardBase):
    pass

class PerformanceDashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dashboard_type: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    widget_configs: Optional[List[Dict[str, Any]]] = None
    filters: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = None
    is_public: Optional[bool] = None
    shared_with: Optional[List[int]] = None

class PerformanceDashboardResponse(PerformanceDashboardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# Bulk Operations and Analysis Schemas
class NetworkTopologyAnalysis(BaseModel):
    """Schema for network topology analysis results."""
    total_devices: int
    device_types: Dict[str, int]
    connectivity_matrix: List[List[int]]
    critical_paths: List[Dict[str, Any]]
    redundancy_analysis: Dict[str, Any]
    single_points_of_failure: List[int]  # device IDs
    network_depth: int
    average_hop_count: float
    analysis_timestamp: datetime

class BandwidthUtilizationSummary(BaseModel):
    """Schema for bandwidth utilization summary."""
    device_id: int
    period_start: datetime
    period_end: datetime
    total_upload_gb: Decimal
    total_download_gb: Decimal
    average_upload_mbps: Decimal
    average_download_mbps: Decimal
    peak_upload_mbps: Decimal
    peak_download_mbps: Decimal
    utilization_percentage: Decimal
    qos_violations: int
    cost_analysis: Dict[str, Any]

class IncidentStatistics(BaseModel):
    """Schema for incident statistics and trends."""
    period_start: datetime
    period_end: datetime
    total_incidents: int
    incidents_by_severity: Dict[str, int]
    incidents_by_type: Dict[str, int]
    average_resolution_time: Decimal  # minutes
    mttr_by_severity: Dict[str, Decimal]  # mean time to resolution
    mtbf: Decimal  # mean time between failures
    availability_percentage: Decimal
    top_affected_devices: List[Dict[str, Any]]
    trending_issues: List[Dict[str, Any]]

# Search and Filter Schemas
class NetworkDeviceFilter(BaseModel):
    """Schema for filtering network devices."""
    device_types: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    vendors: Optional[List[str]] = None
    ip_range: Optional[str] = None
    last_seen_after: Optional[datetime] = None
    last_seen_before: Optional[datetime] = None
    has_snmp: Optional[bool] = None
    has_qos: Optional[bool] = None

class PerformanceDataFilter(BaseModel):
    """Schema for filtering performance data."""
    device_ids: Optional[List[int]] = None
    metric_ids: Optional[List[int]] = None
    start_time: datetime
    end_time: datetime
    aggregation_period: Optional[str] = None
    quality_threshold: Optional[str] = None

class IncidentFilter(BaseModel):
    """Schema for filtering incidents."""
    severities: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    incident_types: Optional[List[str]] = None
    assigned_to: Optional[List[int]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    affected_devices: Optional[List[int]] = None
    customer_impact: Optional[bool] = None

# Rebuild forward references for network topology
NetworkTopologyResponse.model_rebuild()
NetworkConnectionResponse.model_rebuild()
NetworkIncidentResponse.model_rebuild()
IncidentUpdateResponse.model_rebuild()
AutomatedAlertResponse.model_rebuild()
AlertHistoryResponse.model_rebuild()

class PaymentGatewayCreate(BaseModel):
    name: str
    is_active: bool = True
    api_key: str
    api_secret: str
    config: dict = {}

class PaymentGatewayUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    config: Optional[dict] = None

class PaymentGatewayResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    api_key: str
    api_secret: str
    config: dict
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)