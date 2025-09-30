from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..import crud, schemas, audit
from .v1.deps import get_db

# Data structures for permissions and roles (copied from seed_rbac.py)
permissions_to_seed = [
    # System & Security
    {"code": "system.manage_users", "description": "Create, edit and deactivate users", "module": "system"},
    {"code": "system.manage_roles", "description": "Create and assign roles", "module": "system"},
    {"code": "system.view_audit_logs", "description": "View system audit logs", "module": "system"},
    {"code": "system.configure_security", "description": "Manage security settings (RBAC, MFA, SSO)", "module": "system"},
    {"code": "system.manage_backups", "description": "Manage backups and restores", "module": "system"},

    # CRM
    {"code": "crm.view_accounts", "description": "View accounts/customers", "module": "crm"},
    {"code": "crm.create_accounts", "description": "Create accounts/customers", "module": "crm"},
    {"code": "crm.edit_accounts", "description": "Edit accounts/customers", "module": "crm"},
    {"code": "crm.delete_accounts", "description": "Delete accounts/customers", "module": "crm"},
    {"code": "crm.manage_leads", "description": "Manage CRM leads", "module": "crm"},
    {"code": "crm.manage_opportunities", "description": "Manage CRM opportunities", "module": "crm"},

    # Support
    {"code": "support.view_tickets", "description": "View support tickets", "module": "support"},
    {"code": "support.create_tickets", "description": "Create support tickets", "module": "support"},
    {"code": "support.edit_tickets", "description": "Edit support tickets (comments, status)", "module": "support"},
    {"code": "support.assign_tickets", "description": "Assign tickets to agents", "module": "support"},
    {"code": "support.manage_config", "description": "Manage ticket statuses, types, and groups", "module": "support"},
    {"code": "support.manage_knowledge", "description": "Manage knowledge base", "module": "support"},

    # Billing
    {"code": "billing.view_invoices", "description": "View invoices", "module": "billing"},
    {"code": "billing.create_invoices", "description": "Create invoices", "module": "billing"},
    {"code": "billing.edit_invoices", "description": "Edit invoices", "module": "billing"},
    {"code": "billing.process_payments", "description": "Record/process payments & refunds", "module": "billing"},
    {"code": "billing.manage_tariffs", "description": "Create & update tariff plans", "module": "billing"},
    {"code": "billing.view_financials", "description": "View financial reports", "module": "billing"},

    # Network
    {"code": "network.view_devices", "description": "View network devices and topology", "module": "network"},
    {"code": "network.manage_devices", "description": "Add/edit network devices & config", "module": "network"},
    {"code": "network.manage_ip_pools", "description": "Manage IP pools and assignments", "module": "network"},
    {"code": "network.view_sessions", "description": "View RADIUS/PPP sessions", "module": "network"},
    {"code": "network.disconnect_sessions", "description": "Disconnect/CoA sessions", "module": "network"},

    # Inventory
    {"code": "inventory.view_items", "description": "View inventory items", "module": "inventory"},
    {"code": "inventory.add_items", "description": "Add new inventory items", "module": "inventory"},
    {"code": "inventory.edit_items", "description": "Edit inventory items", "module": "inventory"},
    {"code": "inventory.remove_items", "description": "Remove inventory items", "module": "inventory"},

    # Field Operations
    {"code": "field.view_jobs", "description": "View field jobs/work orders", "module": "field"},
    {"code": "field.assign_jobs", "description": "Assign jobs to technicians", "module": "field"},
    {"code": "field.update_jobs", "description": "Update job progress/results", "module": "field"},

    # Projects
    {"code": "projects.view", "description": "View projects and tasks", "module": "projects"},
    {"code": "projects.manage", "description": "Create/edit projects and tasks", "module": "projects"},

    # Reports
    {"code": "reports.view_usage", "description": "View usage reports", "module": "reports"},
    {"code": "reports.view_network", "description": "View network performance reports", "module": "reports"},
    {"code": "reports.view_financial", "description": "View financial reports", "module": "reports"},

    # Reseller
    {"code": "reseller.view_customers", "description": "View reseller's customers", "module": "reseller"},
    {"code": "reseller.manage_customers", "description": "Create/edit reseller customers", "module": "reseller"},
    {"code": "reseller.assign_tariffs", "description": "Assign tariffs to reseller customers", "module": "reseller"},
    {"code": "reseller.generate_reports", "description": "Generate reports for reseller business", "module": "reseller"}
]

roles_to_seed = [
    {"name": "Super Admin", "description": "Full control of all system functions", "scope": schemas.RoleScope.system, "permissions": []},
    {"name": "System Admin", "description": "Manage system config, network, and security", "scope": schemas.RoleScope.system, "permissions": ["system.manage_users","system.manage_roles","system.view_audit_logs","system.configure_security","system.manage_backups","crm.view_accounts","crm.create_accounts","crm.edit_accounts","crm.delete_accounts","crm.manage_leads","crm.manage_opportunities"]},
    {"name": "Network Engineer", "description": "Manage network infrastructure", "scope": schemas.RoleScope.system, "permissions": ["network.view_devices","network.manage_devices","network.manage_ip_pools","network.view_sessions","network.disconnect_sessions","reports.view_network"]},
    {"name": "Billing Manager", "description": "Manage financials, invoices, tariffs", "scope": schemas.RoleScope.system, "permissions": ["billing.view_invoices","billing.create_invoices","billing.edit_invoices","billing.process_payments","billing.manage_tariffs","reports.view_financial"]},
    {"name": "Support Manager", "description": "Oversee support and SLA", "scope": schemas.RoleScope.system, "permissions": ["support.view_tickets","support.create_tickets","support.edit_tickets","support.assign_tickets","support.manage_knowledge","support.manage_config","crm.view_accounts","reports.view_usage"]},
    {"name": "Support Agent", "description": "Handle support tickets", "scope": schemas.RoleScope.system, "permissions": ["support.view_tickets","support.create_tickets","support.edit_tickets","crm.view_accounts"]},
    {"name": "Field Technician", "description": "Execute on-site jobs", "scope": schemas.RoleScope.system, "permissions": ["field.view_jobs","field.update_jobs","crm.view_accounts","inventory.view_items"]},
    {"name": "Inventory Manager", "description": "Manage stock and device assignments", "scope": schemas.RoleScope.system, "permissions": ["inventory.view_items","inventory.add_items","inventory.edit_items","inventory.remove_items"]},
    {"name": "Project Manager", "description": "Manage internal projects", "scope": schemas.RoleScope.system, "permissions": ["projects.view","projects.manage"]},
    {"name": "Read-Only Staff", "description": "View-only across modules", "scope": schemas.RoleScope.system, "permissions": ["crm.view_accounts","support.view_tickets","billing.view_invoices","network.view_devices","network.view_sessions","inventory.view_items","projects.view","reports.view_usage","reports.view_network","reports.view_financial","system.view_audit_logs"]},
    {"name": "Customer Admin", "description": "Lead contact; manage own account", "scope": schemas.RoleScope.customer, "permissions": ["billing.view_invoices","support.create_tickets","support.view_tickets","reports.view_usage"]},
    {"name": "Customer User", "description": "Sub-user; limited actions", "scope": schemas.RoleScope.customer, "permissions": ["support.create_tickets","support.view_tickets","reports.view_usage"]},
    {"name": "Customer Read-Only", "description": "View-only for invoices/usage", "scope": schemas.RoleScope.customer, "permissions": ["billing.view_invoices","reports.view_usage"]},
    {"name": "Reseller Admin", "description": "Manage reseller business and sub-customers", "scope": schemas.RoleScope.reseller, "permissions": ["reseller.view_customers","reseller.manage_customers","reseller.assign_tariffs","reseller.generate_reports","billing.create_invoices","billing.view_invoices","reports.view_usage","reports.view_financial"]},
    {"name": "Reseller Staff", "description": "Operate on reseller's assigned customers", "scope": schemas.RoleScope.reseller, "permissions": ["reseller.view_customers","reseller.manage_customers","reseller.assign_tariffs","billing.create_invoices","billing.view_invoices","reports.view_usage"]},
    {"name": "Reseller Read-Only", "description": "View-only for reseller area", "scope": schemas.RoleScope.reseller, "permissions": ["reseller.view_customers","reports.view_usage","billing.view_invoices"]}
]

def _seed_initial_rbac_data(db: Session):
    """
    Seeds initial permissions and roles into the database if they don't already exist.
    This function is idempotent.
    """
    print("Seeding initial permissions...")
    for perm_data in permissions_to_seed:
        if not crud.get_permission_by_code(db, code=perm_data["code"]):
            permission = schemas.PermissionCreate(**perm_data)
            crud.create_permission(db, permission)

    print("Seeding initial roles...")
    for role_data in roles_to_seed:
        if not crud.get_role_by_name(db, name=role_data["name"]):
            # Create a copy to safely pop 'permissions' for schema creation
            role_data_copy = role_data.copy()
            permission_codes = role_data_copy.pop("permissions")
            role_create = schemas.RoleCreate(**role_data_copy, permission_codes=permission_codes)
            crud.create_role(db, role_create)

    print("Initial RBAC seeding complete.")

setup_router = APIRouter()

@setup_router.get("/status")
def get_setup_status(db: Session = Depends(get_db)):
    count = crud.get_administrators_count(db) # Still checking administrators count for initial setup
    return {"setup_complete": count > 0}

@setup_router.post("/create-admin")
async def create_initial_admin(
    setup_data: schemas.SetupData, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    count = crud.get_administrators_count(db)
    if count > 0:
        raise HTTPException(status_code=403, detail="Setup has already been completed.")
    
    # Seed initial RBAC data (permissions and roles)
    _seed_initial_rbac_data(db)

    # Create partner
    partner_schema = schemas.PartnerCreate(name=setup_data.partner_name)
    partner = crud.create_partner(db, partner=partner_schema)
    await logger.log("create", "partner", partner.id, after_values={"name": partner.name}, risk_level='high', business_context=f"Initial partner '{partner.name}' created during setup.")

    # Create the initial user
    user_create_schema = schemas.UserCreate(
        email=setup_data.admin_email,
        password=setup_data.admin_password,
        full_name=setup_data.admin_full_name,
        kind=schemas.UserKind.staff # Initial admin is a staff user
    )
    user = crud.create_user(db, user=user_create_schema)
    await logger.log("create", "user", user.id, after_values={"email": user.email, "full_name": user.full_name}, risk_level='high', business_context=f"Initial admin user '{user.email}' created during setup.")

    # Create the administrator profile linked to the user
    admin_create_schema = schemas.AdministratorCreate(
        user_id=user.id,
        # Other optional fields can be set here if needed
    )
    admin = crud.create_administrator(db, admin_data=admin_create_schema, partner_id=partner.id)
    await logger.log("create", "administrator", admin.id, after_values={"user_id": user.id, "partner_id": partner.id}, risk_level='high', business_context=f"Administrator profile created for user '{user.email}'.")

    # Assign Super Admin role to the initial admin user
    # Ensure the "Super Admin" role exists and has all permissions
    all_permission_codes = [p.code for p in crud.get_permissions(db)]
    super_admin_role = crud.get_role_by_name(db, name="Super Admin") # Re-fetch to ensure it's fresh after seeding
    # Always ensure the Super Admin role has ALL permissions.
    # This handles cases where new permissions are added or if the role was pre-seeded without all.
    # We explicitly update it to the full set of permissions.
    updated_permission_codes = all_permission_codes # Ensure it has all permissions
    super_admin_role = crud.update_role(db, super_admin_role.id, schemas.RoleUpdate(permission_codes=updated_permission_codes))

    user_role_create = schemas.UserRoleCreate(user_id=user.id, role_id=super_admin_role.id)
    user_role_create.customer_id = None
    user_role_create.reseller_id = None
    crud.assign_role_to_user(db, user_role_create)
    await logger.log("update", "user", user.id, after_values={"role": "Super Admin"}, risk_level='critical', business_context=f"Assigned 'Super Admin' role to user '{user.email}'.")

    return {"message": "Initial admin user and setup completed successfully."}
