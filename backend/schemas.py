from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
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

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfileBase(BaseModel):
    customer_id: Optional[int] = None
    reseller_id: Optional[int] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    user_id: int

    class Config:
        from_attributes = True

class PermissionBase(BaseModel):
    code: str
    description: str
    module: str

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

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
    class Config:
        from_attributes = True

class PaginatedAuditLogResponse(BaseModel):
    total: int
    items: List[AuditLogResponse]

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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None # This will need to be updated to use email/user_id

# Renamed existing Permission schemas
class FrameworkPermissionBase(BaseModel):
    code: str # Renamed from name
    description: Optional[str] = None
    module: Optional[str] = None # Added module

class FrameworkPermissionCreate(FrameworkPermissionBase):
    pass

class FrameworkPermissionResponse(FrameworkPermissionBase):
    id: int
    is_system: bool # Added is_system
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Renamed existing Role schemas
class FrameworkRoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class FrameworkRoleCreate(FrameworkRoleBase):
    permission_ids: List[int] = []

class FrameworkRoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class FrameworkRoleResponse(FrameworkRoleBase):
    id: int
    is_system: bool # Added is_system
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[FrameworkPermissionResponse] = []

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class SetupData(BaseModel):
    partner_name: str
    admin_email: EmailStr # Changed from admin_login
    admin_password: str
    admin_full_name: str # Changed from admin_name