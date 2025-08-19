# Generate a comprehensive PostgreSQL RBAC schema and seed data for an ISP context
sql = r"""
-- =====================================================================================
-- ISP RBAC Schema (PostgreSQL)
-- Covers Admin/Staff, Customers, and Resellers with scoped role assignments.
-- Tested for PostgreSQL 13+.
-- =====================================================================================

-- Create schema (optional)
CREATE SCHEMA IF NOT EXISTS isp_rbac;
SET search_path TO isp_rbac;

-- =====================================================================================
-- Enum types
-- =====================================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_kind') THEN
        CREATE TYPE user_kind AS ENUM ('staff','customer','reseller');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_scope') THEN
        CREATE TYPE role_scope AS ENUM ('system','customer','reseller');
    END IF;
END$$;

-- =====================================================================================
-- Core tables
-- =====================================================================================

-- Users (people who can log into the system)
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    email           CITEXT UNIQUE NOT NULL,
    full_name       TEXT NOT NULL,
    kind            user_kind NOT NULL DEFAULT 'staff',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Customers (accounts that subscribe to ISP services)
CREATE TABLE IF NOT EXISTS customers (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    external_ref    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Resellers (partners)
CREATE TABLE IF NOT EXISTS resellers (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    external_ref    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Optional: link user to a customer or reseller profile (for portal users)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id         BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    customer_id     BIGINT REFERENCES customers(id) ON DELETE SET NULL,
    reseller_id     BIGINT REFERENCES resellers(id) ON DELETE SET NULL,
    CHECK ( (customer_id IS NULL) OR (reseller_id IS NULL) ) -- can't be both
);

-- Roles
CREATE TABLE IF NOT EXISTS roles (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    scope           role_scope NOT NULL DEFAULT 'system', -- where this role is valid
    parent_role_id  BIGINT REFERENCES roles(id) ON DELETE SET NULL -- for hierarchy (optional)
);

-- Permissions
CREATE TABLE IF NOT EXISTS permissions (
    id              BIGSERIAL PRIMARY KEY,
    code            TEXT UNIQUE NOT NULL, -- e.g. 'billing.create_invoices'
    description     TEXT NOT NULL,
    module          TEXT NOT NULL         -- e.g. 'billing','crm','network','support', etc.
);

-- Role -> Permission mapping
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id         BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id   BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- User -> Role assignments, optionally scoped to a customer or reseller
CREATE TABLE IF NOT EXISTS user_roles (
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id         BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    customer_id     BIGINT REFERENCES customers(id) ON DELETE CASCADE,
    reseller_id     BIGINT REFERENCES resellers(id) ON DELETE CASCADE,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id, COALESCE(customer_id,0), COALESCE(reseller_id,0)),
    CHECK ( (customer_id IS NULL AND reseller_id IS NULL)
            OR (customer_id IS NOT NULL AND reseller_id IS NULL)
            OR (customer_id IS NULL AND reseller_id IS NOT NULL) )
);

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_customer ON user_roles(customer_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_reseller ON user_roles(reseller_id);
CREATE INDEX IF NOT EXISTS idx_permissions_code ON permissions(code);

-- =====================================================================================
-- Seed Permissions (modular; extend as needed)
-- =====================================================================================

WITH upsert_perm AS (
    INSERT INTO permissions (code, description, module)
    VALUES
        -- System & Security
        ('system.manage_users',        'Create, edit and deactivate users',               'system'),
        ('system.manage_roles',        'Create and assign roles',                         'system'),
        ('system.view_audit_logs',     'View system audit logs',                          'system'),
        ('system.configure_security',  'Manage security settings (RBAC, MFA, SSO)',       'system'),
        ('system.manage_backups',      'Manage backups and restores',                     'system'),

        -- CRM
        ('crm.view_accounts',          'View accounts/customers',                         'crm'),
        ('crm.create_accounts',        'Create accounts/customers',                       'crm'),
        ('crm.edit_accounts',          'Edit accounts/customers',                         'crm'),
        ('crm.delete_accounts',        'Delete accounts/customers',                       'crm'),
        ('crm.manage_leads',           'Manage CRM leads',                                'crm'),
        ('crm.manage_opportunities',   'Manage CRM opportunities',                        'crm'),

        -- Support
        ('support.view_tickets',       'View support tickets',                            'support'),
        ('support.create_tickets',     'Create support tickets',                          'support'),
        ('support.edit_tickets',       'Edit support tickets (comments, status)',         'support'),
        ('support.assign_tickets',     'Assign tickets to agents',                        'support'),
        ('support.manage_knowledge',   'Manage knowledge base',                           'support'),

        -- Billing
        ('billing.view_invoices',      'View invoices',                                   'billing'),
        ('billing.create_invoices',    'Create invoices',                                 'billing'),
        ('billing.edit_invoices',      'Edit invoices',                                   'billing'),
        ('billing.process_payments',   'Record/process payments & refunds',               'billing'),
        ('billing.manage_tariffs',     'Create & update tariff plans',                    'billing'),
        ('billing.view_financials',    'View financial reports',                          'billing'),

        -- Network
        ('network.view_devices',       'View network devices and topology',               'network'),
        ('network.manage_devices',     'Add/edit network devices & config',               'network'),
        ('network.manage_ip_pools',    'Manage IP pools and assignments',                 'network'),
        ('network.view_sessions',      'View RADIUS/PPP sessions',                        'network'),
        ('network.disconnect_sessions','Disconnect/CoA sessions',                         'network'),

        -- Inventory
        ('inventory.view_items',       'View inventory items',                            'inventory'),
        ('inventory.add_items',        'Add new inventory items',                         'inventory'),
        ('inventory.edit_items',       'Edit inventory items',                            'inventory'),
        ('inventory.remove_items',     'Remove inventory items',                          'inventory'),

        -- Field Operations
        ('field.view_jobs',            'View field jobs/work orders',                     'field'),
        ('field.assign_jobs',          'Assign jobs to technicians',                      'field'),
        ('field.update_jobs',          'Update job progress/results',                     'field'),

        -- Projects
        ('projects.view',              'View projects and tasks',                         'projects'),
        ('projects.manage',            'Create/edit projects and tasks',                  'projects'),

        -- Reports
        ('reports.view_usage',         'View usage reports',                              'reports'),
        ('reports.view_network',       'View network performance reports',                'reports'),
        ('reports.view_financial',     'View financial reports',                          'reports'),

        -- Reseller
        ('reseller.view_customers',    'View reseller''s customers',                      'reseller'),
        ('reseller.manage_customers',  'Create/edit reseller customers',                  'reseller'),
        ('reseller.assign_tariffs',    'Assign tariffs to reseller customers',            'reseller'),
        ('reseller.generate_reports',  'Generate reports for reseller business',          'reseller')
    ON CONFLICT (code) DO NOTHING
    RETURNING id, code
)
SELECT * FROM upsert_perm;

-- =====================================================================================
-- Seed Roles
-- =====================================================================================

WITH upsert_role AS (
    INSERT INTO roles (name, description, scope, parent_role_id)
    VALUES
        -- Staff
        ('Super Admin',       'Full control of all system functions',          'system', NULL),
        ('System Admin',      'Manage system config, network, and security',   'system', 1),
        ('Network Engineer',  'Manage network infrastructure',                 'system', 2),
        ('Billing Manager',   'Manage financials, invoices, tariffs',          'system', 2),
        ('Support Manager',   'Oversee support and SLA',                       'system', 2),
        ('Support Agent',     'Handle support tickets',                        'system', 5),
        ('Field Technician',  'Execute on-site jobs',                          'system', 2),
        ('Inventory Manager', 'Manage stock and device assignments',           'system', 2),
        ('Project Manager',   'Manage internal projects',                      'system', 2),
        ('Read-Only Staff',   'View-only across modules',                      'system', 2),

        -- Customer
        ('Customer Admin',    'Lead contact; manage own account',              'customer', NULL),
        ('Customer User',     'Sub-user; limited actions',                     'customer', 11),
        ('Customer Read-Only','View-only for invoices/usage',                  'customer', 12),

        -- Reseller
        ('Reseller Admin',    'Manage reseller business and sub-customers',    'reseller', NULL),
        ('Reseller Staff',    'Operate on reseller''s assigned customers',     'reseller', 14),
        ('Reseller Read-Only','View-only for reseller area',                   'reseller', 15)
    ON CONFLICT (name) DO NOTHING
    RETURNING id, name
)
SELECT * FROM upsert_role;

-- =====================================================================================
-- Map Role -> Permissions
-- =====================================================================================

-- Helper: get ids
WITH rp AS (
    SELECT r.id AS role_id, r.name, p.id AS perm_id, p.code
    FROM roles r CROSS JOIN permissions p
)
-- Super Admin: all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- System Admin: everything except possibly destructive audit/backup? (keep almost all)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON TRUE
WHERE r.name = 'System Admin'
AND p.code NOT IN ('system.manage_backups') -- adjust policy as needed
ON CONFLICT DO NOTHING;

-- Network Engineer
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'network.view_devices','network.manage_devices','network.manage_ip_pools',
    'network.view_sessions','network.disconnect_sessions',
    'reports.view_network'
)
WHERE r.name = 'Network Engineer'
ON CONFLICT DO NOTHING;

-- Billing Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'billing.view_invoices','billing.create_invoices','billing.edit_invoices',
    'billing.process_payments','billing.manage_tariffs','reports.view_financial'
)
WHERE r.name = 'Billing Manager'
ON CONFLICT DO NOTHING;

-- Support Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'support.view_tickets','support.create_tickets','support.edit_tickets',
    'support.assign_tickets','support.manage_knowledge',
    'crm.view_accounts','reports.view_usage'
)
WHERE r.name = 'Support Manager'
ON CONFLICT DO NOTHING;

-- Support Agent
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'support.view_tickets','support.create_tickets','support.edit_tickets',
    'crm.view_accounts'
)
WHERE r.name = 'Support Agent'
ON CONFLICT DO NOTHING;

-- Field Technician
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'field.view_jobs','field.update_jobs','crm.view_accounts','inventory.view_items'
)
WHERE r.name = 'Field Technician'
ON CONFLICT DO NOTHING;

-- Inventory Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'inventory.view_items','inventory.add_items','inventory.edit_items','inventory.remove_items'
)
WHERE r.name = 'Inventory Manager'
ON CONFLICT DO NOTHING;

-- Project Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN ('projects.view','projects.manage')
WHERE r.name = 'Project Manager'
ON CONFLICT DO NOTHING;

-- Read-Only Staff
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'crm.view_accounts','support.view_tickets','billing.view_invoices',
    'network.view_devices','network.view_sessions',
    'inventory.view_items','projects.view',
    'reports.view_usage','reports.view_network','reports.view_financial',
    'system.view_audit_logs'
)
WHERE r.name = 'Read-Only Staff'
ON CONFLICT DO NOTHING;

-- Customer Admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'billing.view_invoices','support.create_tickets','support.view_tickets',
    'reports.view_usage'
)
WHERE r.name = 'Customer Admin'
ON CONFLICT DO NOTHING;

-- Customer User
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'support.create_tickets','support.view_tickets','reports.view_usage'
)
WHERE r.name = 'Customer User'
ON CONFLICT DO NOTHING;

-- Customer Read-Only
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'billing.view_invoices','reports.view_usage'
)
WHERE r.name = 'Customer Read-Only'
ON CONFLICT DO NOTHING;

-- Reseller Admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'reseller.view_customers','reseller.manage_customers','reseller.assign_tariffs',
    'reseller.generate_reports','billing.create_invoices','billing.view_invoices',
    'reports.view_usage','reports.view_financial'
)
WHERE r.name = 'Reseller Admin'
ON CONFLICT DO NOTHING;

-- Reseller Staff
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'reseller.view_customers','reseller.manage_customers','reseller.assign_tariffs',
    'billing.create_invoices','billing.view_invoices','reports.view_usage'
)
WHERE r.name = 'Reseller Staff'
ON CONFLICT DO NOTHING;

-- Reseller Read-Only
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'reseller.view_customers','reports.view_usage','billing.view_invoices'
)
WHERE r.name = 'Reseller Read-Only'
ON CONFLICT DO NOTHING;

-- System Admin extras (system)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r
JOIN permissions p ON p.code IN (
    'system.manage_users','system.manage_roles','system.view_audit_logs',
    'system.configure_security','system.manage_backups',
    'crm.view_accounts','crm.create_accounts','crm.edit_accounts','crm.delete_accounts',
    'crm.manage_leads','crm.manage_opportunities'
)
WHERE r.name = 'System Admin'
ON CONFLICT DO NOTHING;

-- =====================================================================================
-- Helper Views & Functions
-- =====================================================================================

-- View: effective permissions by user, with optional scope
CREATE OR REPLACE VIEW v_user_effective_permissions AS
SELECT
    ur.user_id,
    r.name AS role_name,
    r.scope,
    ur.customer_id,
    ur.reseller_id,
    p.code AS permission_code
FROM user_roles ur
JOIN roles r ON r.id = ur.role_id
JOIN role_permissions rp ON rp.role_id = r.id
JOIN permissions p ON p.id = rp.permission_id;

-- Function: check if a user has a given permission (optionally within a scope)
CREATE OR REPLACE FUNCTION has_permission(
    p_user_id BIGINT,
    p_permission_code TEXT,
    p_customer_id BIGINT DEFAULT NULL,
    p_reseller_id BIGINT DEFAULT NULL
) RETURNS BOOLEAN LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_allowed BOOLEAN;
BEGIN
    -- System-wide role (no scope)
    SELECT TRUE INTO v_allowed
    FROM v_user_effective_permissions v
    WHERE v.user_id = p_user_id
      AND v.permission_code = p_permission_code
      AND v.scope = 'system'
    LIMIT 1;

    IF v_allowed THEN
        RETURN TRUE;
    END IF;

    -- Customer-scoped
    IF p_customer_id IS NOT NULL THEN
        SELECT TRUE INTO v_allowed
        FROM v_user_effective_permissions v
        WHERE v.user_id = p_user_id
          AND v.permission_code = p_permission_code
          AND v.scope = 'customer'
          AND v.customer_id = p_customer_id
        LIMIT 1;

        IF v_allowed THEN
            RETURN TRUE;
        END IF;
    END IF;

    -- Reseller-scoped
    IF p_reseller_id IS NOT NULL THEN
        SELECT TRUE INTO v_allowed
        FROM v_user_effective_permissions v
        WHERE v.user_id = p_user_id
          AND v.permission_code = p_permission_code
          AND v.scope = 'reseller'
          AND v.reseller_id = p_reseller_id
        LIMIT 1;

        IF v_allowed THEN
            RETURN TRUE;
        END IF;
    END IF;

    RETURN FALSE;
END$$;

-- =====================================================================================
-- Sample Data (optional)
-- =====================================================================================

-- Sample staff users
INSERT INTO users (email, full_name, kind) VALUES
    ('super@isp.local', 'Super User', 'staff'),
    ('neteng@isp.local', 'Network Engineer', 'staff'),
    ('billing@isp.local', 'Billing Manager', 'staff')
ON CONFLICT (email) DO NOTHING;

-- Sample customers & users
INSERT INTO customers (name) VALUES ('Acme Ltd'), ('Globex Corp')
ON CONFLICT DO NOTHING;

INSERT INTO users (email, full_name, kind) VALUES
    ('owner@acme.com', 'Acme Owner', 'customer'),
    ('user@acme.com',  'Acme User',  'customer')
ON CONFLICT (email) DO NOTHING;

-- Link profiles
INSERT INTO user_profiles (user_id, customer_id)
SELECT u.id, c.id
FROM users u
JOIN customers c ON c.name = 'Acme Ltd'
WHERE u.email IN ('owner@acme.com','user@acme.com')
ON CONFLICT (user_id) DO NOTHING;

-- Sample reseller & users
INSERT INTO resellers (name) VALUES ('FiberHub Reseller')
ON CONFLICT DO NOTHING;

INSERT INTO users (email, full_name, kind) VALUES
    ('admin@fiberhub.io', 'FiberHub Admin', 'reseller')
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_profiles (user_id, reseller_id)
SELECT u.id, r.id FROM users u
JOIN resellers r ON r.name = 'FiberHub Reseller'
WHERE u.email = 'admin@fiberhub.io'
ON CONFLICT (user_id) DO NOTHING;

-- Assign roles to users
-- Super Admin to super user (system-wide)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u, roles r
WHERE u.email = 'super@isp.local' AND r.name = 'Super Admin'
ON CONFLICT DO NOTHING;

-- Network Engineer
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u, roles r
WHERE u.email = 'neteng@isp.local' AND r.name = 'Network Engineer'
ON CONFLICT DO NOTHING;

-- Billing Manager
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u, roles r
WHERE u.email = 'billing@isp.local' AND r.name = 'Billing Manager'
ON CONFLICT DO NOTHING;

-- Customer Admin (scoped to Acme Ltd)
INSERT INTO user_roles (user_id, role_id, customer_id)
SELECT u.id, r.id, c.id
FROM users u
JOIN roles r ON r.name = 'Customer Admin'
JOIN customers c ON c.name = 'Acme Ltd'
WHERE u.email = 'owner@acme.com'
ON CONFLICT DO NOTHING;

-- Customer User (scoped to Acme Ltd)
INSERT INTO user_roles (user_id, role_id, customer_id)
SELECT u.id, r.id, c.id
FROM users u
JOIN roles r ON r.name = 'Customer User'
JOIN customers c ON c.name = 'Acme Ltd'
WHERE u.email = 'user@acme.com'
ON CONFLICT DO NOTHING;

-- Reseller Admin (scoped to FiberHub Reseller)
INSERT INTO user_roles (user_id, role_id, reseller_id)
SELECT u.id, r.id, rs.id
FROM users u
JOIN roles r ON r.name = 'Reseller Admin'
JOIN resellers rs ON rs.name = 'FiberHub Reseller'
WHERE u.email = 'admin@fiberhub.io'
ON CONFLICT DO NOTHING;

-- =====================================================================================
-- Example queries
-- =====================================================================================

-- 1) What permissions does a user have (system-wide and scoped)?
-- SELECT * FROM v_user_effective_permissions WHERE user_id = (SELECT id FROM users WHERE email='owner@acme.com');

-- 2) Check permission for a customer-scoped action:
-- SELECT has_permission((SELECT id FROM users WHERE email='owner@acme.com'),
--                       'billing.view_invoices',
--                       (SELECT id FROM customers WHERE name='Acme Ltd'),
--                       NULL);

-- 3) Check permission for a system action:
-- SELECT has_permission((SELECT id FROM users WHERE email='neteng@isp.local'),
--                       'network.manage_devices',
--                       NULL, NULL);

-- =====================================================================================
-- End of file
-- =====================================================================================
"""

path = "/mnt/data/isp_rbac_postgres.sql"
with open(path, "w") as f:
    f.write(sql)

path
