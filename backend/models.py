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
    UniqueConstraint
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
    administrator_profile = relationship("Administrator", back_populates="user", uselist=False)
    user_profile = relationship("UserProfile", back_populates="user", uselist=False)
    user_roles = relationship("UserRole", back_populates="user")

class Customer(Base):
    __tablename__ = "customers" # Existing table, adding relationship

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # ... other existing columns ...
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Assuming this exists

    user_profiles = relationship("UserProfile", back_populates="customer")
    user_roles = relationship("UserRole", back_populates="customer")

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
    role_permissions = relationship("RolePermission", back_populates="role")
    user_roles = relationship("UserRole", back_populates="role")

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
