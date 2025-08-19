-- ISP Framework Complete Database Schema
-- Version 2.0.0 - Fully Aligned with API Contract
-- Includes all features: Core ISP, Extended Features, and Framework Capabilities

-- =============================================================================
-- FRAMEWORK FOUNDATION LAYER
-- =============================================================================

-- Framework System Configuration
CREATE TABLE framework_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB,
    config_type VARCHAR(50) DEFAULT 'json', -- json, string, number, boolean
    is_system BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CORE SYSTEM TABLES
-- =============================================================================

-- Partners (ISP Organizations)
CREATE TABLE partners (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    -- Framework Integration
    framework_config JSONB DEFAULT '{}', -- Custom entity configurations
    ui_customizations JSONB DEFAULT '{}', -- UI overrides
    branding_config JSONB DEFAULT '{}', -- Logo, colors, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations (Geographic service areas)
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    -- Extended Location Data
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'Nigeria',
    -- Geographic Data
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(100) DEFAULT 'Africa/Lagos',
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}', -- Dynamic custom fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Administrators
CREATE TABLE administrators (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER REFERENCES partners(id),
    login VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    role VARCHAR(50) DEFAULT 'admin',
    timeout INTEGER DEFAULT 1200,
    is_active BOOLEAN DEFAULT true,
    -- Enhanced User Management
    last_login TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Framework Integration
    framework_roles INTEGER[] DEFAULT '{}', -- References framework_roles(id)
    custom_permissions JSONB DEFAULT '{}', -- Additional permissions
    ui_preferences JSONB DEFAULT '{}', -- Dashboard layout, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys for authentication
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    partner_id INTEGER REFERENCES partners(id),
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CUSTOMER MANAGEMENT
-- =============================================================================

-- Customer Labels
CREATE TABLE customer_labels (
    id SERIAL PRIMARY KEY,
    label VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#357bf2', -- Hex color
    icon VARCHAR(100),
    description TEXT,
    -- Framework Integration
    custom_properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    login VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    status VARCHAR(20) DEFAULT 'new', -- new, active, blocked, disabled
    partner_id INTEGER NOT NULL REFERENCES partners(id),
    location_id INTEGER NOT NULL REFERENCES locations(id),
    parent_id INTEGER REFERENCES customers(id), -- for sub-accounts
    
    -- Personal Information
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    billing_email VARCHAR(255),
    phone VARCHAR(50),
    category VARCHAR(20) DEFAULT 'person', -- person, company
    
    -- Address
    street_1 VARCHAR(255),
    zip_code VARCHAR(20),
    city VARCHAR(100),
    subdivision_id INTEGER, -- state/province
    
    -- Financial
    billing_type VARCHAR(20) DEFAULT 'recurring', -- recurring, prepaid_daily, prepaid_monthly
    mrr_total DECIMAL(10,4) DEFAULT 0,
    daily_prepaid_cost DECIMAL(10,4) DEFAULT 0,
    
    -- Metadata
    gps VARCHAR(100), -- latitude,longitude
    date_add DATE DEFAULT CURRENT_DATE,
    conversion_date DATE,
    added_by VARCHAR(20) DEFAULT 'admin',
    added_by_id INTEGER,
    last_online TIMESTAMP,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}', -- Dynamic custom fields from framework
    workflow_state JSONB DEFAULT '{}', -- Current state in workflows
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Label Associations
CREATE TABLE customer_label_associations (
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    label_id INTEGER REFERENCES customer_labels(id) ON DELETE CASCADE,
    PRIMARY KEY (customer_id, label_id)
);

-- Customer Additional Information
CREATE TABLE customer_info (
    customer_id INTEGER PRIMARY KEY REFERENCES customers(id) ON DELETE CASCADE,
    birthday DATE,
    passport VARCHAR(100),
    company_id VARCHAR(100),
    contact_person VARCHAR(255),
    vat_id VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Billing Configuration
CREATE TABLE customer_billing (
    customer_id INTEGER PRIMARY KEY REFERENCES customers(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    type INTEGER DEFAULT 1,
    deposit DECIMAL(10,4) DEFAULT 0,
    billing_date INTEGER DEFAULT 1,
    billing_due INTEGER DEFAULT 2,
    blocking_period INTEGER DEFAULT 0,
    grace_period INTEGER DEFAULT 3,
    make_invoices BOOLEAN DEFAULT true,
    payment_method INTEGER DEFAULT 1,
    min_balance DECIMAL(10,4) DEFAULT 0,
    auto_enable_request BOOLEAN DEFAULT false,
    reminder_enabled BOOLEAN DEFAULT true,
    reminder_day_1 INTEGER DEFAULT 2,
    reminder_day_2 INTEGER DEFAULT 8,
    reminder_day_3 INTEGER DEFAULT 20,
    sub_billing_mode VARCHAR(20) DEFAULT 'independent', -- independent, aggregated
    send_finance_notification BOOLEAN DEFAULT true,
    partner_percent DECIMAL(5,4) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SERVICE PLAN MANAGEMENT & LIFECYCLE
-- =============================================================================

-- Transaction Categories
CREATE TABLE transaction_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_base BOOLEAN DEFAULT false,
    -- Framework Integration
    category_config JSONB DEFAULT '{}', -- Rules, automation, etc.
    custom_fields JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Taxes
CREATE TABLE taxes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rate DECIMAL(5,4) NOT NULL,
    type VARCHAR(20) DEFAULT 'single', -- single, group
    archived BOOLEAN DEFAULT false,
    -- Geographic Application
    applicable_locations INTEGER[], -- Which locations this tax applies to
    -- Framework Integration
    calculation_rules JSONB DEFAULT '{}', -- Custom tax calculation logic
    custom_fields JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Internet Service Plans (Tariffs)
CREATE TABLE internet_tariffs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    service_name VARCHAR(255) UNIQUE,
    partners_ids INTEGER[] NOT NULL,
    price DECIMAL(10,4) DEFAULT 0,
    with_vat BOOLEAN DEFAULT true,
    vat_percent DECIMAL(5,2) DEFAULT 0,
    
    -- Speed Configuration
    speed_download INTEGER NOT NULL, -- kbps
    speed_upload INTEGER NOT NULL, -- kbps
    speed_limit_at INTEGER DEFAULT 10, -- percentage
    aggregation INTEGER DEFAULT 1,
    
    -- Burst Configuration
    burst_limit INTEGER DEFAULT 0,
    burst_limit_fixed_down INTEGER DEFAULT 0,
    burst_limit_fixed_up INTEGER DEFAULT 0,
    burst_threshold INTEGER DEFAULT 0,
    burst_threshold_fixed_down INTEGER DEFAULT 0,
    burst_threshold_fixed_up INTEGER DEFAULT 0,
    burst_time INTEGER DEFAULT 0,
    burst_type VARCHAR(20) DEFAULT 'none', -- none, percent, fixed
    
    -- Speed Limit Configuration
    speed_limit_type VARCHAR(20) DEFAULT 'none', -- none, percent, fixed
    speed_limit_fixed_down INTEGER DEFAULT 0,
    speed_limit_fixed_up INTEGER DEFAULT 0,
    
    -- Billing Configuration
    billing_types VARCHAR(100)[], -- recurring, prepaid, prepaid_monthly
    billing_days_count INTEGER DEFAULT 1,
    custom_period BOOLEAN DEFAULT false,
    
    -- Availability
    customer_categories VARCHAR(50)[], -- person, company
    available_for_services BOOLEAN DEFAULT true,
    available_for_locations INTEGER[],
    hide_on_admin_portal BOOLEAN DEFAULT false,
    show_on_customer_portal BOOLEAN DEFAULT false,
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high
    
    -- Financial
    tax_id INTEGER REFERENCES taxes(id),
    transaction_category_id INTEGER REFERENCES transaction_categories(id),
    
    -- Framework Integration
    pricing_rules JSONB DEFAULT '{}', -- Dynamic pricing logic
    service_rules JSONB DEFAULT '{}', -- Service-specific business rules
    custom_fields JSONB DEFAULT '{}', -- User-defined fields
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voice Service Plans
CREATE TABLE voice_tariffs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    service_name VARCHAR(255) UNIQUE,
    type VARCHAR(20) DEFAULT 'voip', -- voip, fix, mobile
    partners_ids INTEGER[] NOT NULL,
    price DECIMAL(10,4) DEFAULT 0,
    with_vat BOOLEAN DEFAULT true,
    vat_percent DECIMAL(5,2) DEFAULT 0,
    
    billing_types VARCHAR(100)[],
    billing_days_count INTEGER DEFAULT 1,
    custom_period BOOLEAN DEFAULT false,
    
    customer_categories VARCHAR(50)[],
    available_for_services BOOLEAN DEFAULT true,
    available_for_locations INTEGER[],
    hide_on_admin_portal BOOLEAN DEFAULT false,
    show_on_customer_portal BOOLEAN DEFAULT false,
    
    tax_id INTEGER REFERENCES taxes(id),
    transaction_category_id INTEGER REFERENCES transaction_categories(id),
    
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recurring (Custom) Service Plans
CREATE TABLE recurring_tariffs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    service_name VARCHAR(255) UNIQUE,
    partners_ids INTEGER[] NOT NULL,
    price DECIMAL(10,4) DEFAULT 0,
    with_vat BOOLEAN DEFAULT true,
    vat_percent DECIMAL(5,2) DEFAULT 0,
    
    billing_types VARCHAR(100)[],
    billing_days_count INTEGER DEFAULT 1,
    custom_period BOOLEAN DEFAULT false,
    
    customer_categories VARCHAR(50)[],
    available_for_services BOOLEAN DEFAULT true,
    available_for_locations INTEGER[],
    hide_on_admin_portal BOOLEAN DEFAULT false,
    show_on_customer_portal BOOLEAN DEFAULT false,
    
    tax_id INTEGER REFERENCES taxes(id),
    transaction_category_id INTEGER REFERENCES transaction_categories(id),
    
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- One-time Service Plans
CREATE TABLE one_time_tariffs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    service_description TEXT,
    price DECIMAL(10,4) DEFAULT 0,
    with_vat BOOLEAN DEFAULT true,
    vat_percent DECIMAL(5,2) DEFAULT 0,
    partners_ids INTEGER[] NOT NULL,
    
    customer_categories VARCHAR(50)[],
    available_for_locations INTEGER[],
    enabled BOOLEAN DEFAULT true,
    hide_on_admin_portal BOOLEAN DEFAULT false,
    show_on_customer_portal BOOLEAN DEFAULT false,
    
    tax_id INTEGER REFERENCES taxes(id),
    transaction_category_id INTEGER REFERENCES transaction_categories(id),
    
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bundle Service Plans
CREATE TABLE bundle_tariffs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    service_description TEXT,
    partners_ids INTEGER[] NOT NULL,
    price DECIMAL(10,4) DEFAULT 0,
    with_vat BOOLEAN DEFAULT true,
    vat_percent DECIMAL(5,2) DEFAULT 0,
    
    -- Fees
    activation_fee DECIMAL(10,4) DEFAULT 0,
    cancellation_fee DECIMAL(10,4) DEFAULT 0,
    prior_cancellation_fee DECIMAL(10,4) DEFAULT 0,
    change_to_other_bundle_fee DECIMAL(10,4) DEFAULT 0,
    
    -- Configuration
    contract_duration INTEGER DEFAULT 0, -- months
    get_activation_fee_when VARCHAR(30) DEFAULT 'create_service',
    automatic_renewal BOOLEAN DEFAULT false,
    auto_reactivate BOOLEAN DEFAULT false,
    issue_invoice_while_service_creation BOOLEAN DEFAULT false,
    
    -- Discount
    discount_period INTEGER DEFAULT 0,
    discount_type VARCHAR(20) DEFAULT 'percent',
    discount_value DECIMAL(10,4) DEFAULT 0,
    
    -- Included tariffs
    internet_tariffs INTEGER[],
    voice_tariffs INTEGER[],
    custom_tariffs INTEGER[],
    
    billing_types VARCHAR(100)[],
    billing_days_count INTEGER DEFAULT 1,
    custom_period BOOLEAN DEFAULT false,
    available_for_services BOOLEAN DEFAULT true,
    
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SERVICES (CUSTOMER SUBSCRIPTIONS)
-- =============================================================================

-- Internet Services
CREATE TABLE internet_services (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    tariff_id INTEGER NOT NULL REFERENCES internet_tariffs(id),
    status VARCHAR(20) DEFAULT 'active', -- active, stopped, disabled, hidden, pending, terminated
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,4),
    
    -- Service Dates
    start_date DATE NOT NULL,
    end_date DATE DEFAULT '9999-12-31',
    
    -- Discount
    discount DECIMAL(10,4) DEFAULT 0,
    discount_type VARCHAR(20) DEFAULT 'percent',
    discount_value DECIMAL(10,4) DEFAULT 0,
    discount_start_date DATE,
    discount_end_date DATE,
    discount_text TEXT,
    
    -- Network Configuration
    router_id INTEGER,
    sector_id INTEGER,
    login VARCHAR(255) NOT NULL,
    password VARCHAR(255),
    taking_ipv4 INTEGER DEFAULT 0, -- 0=none, 1=permanent, 2=dynamic
    ipv4 INET,
    ipv4_route VARCHAR(100),
    ipv4_pool_id INTEGER,
    ipv6 INET,
    ipv6_delegated VARCHAR(100),
    ipv6_pool_id INTEGER,
    taking_ipv6 INTEGER DEFAULT 0,
    mac VARCHAR(100),
    port_id INTEGER,
    
    -- Relationships
    bundle_service_id INTEGER DEFAULT 0,
    parent_id INTEGER DEFAULT 0,
    access_device INTEGER DEFAULT 0,
    
    -- Configuration
    on_approve BOOLEAN DEFAULT false,
    period INTEGER DEFAULT -1,
    status_new VARCHAR(20) DEFAULT '',
    top_up_tariff_id INTEGER DEFAULT 0,
    
    -- Framework Integration
    service_rules JSONB DEFAULT '{}', -- Applied business rules
    custom_fields JSONB DEFAULT '{}', -- Dynamic custom fields
    workflow_state JSONB DEFAULT '{}', -- Current workflow state
    automation_config JSONB DEFAULT '{}', -- Service automation settings
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voice Services
CREATE TABLE voice_services (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    tariff_id INTEGER NOT NULL REFERENCES voice_tariffs(id),
    status VARCHAR(20) DEFAULT 'active',
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,4),
    
    start_date DATE NOT NULL,
    end_date DATE DEFAULT '9999-12-31',
    
    discount DECIMAL(10,4) DEFAULT 0,
    discount_type VARCHAR(20) DEFAULT 'percent',
    discount_value DECIMAL(10,4) DEFAULT 0,
    discount_start_date DATE,
    discount_end_date DATE,
    discount_text TEXT,
    
    -- Voice Configuration
    voice_device_id INTEGER,
    phone VARCHAR(50) NOT NULL,
    direction VARCHAR(20) DEFAULT 'outgoing', -- incoming, outgoing
    
    bundle_service_id INTEGER DEFAULT 0,
    parent_id INTEGER DEFAULT 0,
    on_approve BOOLEAN DEFAULT false,
    period INTEGER DEFAULT -1,
    status_new VARCHAR(20) DEFAULT '',
    
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recurring (Custom) Services
CREATE TABLE recurring_services (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    tariff_id INTEGER NOT NULL REFERENCES recurring_tariffs(id),
    status VARCHAR(20) DEFAULT 'active',
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,4),
    
    start_date DATE NOT NULL,
    end_date DATE DEFAULT '9999-12-31',
    
    discount DECIMAL(10,4) DEFAULT 0,
    discount_type VARCHAR(20) DEFAULT 'percent',
    discount_value DECIMAL(10,4) DEFAULT 0,
    discount_start_date DATE,
    discount_end_date DATE,
    discount_text TEXT,
    
    bundle_service_id INTEGER DEFAULT 0,
    parent_id INTEGER DEFAULT 0,
    on_approve BOOLEAN DEFAULT false,
    period INTEGER DEFAULT -1,
    status_new VARCHAR(20) DEFAULT '',
    
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bundle Services
CREATE TABLE bundle_services (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    bundle_id INTEGER NOT NULL REFERENCES bundle_tariffs(id),
    status VARCHAR(20) DEFAULT 'active',
    description TEXT NOT NULL,
    unit_price DECIMAL(10,4),
    
    start_date DATE NOT NULL,
    end_date DATE DEFAULT '9999-12-31',
    
    discount DECIMAL(10,4) DEFAULT 0,
    discount_type VARCHAR(20) DEFAULT 'percent',
    discount_value DECIMAL(10,4) DEFAULT 0,
    discount_start_date DATE,
    discount_end_date DATE,
    discount_text TEXT,
    
    -- Bundle Configuration
    automatic_renewal BOOLEAN DEFAULT false,
    activation_fee DECIMAL(10,4) DEFAULT 0,
    auto_reactivate BOOLEAN DEFAULT false,
    get_activation_fee_when VARCHAR(30) DEFAULT 'create_service',
    issue_invoice_while_service_creation BOOLEAN DEFAULT false,
    cancellation_fee DECIMAL(10,4) DEFAULT 0,
    prior_cancellation_fee DECIMAL(10,4) DEFAULT 0,
    
    -- Transaction IDs for fees
    activation_fee_transaction_id INTEGER,
    cancellation_fee_transaction_id INTEGER,
    prior_cancellation_fee_transaction_id INTEGER,
    
    -- Framework Integration
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- USAGE & TIME VALIDATION ENGINE
-- =============================================================================

-- FUP (Fair Usage Policy) Policies
CREATE TABLE fup_policies (
    id SERIAL PRIMARY KEY,
    tariff_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    fixed_up BIGINT DEFAULT 0, -- bytes
    fixed_down BIGINT DEFAULT 0, -- bytes
    accounting_traffic BOOLEAN DEFAULT false,
    accounting_online BOOLEAN DEFAULT false,
    action VARCHAR(20) DEFAULT 'block', -- increase, decrease, block
    percent INTEGER DEFAULT 0,
    conditions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FUP Limits per tariff
CREATE TABLE fup_limits (
    tariff_id INTEGER PRIMARY KEY,
    cap_tariff_id INTEGER,
    traffic_from TIME DEFAULT '00:00:00',
    online_from TIME DEFAULT '00:00:00',
    traffic_to TIME DEFAULT '24:00:00',
    online_to TIME DEFAULT '24:00:00',
    traffic_days INTEGER[] DEFAULT ARRAY[1,2,3,4,5,6,7],
    online_days INTEGER[] DEFAULT ARRAY[1,2,3,4,5,6,7],
    action VARCHAR(20) DEFAULT 'block',
    percent INTEGER DEFAULT 0,
    traffic_amount BIGINT DEFAULT 0,
    traffic_direction VARCHAR(20) DEFAULT 'up_down',
    traffic_in VARCHAR(10) DEFAULT 'gb',
    override_traffic BOOLEAN DEFAULT false,
    online_amount INTEGER DEFAULT 0,
    online_in VARCHAR(20) DEFAULT 'hours',
    override_online BOOLEAN DEFAULT false,
    rollover_data BOOLEAN DEFAULT false,
    rollover_time BOOLEAN DEFAULT false,
    bonus_is_unlimited BOOLEAN DEFAULT true,
    bonus_traffic DECIMAL(10,4) DEFAULT 0,
    bonus_traffic_in VARCHAR(10),
    fixed_up BIGINT DEFAULT 0,
    fixed_down BIGINT DEFAULT 0,
    top_up_over_usage BOOLEAN DEFAULT false,
    top_up_trigger_percent INTEGER DEFAULT 0,
    use_bonus_when_normal_ended BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FUP Counters (per service)
CREATE TABLE fup_counters (
    service_id INTEGER PRIMARY KEY REFERENCES internet_services(id) ON DELETE CASCADE,
    day_up BIGINT DEFAULT 0,
    day_down BIGINT DEFAULT 0,
    day_time INTEGER DEFAULT 0, -- seconds
    day_bonus_up BIGINT DEFAULT 0,
    day_bonus_down BIGINT DEFAULT 0,
    week_up BIGINT DEFAULT 0,
    week_down BIGINT DEFAULT 0,
    week_bonus_up BIGINT DEFAULT 0,
    week_bonus_down BIGINT DEFAULT 0,
    week_time INTEGER DEFAULT 0,
    month_up BIGINT DEFAULT 0,
    month_down BIGINT DEFAULT 0,
    month_bonus_up BIGINT DEFAULT 0,
    month_bonus_down BIGINT DEFAULT 0,
    month_time INTEGER DEFAULT 0,
    cap_amount BIGINT DEFAULT 0,
    cap_used BIGINT DEFAULT 0,
    over_usage BIGINT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CAP Tariffs (Top-up data packages)
CREATE TABLE cap_tariffs (
    id SERIAL PRIMARY KEY,
    tariff_id INTEGER,
    title VARCHAR(255) NOT NULL,
    amount DECIMAL(10,4) NOT NULL,
    amount_in VARCHAR(10) DEFAULT 'mb', -- gb, mb
    price DECIMAL(10,4) DEFAULT 0,
    type VARCHAR(20) DEFAULT 'manual', -- manual, automatic
    validity VARCHAR(50) NOT NULL, -- end_of_period, unlimited, week_2, day_3, etc.
    to_invoice BOOLEAN DEFAULT false,
    transaction_category_id INTEGER REFERENCES transaction_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Capped Data (Allocated data packages per service)
CREATE TABLE capped_data (
    id SERIAL PRIMARY KEY,
    service_id INTEGER NOT NULL REFERENCES internet_services(id) ON DELETE CASCADE,
    quantity BIGINT DEFAULT 0, -- bytes
    quantity_remind BIGINT DEFAULT 0,
    tariff_id INTEGER REFERENCES cap_tariffs(id),
    over_usage BIGINT DEFAULT 0,
    valid_till TIMESTAMP,
    end_of_period TIMESTAMP,
    transaction_id INTEGER,
    price DECIMAL(10,4) DEFAULT 0,
    added_by VARCHAR(20) DEFAULT 'system',
    type VARCHAR(50) DEFAULT 'admin_top_up',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Traffic Counters (daily statistics)
CREATE TABLE customer_traffic_counters (
    service_id INTEGER NOT NULL REFERENCES internet_services(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    up BIGINT DEFAULT 0, -- bytes uploaded
    down BIGINT DEFAULT 0, -- bytes downloaded
    PRIMARY KEY (service_id, date),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bonus Traffic Counters
CREATE TABLE customer_bonus_traffic_counters (
    service_id INTEGER NOT NULL REFERENCES internet_services(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    up BIGINT DEFAULT 0,
    down BIGINT DEFAULT 0,
    PRIMARY KEY (service_id, date),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- DEVICE MANAGEMENT & IPAM
-- =============================================================================

-- Network Sites
CREATE TABLE network_sites (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    address TEXT,
    gps VARCHAR(100), -- coordinates
    location_id INTEGER NOT NULL REFERENCES locations(id),
    partners_ids INTEGER[] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monitoring Device Types
CREATE TABLE monitoring_device_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monitoring Groups
CREATE TABLE monitoring_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monitoring Producers
CREATE TABLE monitoring_producers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monitoring Devices
CREATE TABLE monitoring_devices (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    network_site_id INTEGER REFERENCES network_sites(id),
    parent_id INTEGER DEFAULT 0 REFERENCES monitoring_devices(id),
    producer INTEGER NOT NULL REFERENCES monitoring_producers(id),
    model VARCHAR(255),
    ip INET NOT NULL UNIQUE,
    snmp_port INTEGER DEFAULT 161,
    is_ping BOOLEAN DEFAULT true,
    active BOOLEAN DEFAULT true,
    snmp_community VARCHAR(100) DEFAULT 'public',
    snmp_version INTEGER DEFAULT 1,
    type INTEGER NOT NULL REFERENCES monitoring_device_types(id),
    monitoring_group INTEGER NOT NULL REFERENCES monitoring_groups(id),
    partners_ids INTEGER[] NOT NULL,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    address TEXT,
    send_notifications BOOLEAN DEFAULT true,
    gps VARCHAR(100),
    gps_area TEXT,
    delay_timer INTEGER DEFAULT 0,
    access_device BOOLEAN DEFAULT false,
    
    -- SNMP Status
    snmp_time BIGINT DEFAULT 0,
    snmp_uptime BIGINT DEFAULT 0,
    snmp_status INTEGER DEFAULT 9,
    snmp_status_1 INTEGER DEFAULT 9,
    snmp_status_2 INTEGER DEFAULT 9,
    snmp_status_3 INTEGER DEFAULT 9,
    snmp_status_4 INTEGER DEFAULT 9,
    snmp_status_5 INTEGER DEFAULT 9,
    snmp_state VARCHAR(20) DEFAULT 'unknown', -- up, down
    ping_state VARCHAR(20) DEFAULT 'unknown', -- up, down
    
    versions INTEGER[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Network Categories
CREATE TABLE network_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- IPv4 Networks
CREATE TABLE ipv4_networks (
    id SERIAL PRIMARY KEY,
    network INET NOT NULL,
    mask INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    comment TEXT,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    network_category INTEGER NOT NULL REFERENCES network_categories(id),
    network_type VARCHAR(20) DEFAULT 'endnet', -- rootnet, endnet
    type_of_usage VARCHAR(20) DEFAULT 'management', -- pool, static, management
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- IPv4 IP Addresses
CREATE TABLE ipv4_ips (
    id SERIAL PRIMARY KEY,
    ipv4_networks_id INTEGER NOT NULL REFERENCES ipv4_networks(id) ON DELETE CASCADE,
    ip INET NOT NULL,
    hostname VARCHAR(255),
    location_id INTEGER REFERENCES locations(id),
    title VARCHAR(255),
    comment TEXT,
    host_category INTEGER,
    is_used BOOLEAN DEFAULT false,
    status INTEGER DEFAULT 9, -- 0=OK, 1=Timeout, 2=Error, 9=Unknown
    last_check BIGINT DEFAULT 0,
    customer_id INTEGER REFERENCES customers(id),
    card_id INTEGER,
    module VARCHAR(100),
    module_item_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ipv4_networks_id, ip)
);

-- IPv6 Networks
CREATE TABLE ipv6_networks (
    id SERIAL PRIMARY KEY,
    network INET NOT NULL,
    prefix INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    comment TEXT,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    network_category INTEGER NOT NULL REFERENCES network_categories(id),
    network_type VARCHAR(20) DEFAULT 'endnet', -- rootnet, endnet
    type_of_usage VARCHAR(20) DEFAULT 'static', -- static, management
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- IPv6 IP Addresses
CREATE TABLE ipv6_ips (
    id SERIAL PRIMARY KEY,
    ipv6_networks_id INTEGER NOT NULL REFERENCES ipv6_networks(id) ON DELETE CASCADE,
    ip INET NOT NULL,
    ip_end INET,
    prefix INTEGER,
    location_id INTEGER REFERENCES locations(id),
    title VARCHAR(255),
    comment TEXT,
    host_category INTEGER,
    is_used BOOLEAN DEFAULT false,
    customer_id INTEGER REFERENCES customers(id),
    service_id INTEGER,
    card_id INTEGER,
    module VARCHAR(100),
    module_item_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Routers/NAS Devices
CREATE TABLE routers (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    model VARCHAR(255),
    partners_ids INTEGER[] NOT NULL,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    address TEXT,
    ip INET NOT NULL UNIQUE,
    gps TEXT, -- area coordinates
    gps_point VARCHAR(100), -- point coordinates
    authorization_method VARCHAR(50) DEFAULT 'none',
    accounting_method VARCHAR(50) DEFAULT 'none',
    nas_type INTEGER NOT NULL,
    nas_ip INET,
    radius_secret VARCHAR(255),
    status VARCHAR(20) DEFAULT 'unknown', -- ok, api_error, error, disabled, unknown
    pool_ids INTEGER[],
    
    -- Mikrotik API Configuration
    api_login VARCHAR(100),
    api_password VARCHAR(255),
    api_port INTEGER DEFAULT 8728,
    api_enable BOOLEAN DEFAULT false,
    api_status VARCHAR(20) DEFAULT 'unknown',
    shaper BOOLEAN DEFAULT false,
    shaper_id INTEGER,
    shaping_type VARCHAR(20) DEFAULT 'simple',
    
    -- Status tracking
    last_status TIMESTAMP,
    cpu_usage INTEGER DEFAULT 0,
    platform VARCHAR(100),
    board_name VARCHAR(100),
    version VARCHAR(100),
    connection_error INTEGER DEFAULT 0,
    last_api_error BOOLEAN DEFAULT false,
    is_used BOOLEAN DEFAULT false,
    pid INTEGER,
    used_date_time TIMESTAMP,
    change_status BOOLEAN DEFAULT false,
    change_authorization BOOLEAN DEFAULT false,
    change_shaping BOOLEAN DEFAULT false,
    last_connect TIMESTAMP,
    last_accounting TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Router Sectors (Traffic Shaping Profiles)
CREATE TABLE router_sectors (
    id SERIAL PRIMARY KEY,
    router_id INTEGER NOT NULL REFERENCES routers(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    speed_down INTEGER NOT NULL, -- kbps
    speed_up INTEGER NOT NULL, -- kbps
    limit_at INTEGER DEFAULT 95, -- percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INTEGRATED BILLING SYSTEM
-- =============================================================================

-- Payment Methods
CREATE TABLE payment_methods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    name_1 VARCHAR(255), -- Custom field 1
    name_2 VARCHAR(255), -- Custom field 2
    name_3 VARCHAR(255), -- Custom field 3
    name_4 VARCHAR(255), -- Custom field 4
    name_5 VARCHAR(255), -- Custom field 5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL, -- debit (income), credit (charge)
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    unit VARCHAR(50),
    price DECIMAL(10,4) NOT NULL,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    tax_id INTEGER REFERENCES taxes(id),
    total DECIMAL(10,4) NOT NULL,
    remind_amount DECIMAL(10,4) DEFAULT 0,
    date DATE NOT NULL,
    category INTEGER NOT NULL REFERENCES transaction_categories(id),
    description TEXT,
    period_from DATE,
    period_to DATE,
    service_id INTEGER,
    service_type VARCHAR(20), -- internet, voice, custom, bundle, one_time
    payment_id INTEGER,
    credit_note_id INTEGER,
    invoice_id INTEGER,
    invoiced_by_id INTEGER,
    comment TEXT,
    to_invoice BOOLEAN DEFAULT false,
    source VARCHAR(20) DEFAULT 'manual', -- manual, auto, cdr, config
    sub_account_id INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoices
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    number VARCHAR(50) UNIQUE NOT NULL,
    date_created DATE NOT NULL,
    date_updated DATE,
    date_till DATE,
    date_payment DATE,
    use_transactions BOOLEAN DEFAULT true,
    note TEXT,
    memo TEXT,
    status VARCHAR(20) DEFAULT 'not_paid', -- not_paid, paid, pending, deleted, overdue
    payment_id INTEGER,
    type VARCHAR(20) DEFAULT 'one_time', -- one_time, recurring
    payd_from_deposit BOOLEAN DEFAULT false,
    is_sent BOOLEAN DEFAULT false,
    total DECIMAL(10,4) DEFAULT 0,
    due DECIMAL(10,4) DEFAULT 0,
    real_create_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by VARCHAR(20) DEFAULT 'admin',
    added_by_id INTEGER,
    
    -- Framework Integration
    invoice_rules JSONB DEFAULT '{}', -- Applied business rules
    custom_fields JSONB DEFAULT '{}', -- Dynamic fields
    workflow_state JSONB DEFAULT '{}', -- Invoice workflow state
    template_used VARCHAR(100), -- Which template generated this invoice
    generation_context JSONB DEFAULT '{}', -- Context when generated
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice Items
CREATE TABLE invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit INTEGER,
    price DECIMAL(10,4) NOT NULL,
    tax DECIMAL(5,2) DEFAULT 0,
    period_from DATE,
    period_to DATE,
    category_id_for_transaction INTEGER REFERENCES transaction_categories(id),
    sub_account_id INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Credit Notes
CREATE TABLE credit_notes (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    number VARCHAR(50) UNIQUE NOT NULL,
    date_created DATE NOT NULL,
    date_updated DATE,
    date_payment DATE,
    status VARCHAR(20) DEFAULT 'not_refunded', -- not_refunded, refunded, deleted
    payment_id INTEGER,
    note TEXT,
    is_sent BOOLEAN DEFAULT false,
    total DECIMAL(10,4) DEFAULT 0,
    remind_amount DECIMAL(10,4) DEFAULT 0,
    real_create_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by VARCHAR(20) DEFAULT 'system',
    added_by_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Credit Note Items
CREATE TABLE credit_note_items (
    id SERIAL PRIMARY KEY,
    credit_note_id INTEGER NOT NULL REFERENCES credit_notes(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit INTEGER,
    price DECIMAL(10,4) NOT NULL,
    tax DECIMAL(5,2) DEFAULT 0,
    sub_account_id INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    invoice_id INTEGER REFERENCES invoices(id),
    credit_note_id INTEGER REFERENCES credit_notes(id),
    request_id INTEGER, -- proforma invoice
    transaction_id INTEGER REFERENCES transactions(id),
    payment_statement_id INTEGER,
    payment_type INTEGER NOT NULL REFERENCES payment_methods(id),
    receipt_number VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    amount DECIMAL(10,4) NOT NULL,
    comment TEXT,
    is_sent BOOLEAN DEFAULT false,
    field_1 TEXT, -- Custom fields for payment method
    field_2 TEXT,
    field_3 TEXT,
    field_4 TEXT,
    field_5 TEXT,
    note TEXT,
    memo TEXT,
    remind_amount DECIMAL(10,4) DEFAULT 0,
    real_create_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by VARCHAR(20) DEFAULT 'admin',
    added_by_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Proforma Invoices (Requests)
CREATE TABLE proforma_invoices (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    number VARCHAR(50) UNIQUE NOT NULL,
    date_created DATE NOT NULL,
    date_updated DATE,
    date_till DATE,
    date_payment DATE,
    status VARCHAR(20) DEFAULT 'not_paid', -- not_paid, paid, pending
    payment_id INTEGER REFERENCES payments(id),
    total DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Proforma Invoice Items
CREATE TABLE proforma_invoice_items (
    id SERIAL PRIMARY KEY,
    proforma_invoice_id INTEGER NOT NULL REFERENCES proforma_invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit INTEGER,
    price DECIMAL(10,4) NOT NULL,
    tax DECIMAL(5,2) DEFAULT 0,
    period_from DATE,
    period_to DATE,
    sub_account_id INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Additional Discounts (per service)
CREATE TABLE additional_discounts (
    id SERIAL PRIMARY KEY,
    service_type VARCHAR(20) NOT NULL, -- internet, voice, custom, bundle
    service_id INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT true,
    percent DECIMAL(5,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ACCOUNTING SYSTEM (NEW - Added for API alignment)
-- =============================================================================

-- Accounting Categories
CREATE TABLE accounting_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES accounting_categories(id),
    type VARCHAR(50) NOT NULL, -- income, expense, asset, liability, equity
    code VARCHAR(50) UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Journal Entries
CREATE TABLE journal_entries (
    id SERIAL PRIMARY KEY,
    entry_date DATE NOT NULL,
    description TEXT NOT NULL,
    reference_type VARCHAR(50), -- invoice, payment, adjustment, etc.
    reference_id INTEGER,
    status VARCHAR(20) DEFAULT 'posted', -- draft, posted, voided
    created_by INTEGER REFERENCES administrators(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Journal Entry Lines
CREATE TABLE journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_category_id INTEGER NOT NULL REFERENCES accounting_categories(id),
    debit DECIMAL(12,4) DEFAULT 0,
    credit DECIMAL(12,4) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- VOICE CDR SYSTEM (NEW - Added for API alignment)
-- =============================================================================

-- Voice Call Detail Records
CREATE TABLE voice_cdr (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    service_id INTEGER REFERENCES voice_services(id),
    call_date TIMESTAMP NOT NULL,
    call_type VARCHAR(20) NOT NULL, -- inbound, outbound, internal
    source VARCHAR(50) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    duration INTEGER NOT NULL, -- seconds
    billable_duration INTEGER NOT NULL, -- seconds
    cost DECIMAL(10,4) DEFAULT 0,
    rate_per_minute DECIMAL(10,4) DEFAULT 0,
    destination_type VARCHAR(50), -- local, national, international, mobile
    termination_cause VARCHAR(100),
    quality_score DECIMAL(3,2), -- 0.00 to 5.00
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CDR Summary (for performance)
CREATE TABLE voice_cdr_summary (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    service_id INTEGER REFERENCES voice_services(id),
    summary_date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    total_duration INTEGER DEFAULT 0, -- seconds
    total_cost DECIMAL(10,4) DEFAULT 0,
    inbound_calls INTEGER DEFAULT 0,
    outbound_calls INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, service_id, summary_date)
);

-- =============================================================================
-- SCHEDULING & JOBS SYSTEM (NEW - Added for API alignment)
-- =============================================================================

-- Scheduled Jobs
CREATE TABLE scheduled_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL, -- billing_run, backup, report_generation, etc.
    description TEXT,
    schedule_cron VARCHAR(100), -- Cron expression
    next_run TIMESTAMP,
    last_run TIMESTAMP,
    last_duration_seconds INTEGER,
    status VARCHAR(50) DEFAULT 'active', -- active, paused, disabled
    configuration JSONB DEFAULT '{}',
    retry_on_failure BOOLEAN DEFAULT true,
    max_retries INTEGER DEFAULT 3,
    created_by INTEGER REFERENCES administrators(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Execution History
CREATE TABLE job_execution_history (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES scheduled_jobs(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- running, completed, failed, cancelled
    output TEXT,
    error_message TEXT,
    records_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- WEBHOOKS SYSTEM (NEW - Added for API alignment)
-- =============================================================================

-- Webhook Configurations
CREATE TABLE webhook_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- customer.created, invoice.paid, etc.
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(255),
    headers JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    retry_count INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhook Event Log
CREATE TABLE webhook_events (
    id SERIAL PRIMARY KEY,
    webhook_config_id INTEGER NOT NULL REFERENCES webhook_configs(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    attempt_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    next_retry_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending', -- pending, delivered, failed
    response_status INTEGER, -- HTTP status code
    response_body TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- MESSAGES/COMMUNICATIONS SYSTEM (NEW - Added for API alignment)
-- =============================================================================

-- Message Queue
CREATE TABLE message_queue (
    id SERIAL PRIMARY KEY,
    recipient_type VARCHAR(50) NOT NULL, -- customer, admin, reseller
    recipient_id INTEGER NOT NULL,
    channel VARCHAR(50) NOT NULL, -- email, sms, whatsapp, push
    template_id INTEGER REFERENCES communication_templates(id),
    subject TEXT,
    body TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    priority INTEGER DEFAULT 5, -- 1-10, 1 is highest
    scheduled_for TIMESTAMP,
    status VARCHAR(50) DEFAULT 'queued', -- queued, processing, sent, failed
    attempts INTEGER DEFAULT 0,
    sent_at TIMESTAMP,
    error_message TEXT,
    provider_message_id VARCHAR(255), -- External provider's ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CONTACT MANAGEMENT SYSTEM
-- =============================================================================

-- Contact Types
CREATE TABLE contact_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- Technical, Billing, Administrative, Emergency
    description TEXT,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contacts (can be shared across customers)
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    position VARCHAR(100),
    department VARCHAR(100),
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Contact Associations
CREATE TABLE customer_contacts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    contact_type_id INTEGER NOT NULL REFERENCES contact_types(id),
    is_primary BOOLEAN DEFAULT false,
    receives_billing BOOLEAN DEFAULT false,
    receives_technical BOOLEAN DEFAULT false,
    receives_marketing BOOLEAN DEFAULT false,
    receives_outage_notifications BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, contact_id, contact_type_id)
);

-- =============================================================================
-- RESELLER MANAGEMENT SYSTEM
-- =============================================================================

-- Resellers
CREATE TABLE resellers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_reseller_id INTEGER REFERENCES resellers(id),
    level INTEGER DEFAULT 0, -- 0=direct, 1=sub-reseller, etc.
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, terminated
    
    -- Contact Information
    contact_person VARCHAR(255),
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    
    -- Financial Configuration
    default_markup_percent DECIMAL(5,2) DEFAULT 0, -- Default markup on services
    commission_percent DECIMAL(5,2) DEFAULT 0, -- Commission on sales
    credit_limit DECIMAL(12,4) DEFAULT 0,
    current_balance DECIMAL(12,4) DEFAULT 0,
    payment_terms INTEGER DEFAULT 30, -- days
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Business Configuration
    allowed_services JSONB DEFAULT '[]', -- Array of service types they can sell
    max_customers INTEGER DEFAULT 0, -- 0 = unlimited
    can_create_sub_resellers BOOLEAN DEFAULT false,
    white_label_enabled BOOLEAN DEFAULT false,
    
    -- Branding
    logo_url VARCHAR(500),
    brand_name VARCHAR(255),
    support_email VARCHAR(255),
    support_phone VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reseller Customer Associations
CREATE TABLE reseller_customers (
    id SERIAL PRIMARY KEY,
    reseller_id INTEGER NOT NULL REFERENCES resellers(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    assigned_date DATE DEFAULT CURRENT_DATE,
    commission_rate DECIMAL(5,2), -- Override default commission
    markup_rate DECIMAL(5,2), -- Override default markup
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id) -- Customer can only belong to one reseller
);

-- Reseller Commission Tracking
CREATE TABLE reseller_commissions (
    id SERIAL PRIMARY KEY,
    reseller_id INTEGER NOT NULL REFERENCES resellers(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    invoice_id INTEGER REFERENCES invoices(id),
    payment_id INTEGER REFERENCES payments(id),
    commission_type VARCHAR(50) NOT NULL, -- setup, recurring, usage, penalty
    base_amount DECIMAL(12,4) NOT NULL, -- Amount commission is calculated on
    commission_rate DECIMAL(5,2) NOT NULL,
    commission_amount DECIMAL(12,4) NOT NULL,
    period_start DATE,
    period_end DATE,
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, paid, cancelled
    paid_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reseller Service Pricing (custom pricing per reseller)
CREATE TABLE reseller_pricing (
    id SERIAL PRIMARY KEY,
    reseller_id INTEGER NOT NULL REFERENCES resellers(id) ON DELETE CASCADE,
    service_type VARCHAR(50) NOT NULL, -- internet, voice, custom, bundle
    tariff_id INTEGER NOT NULL,
    markup_type VARCHAR(20) DEFAULT 'percent', -- percent, fixed
    markup_value DECIMAL(10,4) NOT NULL,
    min_price DECIMAL(10,4),
    max_price DECIMAL(10,4),
    effective_from DATE DEFAULT CURRENT_DATE,
    effective_to DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reseller Portal Users (separate from admin users)
CREATE TABLE reseller_users (
    id SERIAL PRIMARY KEY,
    reseller_id INTEGER NOT NULL REFERENCES resellers(id) ON DELETE CASCADE,
    
    -- Authentication
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    
    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    position VARCHAR(100),
    department VARCHAR(100),
    
    -- Account Status
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, disabled, pending_verification
    email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP,
    
    -- Access Control
    role VARCHAR(50) DEFAULT 'user', -- admin, manager, user, readonly
    permissions JSONB DEFAULT '[]', -- Specific permissions array
    allowed_customer_ids INTEGER[] DEFAULT '{}', -- Restrict to specific customers
    ip_whitelist INET[] DEFAULT '{}', -- IP restrictions
    
    -- Session Management
    last_login TIMESTAMP,
    last_login_ip INET,
    current_session_id VARCHAR(255),
    session_expires TIMESTAMP,
    concurrent_sessions_allowed INTEGER DEFAULT 1,
    
    -- Security
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    force_password_change BOOLEAN DEFAULT false,
    
    -- Preferences
    timezone VARCHAR(100) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    notifications_enabled BOOLEAN DEFAULT true,
    
    -- Audit
    created_by INTEGER REFERENCES reseller_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- MASS INCIDENT MANAGEMENT SYSTEM
-- =============================================================================

-- Mass Incidents (Network outages affecting multiple customers)
CREATE TABLE mass_incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    incident_type VARCHAR(50) NOT NULL, -- outage, degradation, maintenance
    severity VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    status VARCHAR(20) DEFAULT 'investigating', -- investigating, identified, monitoring, resolved
    
    -- Affected Infrastructure
    affected_sites INTEGER[], -- network_site_ids
    affected_devices INTEGER[], -- monitoring_device_ids
    affected_routers INTEGER[], -- router_ids
    affected_networks JSONB DEFAULT '[]', -- IP ranges/networks affected
    
    -- Timeline
    started_at TIMESTAMP NOT NULL,
    estimated_resolution TIMESTAMP,
    resolved_at TIMESTAMP,
    
    -- Impact Assessment
    total_customers_affected INTEGER DEFAULT 0,
    business_customers_affected INTEGER DEFAULT 0,
    estimated_revenue_impact DECIMAL(12,4) DEFAULT 0,
    
    -- Response
    assigned_to INTEGER REFERENCES administrators(id),
    escalation_level INTEGER DEFAULT 1, -- 1=L1, 2=L2, 3=L3, 4=Management
    
    -- Customer Communication
    customer_notification_sent BOOLEAN DEFAULT false,
    notification_template_id INTEGER,
    public_status_page_visible BOOLEAN DEFAULT false,
    status_page_message TEXT,
    
    -- SLA Impact
    auto_credit_applied BOOLEAN DEFAULT false,
    manual_credit_required BOOLEAN DEFAULT false,
    credit_percentage DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mass Incident Updates (Timeline of incident progress)
CREATE TABLE mass_incident_updates (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES mass_incidents(id) ON DELETE CASCADE,
    update_type VARCHAR(50) NOT NULL, -- status_change, investigation_update, resolution_update
    message TEXT NOT NULL,
    internal_notes TEXT,
    status_before VARCHAR(20),
    status_after VARCHAR(20),
    posted_by INTEGER REFERENCES administrators(id),
    visible_to_customers BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Impact Assessment (per incident)
CREATE TABLE incident_customer_impact (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES mass_incidents(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Impact Details
    services_affected JSONB DEFAULT '[]', -- Array of affected service IDs and types
    impact_level VARCHAR(20) DEFAULT 'full', -- full, partial, minimal
    impact_start TIMESTAMP,
    impact_end TIMESTAMP,
    downtime_minutes INTEGER DEFAULT 0,
    
    -- Customer Communication
    notification_sent BOOLEAN DEFAULT false,
    notification_method VARCHAR(50), -- email, sms, phone, portal
    notification_sent_at TIMESTAMP,
    customer_acknowledged BOOLEAN DEFAULT false,
    customer_complaint_logged BOOLEAN DEFAULT false,
    
    -- SLA & Credits
    sla_breach BOOLEAN DEFAULT false,
    credit_applicable BOOLEAN DEFAULT false,
    credit_amount DECIMAL(10,4) DEFAULT 0,
    credit_processed BOOLEAN DEFAULT false,
    credit_note_id INTEGER REFERENCES credit_notes(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(incident_id, customer_id)
);

-- =============================================================================
-- INTEGRATED SUPPORT SYSTEM
-- =============================================================================

-- Ticket Statuses
CREATE TABLE ticket_statuses (
    id SERIAL PRIMARY KEY,
    title_for_agent VARCHAR(255) NOT NULL,
    title_for_customer VARCHAR(255) NOT NULL,
    label VARCHAR(50) DEFAULT 'default',
    mark VARCHAR(100)[], -- open, unresolved, closed
    icon VARCHAR(50) DEFAULT 'fa-tasks',
    view_on_dashboard BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ticket Groups
CREATE TABLE ticket_groups (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    agent_ids INTEGER[], -- admin IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ticket Types
CREATE TABLE ticket_types (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    background_color VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tickets
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    incoming_customer_id INTEGER,
    reporter_id INTEGER,
    reporter_type VARCHAR(20) DEFAULT 'admin', -- admin, customer, api, incoming, none
    hidden BOOLEAN DEFAULT false,
    assign_to INTEGER DEFAULT 0, -- admin ID
    status_id INTEGER NOT NULL REFERENCES ticket_statuses(id),
    group_id INTEGER REFERENCES ticket_groups(id),
    type_id INTEGER NOT NULL REFERENCES ticket_types(id),
    task_id INTEGER,
    subject TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, urgent
    star BOOLEAN DEFAULT false,
    unread_by_customer BOOLEAN DEFAULT false,
    unread_by_admin BOOLEAN DEFAULT false,
    closed BOOLEAN DEFAULT false,
    source VARCHAR(20) DEFAULT 'administration', -- administration, api, portal, widget, incoming
    trash BOOLEAN DEFAULT false,
    shareable BOOLEAN DEFAULT true,
    note TEXT,
    watching BOOLEAN DEFAULT false,
    related_account_id INTEGER DEFAULT 0,
    related_account_type VARCHAR(20) DEFAULT 'none', -- none, main, sub
    hidden_from_related_account BOOLEAN DEFAULT false,
    unread_by_related_account BOOLEAN DEFAULT true,
    
    -- Framework Integration
    ticket_rules JSONB DEFAULT '{}', -- Applied business rules
    custom_fields JSONB DEFAULT '{}', -- Dynamic fields
    workflow_state JSONB DEFAULT '{}', -- Ticket workflow state
    automation_history JSONB DEFAULT '[]', -- History of automated actions
    escalation_config JSONB DEFAULT '{}', -- Escalation rules
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ticket Messages
CREATE TABLE ticket_messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id),
    incoming_customer_id INTEGER DEFAULT 0,
    admin_id INTEGER REFERENCES administrators(id),
    api_id INTEGER DEFAULT 0,
    source VARCHAR(20) DEFAULT 'administration', -- administration, api, portal, public_form, incoming
    date DATE NOT NULL,
    time TIME NOT NULL,
    message TEXT NOT NULL,
    raw_message TEXT,
    is_merged BOOLEAN DEFAULT false,
    can_be_deleted BOOLEAN DEFAULT true,
    hide_for_customer BOOLEAN DEFAULT false,
    mail_to VARCHAR(255),
    sms_to VARCHAR(50)[],
    mail_cc VARCHAR(255),
    mail_bcc VARCHAR(255),
    author_type VARCHAR(20) DEFAULT 'admin', -- admin, customer, api, system
    message_type VARCHAR(20) DEFAULT 'message', -- message, note, change_ticket
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ticket Attachments
CREATE TABLE ticket_attachments (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES ticket_messages(id) ON DELETE CASCADE,
    type VARCHAR(50) DEFAULT 'ticket_attachment',
    filename_original VARCHAR(255) NOT NULL,
    filename_uploaded VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SLA Violations (automatic credit notes)
CREATE TABLE sla_violations (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    service_id INTEGER,
    service_type VARCHAR(20), -- internet, voice, custom
    ticket_id INTEGER REFERENCES tickets(id),
    violation_type VARCHAR(50) NOT NULL, -- response_time, resolution_time, uptime
    violation_start TIMESTAMP NOT NULL,
    violation_end TIMESTAMP,
    sla_target INTEGER, -- target in minutes or percentage
    actual_value INTEGER, -- actual value
    credit_amount DECIMAL(10,4) DEFAULT 0,
    credit_note_id INTEGER REFERENCES credit_notes(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, processed, ignored
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SLA Credit Reviews (Human oversight for automated credits)
CREATE TABLE sla_credit_reviews (
    id SERIAL PRIMARY KEY,
    violation_id INTEGER NOT NULL REFERENCES sla_violations(id) ON DELETE CASCADE,
    review_status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected, requires_info
    
    -- Review Details
    assigned_reviewer INTEGER REFERENCES administrators(id),
    review_priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    auto_calculated_credit DECIMAL(10,4) NOT NULL,
    reviewer_recommended_credit DECIMAL(10,4),
    final_approved_credit DECIMAL(10,4),
    
    -- Review Process
    review_notes TEXT,
    rejection_reason TEXT,
    requires_manager_approval BOOLEAN DEFAULT false,
    manager_approved_by INTEGER REFERENCES administrators(id),
    manager_approval_notes TEXT,
    
    -- Customer Communication
    customer_notified BOOLEAN DEFAULT false,
    customer_dispute BOOLEAN DEFAULT false,
    customer_dispute_notes TEXT,
    
    -- Workflow Timestamps
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_started_at TIMESTAMP,
    review_completed_at TIMESTAMP,
    credit_applied_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SLA Credit Approval Workflows
CREATE TABLE sla_credit_workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Trigger Conditions
    min_credit_amount DECIMAL(10,4) DEFAULT 0, -- Auto-approve below this amount
    max_auto_approve_amount DECIMAL(10,4) DEFAULT 0,
    violation_types VARCHAR(100)[], -- Which violation types this applies to
    customer_tiers VARCHAR(50)[], -- Which customer tiers this applies to
    
    -- Approval Requirements
    requires_l1_approval BOOLEAN DEFAULT false,
    requires_l2_approval BOOLEAN DEFAULT false,
    requires_manager_approval BOOLEAN DEFAULT false,
    
    -- Reviewers
    default_reviewer_group INTEGER REFERENCES ticket_groups(id),
    escalation_reviewer_group INTEGER REFERENCES ticket_groups(id),
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- BULK OPERATIONS SYSTEM
-- =============================================================================

-- Bulk Operations (Mass updates, imports, exports)
CREATE TABLE bulk_operations (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL, -- customer_import, service_update, billing_run, etc.
    operation_name VARCHAR(255) NOT NULL,
    initiated_by INTEGER REFERENCES administrators(id),
    
    -- Input Data
    input_source VARCHAR(50), -- csv_file, manual_selection, api_call
    input_file_path VARCHAR(500),
    input_data JSONB,
    
    -- Operation Configuration
    target_table VARCHAR(100),
    operation_mode VARCHAR(50), -- create, update, delete, mixed
    validation_rules JSONB DEFAULT '{}',
    dry_run BOOLEAN DEFAULT false,
    
    -- Progress Tracking
    status VARCHAR(20) DEFAULT 'queued', -- queued, running, completed, failed, cancelled
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    successful_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    skipped_records INTEGER DEFAULT 0,
    
    -- Results
    success_data JSONB DEFAULT '[]',
    error_data JSONB DEFAULT '[]',
    validation_errors JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_completion TIMESTAMP,
    
    -- Options
    rollback_on_failure BOOLEAN DEFAULT false,
    send_completion_notification BOOLEAN DEFAULT true,
    notification_email VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bulk Operation Details (Individual record results)
CREATE TABLE bulk_operation_details (
    id SERIAL PRIMARY KEY,
    bulk_operation_id INTEGER NOT NULL REFERENCES bulk_operations(id) ON DELETE CASCADE,
    record_index INTEGER NOT NULL,
    record_identifier VARCHAR(255), -- Could be ID, login, email, etc.
    operation_action VARCHAR(50), -- create, update, delete, skip
    status VARCHAR(20), -- success, failed, skipped, warning
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    warning_message TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INFRASTRUCTURE DEPENDENCY MAPPING
-- =============================================================================

-- Customer Infrastructure Dependencies
CREATE TABLE customer_infrastructure_dependencies (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Network Dependencies
    primary_router_id INTEGER REFERENCES routers(id),
    backup_router_id INTEGER REFERENCES routers(id),
    primary_monitoring_device_id INTEGER REFERENCES monitoring_devices(id),
    network_site_id INTEGER REFERENCES network_sites(id),
    
    -- Service Dependencies
    service_id INTEGER, -- Can reference any service type
    service_type VARCHAR(20), -- internet, voice, custom, bundle
    
    -- Physical Dependencies
    ipv4_pool_id INTEGER REFERENCES ipv4_networks(id),
    ipv6_pool_id INTEGER REFERENCES ipv6_networks(id),
    static_ip_id INTEGER REFERENCES ipv4_ips(id),
    
    -- Circuit/Connection Info
    circuit_id VARCHAR(100),
    port_number VARCHAR(50),
    vlan_id INTEGER,
    
    -- Dependency Type
    dependency_type VARCHAR(50) NOT NULL, -- primary, backup, monitoring, billing
    criticality VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_verified TIMESTAMP,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Infrastructure Impact Analysis (for planning)
CREATE TABLE infrastructure_impact_analysis (
    id SERIAL PRIMARY KEY,
    device_id INTEGER, -- Can reference routers, monitoring_devices, etc.
    device_type VARCHAR(50), -- router, monitoring_device, network_site
    
    -- Impact Scope
    total_customers_impacted INTEGER DEFAULT 0,
    business_customers_impacted INTEGER DEFAULT 0,
    residential_customers_impacted INTEGER DEFAULT 0,
    services_impacted JSONB DEFAULT '[]',
    
    -- Financial Impact
    estimated_revenue_impact_hourly DECIMAL(10,4) DEFAULT 0,
    estimated_sla_credits_required DECIMAL(10,4) DEFAULT 0,
    
    -- Analysis Date
    analysis_date DATE DEFAULT CURRENT_DATE,
    analyzed_by INTEGER REFERENCES administrators(id),
    
    -- Cache status (for performance)
    needs_refresh BOOLEAN DEFAULT false,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, device_type, analysis_date)
);

-- =============================================================================
-- NETWORK ACCESS & RADIUS
-- =============================================================================

-- RADIUS Sessions
CREATE TABLE radius_sessions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES internet_services(id),
    tariff_id INTEGER,
    partner_id INTEGER REFERENCES partners(id),
    nas_id INTEGER,
    login VARCHAR(255) NOT NULL,
    username_real VARCHAR(255),
    in_bytes BIGINT DEFAULT 0,
    out_bytes BIGINT DEFAULT 0,
    start_session TIMESTAMP NOT NULL,
    end_session TIMESTAMP,
    ipv4 INET,
    ipv6 INET,
    mac VARCHAR(17),
    call_to VARCHAR(50),
    port VARCHAR(50),
    price DECIMAL(10,4) DEFAULT 0,
    time_on INTEGER DEFAULT 0, -- seconds
    last_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(50) DEFAULT 'mikrotik_api',
    login_is VARCHAR(20) DEFAULT 'user',
    session_id VARCHAR(255),
    session_status VARCHAR(20) DEFAULT 'active', -- active, stopped
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Online Status
CREATE TABLE customers_online (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES internet_services(id),
    tariff_id INTEGER,
    partner_id INTEGER REFERENCES partners(id),
    nas_id INTEGER,
    login VARCHAR(255) NOT NULL,
    username_real VARCHAR(255),
    in_bytes BIGINT DEFAULT 0,
    out_bytes BIGINT DEFAULT 0,
    start_session TIMESTAMP NOT NULL,
    ipv4 INET,
    ipv6 INET,
    mac VARCHAR(17),
    call_to VARCHAR(50),
    port VARCHAR(50),
    price DECIMAL(10,4) DEFAULT 0,
    time_on INTEGER DEFAULT 0,
    last_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(50) DEFAULT 'mikrotik_api',
    login_is VARCHAR(20) DEFAULT 'user',
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ANALYTICS & REPORTING
-- =============================================================================

-- Customer Statistics (aggregated)
CREATE TABLE customer_statistics (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    service_id INTEGER,
    tariff_id INTEGER,
    partner_id INTEGER,
    nas_id INTEGER,
    login VARCHAR(255),
    in_bytes BIGINT DEFAULT 0,
    out_bytes BIGINT DEFAULT 0,
    start_date DATE,
    start_time TIME,
    end_date DATE,
    end_time TIME,
    ipv4 INET,
    ipv6 INET,
    mac VARCHAR(17),
    call_to VARCHAR(50),
    port VARCHAR(50),
    error INTEGER DEFAULT 0,
    error_repeat INTEGER DEFAULT 0,
    price DECIMAL(10,4) DEFAULT 0,
    session_id VARCHAR(255),
    terminate_cause VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Configuration
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    module VARCHAR(100) NOT NULL,
    path VARCHAR(100) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    partner_id INTEGER REFERENCES partners(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(module, path, key, partner_id)
);

-- =============================================================================
-- AUDIT & COMPLIANCE
-- =============================================================================

-- Audit Categories (for better organization and compliance)
CREATE TABLE audit_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    code VARCHAR(20) UNIQUE NOT NULL, -- For programmatic reference
    
    -- Risk & Compliance
    default_risk_level VARCHAR(20) DEFAULT 'low', -- low, medium, high, critical
    compliance_required BOOLEAN DEFAULT false,
    retention_years INTEGER DEFAULT 7,
    
    -- Monitoring
    real_time_alerts BOOLEAN DEFAULT false,
    alert_threshold INTEGER DEFAULT 100, -- Alert after N actions
    requires_approval BOOLEAN DEFAULT false,
    
    -- UI Configuration
    icon VARCHAR(50) DEFAULT 'fa-file-text',
    color VARCHAR(7) DEFAULT '#6c757d',
    display_order INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced Audit Logs (with missing fields)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    
    -- Actor Information
    user_type VARCHAR(20) NOT NULL, -- admin, customer, api, system, reseller
    user_id INTEGER,
    user_name VARCHAR(255), -- Store name for reference
    session_id VARCHAR(255),
    
    -- Action Details
    action VARCHAR(100) NOT NULL, -- create, update, delete, login, logout, etc.
    action_category VARCHAR(50), -- customer_mgmt, billing, support, network, etc.
    table_name VARCHAR(100),
    record_id INTEGER,
    
    -- Detailed Change Tracking
    before_values JSONB, -- Complete JSON of record before change
    after_values JSONB, -- Complete JSON of record after change
    changed_fields JSONB, -- Array of specific fields that changed
    
    -- Request Context
    ip_address INET,
    user_agent TEXT,
    request_url TEXT,
    request_method VARCHAR(10), -- GET, POST, PUT, DELETE
    request_payload JSONB, -- API request data
    
    -- Additional Context
    business_context VARCHAR(255), -- "Customer signup", "Billing cycle", etc.
    related_records JSONB, -- Related record IDs and types
    integration_source VARCHAR(100), -- Which system/integration caused this
    
    -- Compliance & Security
    risk_level VARCHAR(20) DEFAULT 'low', -- low, medium, high, critical
    compliance_tags VARCHAR(100)[], -- gdpr, pci, sox, etc.
    retention_period INTEGER DEFAULT 2555, -- days (7 years default)
    
    -- Performance Tracking
    execution_time_ms INTEGER, -- How long the operation took
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log Summaries (for performance on large datasets)
CREATE TABLE audit_log_summaries (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    user_type VARCHAR(20) NOT NULL,
    record_count INTEGER DEFAULT 0,
    high_risk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, table_name, action, user_type)
);

-- =============================================================================
-- CONTACT VERIFICATION SYSTEM
-- =============================================================================

-- Contact Verifications (email/phone verification tracking)
CREATE TABLE contact_verifications (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    verification_type VARCHAR(50) NOT NULL, -- email, phone, address
    verification_method VARCHAR(50) NOT NULL, -- code, link, call, mail
    
    -- Verification Details
    verification_token VARCHAR(255) UNIQUE NOT NULL,
    verification_code VARCHAR(20), -- For SMS/voice verification
    verification_target VARCHAR(255) NOT NULL, -- Email or phone being verified
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, verified, expired, failed
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Timing
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP,
    
    -- Metadata
    verification_ip INET,
    verification_user_agent TEXT,
    failure_reason TEXT,
    
    -- Security
    rate_limit_key VARCHAR(255), -- For rate limiting
    suspicious_activity BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Contact Preferences (detailed communication preferences)
CREATE TABLE customer_contact_preferences (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE, -- NULL = default for customer
    
    -- Communication Channels
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    phone_enabled BOOLEAN DEFAULT false,
    whatsapp_enabled BOOLEAN DEFAULT false,
    postal_enabled BOOLEAN DEFAULT false,
    push_notifications_enabled BOOLEAN DEFAULT false,
    
    -- Communication Types
    billing_notifications BOOLEAN DEFAULT true,
    service_notifications BOOLEAN DEFAULT true,
    outage_notifications BOOLEAN DEFAULT true,
    maintenance_notifications BOOLEAN DEFAULT true,
    marketing_communications BOOLEAN DEFAULT false,
    newsletter BOOLEAN DEFAULT false,
    product_updates BOOLEAN DEFAULT false,
    security_alerts BOOLEAN DEFAULT true,
    
    -- Frequency Preferences
    notification_frequency VARCHAR(50) DEFAULT 'immediate', -- immediate, daily, weekly, monthly
    digest_time TIME DEFAULT '09:00:00', -- Preferred time for digests
    timezone VARCHAR(100) DEFAULT 'UTC',
    
    -- Quiet Hours
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '08:00:00',
    quiet_hours_timezone VARCHAR(100) DEFAULT 'UTC',
    
    -- Language & Format
    preferred_language VARCHAR(10) DEFAULT 'en',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- GDPR Compliance
    consent_given BOOLEAN DEFAULT false,
    consent_date TIMESTAMP,
    consent_ip INET,
    consent_method VARCHAR(50), -- website, email, phone, paper
    consent_evidence TEXT, -- Reference to consent record
    data_processing_consent BOOLEAN DEFAULT false,
    marketing_consent BOOLEAN DEFAULT false,
    
    -- Opt-out Management
    global_opt_out BOOLEAN DEFAULT false,
    opt_out_date TIMESTAMP,
    opt_out_reason TEXT,
    easy_unsubscribe_token UUID DEFAULT gen_random_uuid(),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, contact_id)
);

-- =============================================================================
-- COMMUNICATION TEMPLATES SYSTEM
-- =============================================================================

-- Communication Templates (enhanced template system)
CREATE TABLE communication_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_code VARCHAR(100) UNIQUE NOT NULL, -- For programmatic reference
    
    -- Template Type & Category
    template_type VARCHAR(50) NOT NULL, -- email, sms, whatsapp, push, letter
    category VARCHAR(100) NOT NULL, -- billing, service, outage, marketing, etc.
    subcategory VARCHAR(100), -- payment_reminder, service_activation, etc.
    
    -- Content
    subject_template TEXT, -- For email/push notifications
    body_template TEXT NOT NULL,
    html_template TEXT, -- Rich HTML version for emails
    
    -- Template Variables
    available_variables JSONB DEFAULT '[]', -- List of available variables
    required_variables JSONB DEFAULT '[]', -- Variables that must be provided
    variable_descriptions JSONB DEFAULT '{}', -- Help text for variables
    
    -- Localization
    language VARCHAR(10) DEFAULT 'en',
    is_default_language BOOLEAN DEFAULT false,
    parent_template_id INTEGER REFERENCES communication_templates(id), -- For translations
    
    -- Targeting & Conditions
    customer_segments JSONB DEFAULT '[]', -- Which customer segments this applies to
    trigger_conditions JSONB DEFAULT '{}', -- When this template should be used
    priority INTEGER DEFAULT 0, -- Higher priority templates are preferred
    
    -- Formatting & Delivery
    format_type VARCHAR(50) DEFAULT 'text', -- text, html, markdown
    delivery_timing VARCHAR(50) DEFAULT 'immediate', -- immediate, scheduled, digest
    throttle_limit INTEGER DEFAULT 0, -- Max sends per hour (0 = unlimited)
    
    -- A/B Testing
    is_ab_test BOOLEAN DEFAULT false,
    ab_test_group VARCHAR(50), -- A, B, C, etc.
    ab_test_weight INTEGER DEFAULT 100, -- Percentage weight
    ab_test_ends_at TIMESTAMP,
    
    -- Approval Workflow
    status VARCHAR(50) DEFAULT 'draft', -- draft, pending_approval, approved, rejected, archived
    requires_approval BOOLEAN DEFAULT false,
    approved_by INTEGER REFERENCES administrators(id),
    approved_at TIMESTAMP,
    approval_notes TEXT,
    
    -- Usage Tracking
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    success_rate DECIMAL(5,2) DEFAULT 0, -- Delivery success rate
    open_rate DECIMAL(5,2) DEFAULT 0, -- Email open rate
    click_rate DECIMAL(5,2) DEFAULT 0, -- Click-through rate
    
    -- Version Control
    version_number INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    replaced_by INTEGER REFERENCES communication_templates(id),
    
    -- Compliance
    gdpr_compliant BOOLEAN DEFAULT true,
    retention_period INTEGER DEFAULT 365, -- Days to retain sending logs
    
    created_by INTEGER REFERENCES administrators(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Template Usage Logs (track template performance)
CREATE TABLE template_usage_logs (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES communication_templates(id) ON DELETE CASCADE,
    
    -- Delivery Details
    delivery_type VARCHAR(50) NOT NULL, -- email, sms, whatsapp, push
    recipient_type VARCHAR(50), -- customer, admin, reseller
    recipient_id INTEGER,
    recipient_address VARCHAR(255), -- Email/phone/etc.
    
    -- Message Content
    final_subject TEXT,
    final_body TEXT,
    variables_used JSONB,
    
    -- Delivery Status
    delivery_status VARCHAR(50) DEFAULT 'pending', -- pending, sent, delivered, failed, bounced
    delivery_provider VARCHAR(100), -- SendGrid, Twilio, etc.
    delivery_provider_id VARCHAR(255), -- Provider's message ID
    
    -- Tracking
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    bounced_at TIMESTAMP,
    complaint_at TIMESTAMP,
    
    -- Delivery Details
    delivery_attempts INTEGER DEFAULT 0,
    failure_reason TEXT,
    provider_response JSONB,
    
    -- Context
    triggered_by VARCHAR(100), -- invoice_created, payment_failed, etc.
    business_context JSONB, -- Additional context data
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Template A/B Test Results
CREATE TABLE template_ab_test_results (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES communication_templates(id) ON DELETE CASCADE,
    test_group VARCHAR(50) NOT NULL,
    
    -- Metrics
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,
    total_bounced INTEGER DEFAULT 0,
    total_complaints INTEGER DEFAULT 0,
    
    -- Calculated Rates
    delivery_rate DECIMAL(5,2) DEFAULT 0,
    open_rate DECIMAL(5,2) DEFAULT 0,
    click_rate DECIMAL(5,2) DEFAULT 0,
    bounce_rate DECIMAL(5,2) DEFAULT 0,
    complaint_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Statistical Significance
    is_statistically_significant BOOLEAN DEFAULT false,
    confidence_level DECIMAL(5,2) DEFAULT 0,
    winner_declared BOOLEAN DEFAULT false,
    
    test_period_start TIMESTAMP,
    test_period_end TIMESTAMP,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_id, test_group)
);

-- =============================================================================
-- FILE STORAGE SYSTEM (S3 Integration)
-- =============================================================================

-- Storage Providers Configuration
CREATE TABLE storage_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- AWS S3, MinIO, DigitalOcean Spaces, etc.
    provider_type VARCHAR(50) NOT NULL, -- s3, compatible_s3, local, etc.
    endpoint_url VARCHAR(500), -- S3 endpoint URL
    region VARCHAR(100),
    access_key_id VARCHAR(255),
    secret_access_key_encrypted TEXT, -- Encrypted storage
    bucket_name VARCHAR(255) NOT NULL,
    base_path VARCHAR(500) DEFAULT '', -- Base folder path in bucket
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- Configuration Options
    server_side_encryption BOOLEAN DEFAULT true,
    versioning_enabled BOOLEAN DEFAULT false,
    lifecycle_rules JSONB DEFAULT '[]',
    cors_configuration JSONB DEFAULT '{}',
    
    -- Performance Settings
    multipart_threshold BIGINT DEFAULT 67108864, -- 64MB
    max_concurrent_uploads INTEGER DEFAULT 10,
    upload_timeout INTEGER DEFAULT 300, -- seconds
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File Storage Registry
CREATE TABLE file_storage (
    id SERIAL PRIMARY KEY,
    
    -- File Identification
    file_uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL, -- UUID-based filename in storage
    file_extension VARCHAR(20),
    mime_type VARCHAR(255),
    file_size BIGINT NOT NULL, -- bytes
    checksum_md5 VARCHAR(32), -- MD5 hash for integrity
    checksum_sha256 VARCHAR(64), -- SHA256 hash for security
    
    -- Storage Location
    storage_provider_id INTEGER NOT NULL REFERENCES storage_providers(id),
    bucket_name VARCHAR(255) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL, -- Full path in storage
    storage_url VARCHAR(1000), -- Full S3 URL
    cdn_url VARCHAR(1000), -- CDN URL if configured
    
    -- File Metadata
    file_category VARCHAR(100), -- document, image, video, audio, archive, etc.
    file_purpose VARCHAR(100), -- invoice, ticket_attachment, customer_document, etc.
    is_public BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    encryption_key_id VARCHAR(255), -- KMS key ID if encrypted
    
    -- Access Control
    owner_type VARCHAR(50), -- customer, admin, system, reseller
    owner_id INTEGER,
    access_level VARCHAR(50) DEFAULT 'private', -- public, private, authenticated, role_based
    allowed_roles VARCHAR(100)[], -- Which roles can access
    
    -- Lifecycle Management
    expiry_date TIMESTAMP, -- When file should be deleted
    archive_date TIMESTAMP, -- When to move to archive storage
    is_archived BOOLEAN DEFAULT false,
    archive_storage_class VARCHAR(50), -- glacier, deep_archive, etc.
    
    -- Version Control
    version_number INTEGER DEFAULT 1,
    parent_file_id INTEGER REFERENCES file_storage(id), -- For versioned files
    is_latest_version BOOLEAN DEFAULT true,
    
    -- Usage Tracking
    download_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    access_log_enabled BOOLEAN DEFAULT false,
    
    -- Compliance & Retention
    retention_period INTEGER, -- days to retain
    legal_hold BOOLEAN DEFAULT false,
    compliance_tags VARCHAR(100)[],
    
    -- Upload Information
    uploaded_by_type VARCHAR(50), -- admin, customer, api, system
    uploaded_by_id INTEGER,
    upload_session_id VARCHAR(255),
    upload_ip INET,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File Access Logs (for compliance and security)
CREATE TABLE file_access_logs (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES file_storage(id) ON DELETE CASCADE,
    
    -- Access Details
    access_type VARCHAR(50) NOT NULL, -- download, view, delete, share
    access_method VARCHAR(50), -- direct_url, api, portal, email_link
    
    -- Accessor Information
    accessor_type VARCHAR(50), -- admin, customer, anonymous, api
    accessor_id INTEGER,
    accessor_name VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Request Details
    ip_address INET,
    user_agent TEXT,
    referer_url TEXT,
    request_headers JSONB,
    
    -- Response Details
    response_status INTEGER, -- HTTP status code
    bytes_transferred BIGINT,
    response_time_ms INTEGER,
    
    -- Security Context
    security_level VARCHAR(50), -- normal, elevated, suspicious
    authentication_method VARCHAR(100),
    access_granted BOOLEAN DEFAULT true,
    denial_reason TEXT,
    
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File Sharing & Temporary Access
CREATE TABLE file_shares (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES file_storage(id) ON DELETE CASCADE,
    
    -- Share Configuration
    share_token UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    share_type VARCHAR(50) DEFAULT 'temporary', -- temporary, permanent, password_protected
    password_hash VARCHAR(255), -- If password protected
    
    -- Access Control
    max_downloads INTEGER DEFAULT 1, -- 0 = unlimited
    current_downloads INTEGER DEFAULT 0,
    allowed_ips INET[], -- IP whitelist
    allowed_domains VARCHAR(255)[], -- Domain whitelist
    
    -- Timing
    expires_at TIMESTAMP,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Creator
    created_by_type VARCHAR(50), -- admin, customer, api
    created_by_id INTEGER,
    
    -- Usage Tracking
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Templates Storage
CREATE TABLE document_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(100) NOT NULL, -- invoice, contract, report, etc.
    
    -- Template File
    template_file_id INTEGER REFERENCES file_storage(id),
    
    -- Template Configuration
    variables JSONB DEFAULT '[]', -- Available template variables
    required_variables JSONB DEFAULT '[]',
    default_values JSONB DEFAULT '{}',
    
    -- Generation Settings
    output_format VARCHAR(50) DEFAULT 'pdf', -- pdf, docx, html
    paper_size VARCHAR(20) DEFAULT 'A4',
    orientation VARCHAR(20) DEFAULT 'portrait',
    
    -- Usage
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_system_template BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generated Documents Tracking
CREATE TABLE generated_documents (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES document_templates(id),
    generated_file_id INTEGER REFERENCES file_storage(id),
    
    -- Generation Context
    entity_type VARCHAR(100), -- customer, invoice, ticket, etc.
    entity_id INTEGER,
    generated_for_type VARCHAR(50), -- customer, admin, system
    generated_for_id INTEGER,
    
    -- Generation Data
    template_variables JSONB, -- Variables used for generation
    generation_status VARCHAR(50) DEFAULT 'completed', -- pending, completed, failed
    error_message TEXT,
    
    -- Usage
    download_count INTEGER DEFAULT 0,
    last_downloaded TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SPECIFIC FILE ASSOCIATIONS
-- =============================================================================

-- Customer Documents (Links to file_storage)
CREATE TABLE customer_documents (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES file_storage(id) ON DELETE CASCADE,
    
    -- Document Information
    document_type VARCHAR(100) NOT NULL, -- contract, id_copy, utility_bill, etc.
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Document Status
    status VARCHAR(50) DEFAULT 'uploaded', -- uploaded, verified, rejected, expired
    verification_status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected
    verified_by INTEGER REFERENCES administrators(id),
    verification_date TIMESTAMP,
    verification_notes TEXT,
    
    -- Document Properties
    is_required BOOLEAN DEFAULT false,
    is_sensitive BOOLEAN DEFAULT false,
    visible_to_customer BOOLEAN DEFAULT true,
    
    -- Contract Specific
    contract_start_date DATE,
    contract_end_date DATE,
    contract_value DECIMAL(12,4),
    auto_renewal BOOLEAN DEFAULT false,
    
    -- Compliance
    retention_years INTEGER DEFAULT 7,
    gdpr_category VARCHAR(100), -- personal_data, financial_data, etc.
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ticket Attachments (Links to file_storage)
CREATE TABLE ticket_file_attachments (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    message_id INTEGER REFERENCES ticket_messages(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES file_storage(id) ON DELETE CASCADE,
    
    -- Attachment Context
    attachment_type VARCHAR(50) DEFAULT 'customer_upload', -- customer_upload, agent_attachment, system_log
    is_internal BOOLEAN DEFAULT false, -- Only visible to agents
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice/Financial Document Storage
CREATE TABLE financial_document_files (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL, -- invoice, credit_note, payment_receipt, statement
    document_id INTEGER NOT NULL, -- References invoice, credit_note, payment, etc.
    file_id INTEGER NOT NULL REFERENCES file_storage(id) ON DELETE CASCADE,
    
    -- Document Properties
    is_original BOOLEAN DEFAULT true,
    is_customer_copy BOOLEAN DEFAULT false,
    is_official BOOLEAN DEFAULT true,
    
    -- Digital Signature
    is_digitally_signed BOOLEAN DEFAULT false,
    signature_algorithm VARCHAR(100),
    signature_timestamp TIMESTAMP,
    signature_certificate TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- STORAGE OPTIMIZATION & CLEANUP
-- =============================================================================

-- Storage Usage Statistics
CREATE TABLE storage_usage_stats (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    storage_provider_id INTEGER REFERENCES storage_providers(id),
    
    -- Usage Metrics
    total_files BIGINT DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    new_files_today INTEGER DEFAULT 0,
    deleted_files_today INTEGER DEFAULT 0,
    
    -- By Category
    documents_count BIGINT DEFAULT 0,
    documents_size_bytes BIGINT DEFAULT 0,
    images_count BIGINT DEFAULT 0,
    images_size_bytes BIGINT DEFAULT 0,
    videos_count BIGINT DEFAULT 0,
    videos_size_bytes BIGINT DEFAULT 0,
    archives_count BIGINT DEFAULT 0,
    archives_size_bytes BIGINT DEFAULT 0,
    
    -- Cost Estimation
    estimated_storage_cost DECIMAL(10,4) DEFAULT 0,
    estimated_transfer_cost DECIMAL(10,4) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, storage_provider_id)
);

-- File Cleanup Tasks
CREATE TABLE file_cleanup_tasks (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL, -- expire_old_files, archive_large_files, cleanup_temp_files
    
    -- Selection Criteria
    file_age_days INTEGER,
    file_size_min BIGINT, -- bytes
    file_categories VARCHAR(100)[],
    file_purposes VARCHAR(100)[],
    exclude_legal_hold BOOLEAN DEFAULT true,
    
    -- Execution
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    dry_run BOOLEAN DEFAULT true,
    scheduled_for TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    files_processed INTEGER DEFAULT 0,
    files_deleted INTEGER DEFAULT 0,
    files_archived INTEGER DEFAULT 0,
    space_freed_bytes BIGINT DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    error_log TEXT,
    
    created_by INTEGER REFERENCES administrators(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- DATA MIGRATION SUPPORT
-- =============================================================================

-- Migration Status
CREATE TABLE migration_status (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL, -- splynx, other
    migration_type VARCHAR(50) NOT NULL, -- full, customers, services, etc.
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    error_log TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migration Mappings (for data transformation)
CREATE TABLE migration_mappings (
    id SERIAL PRIMARY KEY,
    migration_id INTEGER REFERENCES migration_status(id) ON DELETE CASCADE,
    source_table VARCHAR(100) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    target_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- FRAMEWORK FOUNDATION - DYNAMIC ENTITY BUILDER
-- =============================================================================

-- Dynamic Entity Definitions
CREATE TABLE framework_entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- "EquipmentMaintenance", "CustomAssets"
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Dynamic Schema Definition
    schema JSONB NOT NULL, -- {fields:[{name,type,required,validation}]}
    ui_configuration JSONB DEFAULT '{}', -- Form layouts, list views, etc.
    api_configuration JSONB DEFAULT '{}', -- Auto-generated endpoint settings
    
    -- Table Management
    table_name VARCHAR(100) UNIQUE, -- Auto-generated or custom table name
    auto_create_table BOOLEAN DEFAULT true, -- Create physical table automatically
    
    -- Framework Settings
    is_system_entity BOOLEAN DEFAULT false, -- Core framework entities (customers, invoices)
    is_template_entity BOOLEAN DEFAULT false, -- Part of ISP/other solution templates
    is_customizable BOOLEAN DEFAULT true, -- Can users modify this entity?
    
    -- Access Control
    permissions JSONB DEFAULT '{}', -- {roles:["admin","reseller"], actions:["read","write"]}
    field_permissions JSONB DEFAULT '{}', -- Field-level access control
    
    -- Entity Relationships
    parent_entity_id INTEGER REFERENCES framework_entities(id),
    related_entities JSONB DEFAULT '[]', -- References to related entities
    
    -- Versioning & Change Management
    version_number INTEGER DEFAULT 1,
    change_log JSONB DEFAULT '[]', -- History of schema changes
    
    -- Metadata
    icon VARCHAR(100) DEFAULT 'fa-table',
    color VARCHAR(7) DEFAULT '#357bf2',
    sort_order INTEGER DEFAULT 0,
    
    created_by INTEGER REFERENCES administrators(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dynamic Field Definitions
CREATE TABLE framework_fields (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL REFERENCES framework_entities(id) ON DELETE CASCADE,
    
    -- Field Basic Info
    field_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL, -- text, number, date, boolean, select, reference, currency, email, phone
    
    -- Field Configuration
    field_config JSONB DEFAULT '{}', -- {max_length: 255, options: ["A","B"], precision: 2}
    validation_rules JSONB DEFAULT '{}', -- {required: true, min: 0, max: 100, regex: "pattern"}
    default_value TEXT,
    
    -- UI Configuration
    ui_component VARCHAR(100) DEFAULT 'input', -- input, select, textarea, datepicker, file_upload
    ui_config JSONB DEFAULT '{}', -- Component-specific settings
    display_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT true,
    is_editable BOOLEAN DEFAULT true,
    is_required BOOLEAN DEFAULT false,
    is_unique BOOLEAN DEFAULT false,
    is_indexed BOOLEAN DEFAULT false,
    
    -- Advanced Features
    is_system_field BOOLEAN DEFAULT false,
    is_computed BOOLEAN DEFAULT false,
    computation_formula TEXT, -- For calculated fields
    
    -- Relationships
    reference_entity_id INTEGER REFERENCES framework_entities(id),
    reference_display_field VARCHAR(100),
    cascade_delete BOOLEAN DEFAULT false,
    
    -- Field Permissions
    field_permissions JSONB DEFAULT '{}', -- Role-based field access
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(entity_id, field_name)
);

-- Dynamic Entity Data Storage (EAV pattern for custom fields)
CREATE TABLE framework_entity_data (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL REFERENCES framework_entities(id),
    record_id INTEGER NOT NULL, -- ID in the entity's table
    field_id INTEGER NOT NULL REFERENCES framework_fields(id),
    
    -- Value Storage (use appropriate column based on field type)
    value_text TEXT,
    value_number DECIMAL(20,6),
    value_date DATE,
    value_datetime TIMESTAMP,
    value_boolean BOOLEAN,
    value_json JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(entity_id, record_id, field_id)
);

-- =============================================================================
-- FRAMEWORK - VISUAL RULE ENGINE
-- =============================================================================

-- Business Rules
CREATE TABLE framework_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'automation', -- automation, validation, workflow, integration
    
    -- Rule Targeting
    entity_name VARCHAR(100) NOT NULL, -- Target entity (can reference framework_entities.name)
    trigger_event VARCHAR(100) NOT NULL, -- create, update, delete, status_change, custom_event
    
    -- Rule Logic (Visual Builder JSON)
    conditions JSONB NOT NULL, -- [{field:"status",operator:"equals",value:"overdue"}]
    actions JSONB NOT NULL, -- [{"action":"suspend_service","params":{}},{"action":"send_email"}]
    
    -- Advanced Logic
    condition_logic VARCHAR(10) DEFAULT 'AND', -- AND, OR for multiple conditions
    priority INTEGER DEFAULT 0, -- Execution order (higher = first)
    
    -- Execution Settings
    is_active BOOLEAN DEFAULT true,
    execution_mode VARCHAR(50) DEFAULT 'immediate', -- immediate, scheduled, manual
    schedule_cron VARCHAR(100), -- For scheduled rules
    
    -- Error Handling & Retry
    on_error VARCHAR(50) DEFAULT 'log', -- log, halt, continue, retry
    max_retries INTEGER DEFAULT 0,
    retry_delay_seconds INTEGER DEFAULT 60,
    
    -- Integration Hooks
    webhook_url VARCHAR(500), -- Call external webhook
    api_integration VARCHAR(100), -- Built-in integration name
    
    -- Usage Tracking
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_executed TIMESTAMP,
    last_error TEXT,
    avg_execution_time_ms INTEGER DEFAULT 0,
    
    -- Rule Builder Metadata
    visual_config JSONB DEFAULT '{}', -- UI builder state
    test_data JSONB DEFAULT '{}', -- Test scenarios
    
    created_by INTEGER REFERENCES administrators(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rule Execution History
CREATE TABLE framework_rule_history (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES framework_rules(id) ON DELETE CASCADE,
    
    -- Execution Context
    trigger_event VARCHAR(100),
    entity_record_id INTEGER,
    execution_time_ms INTEGER,
    
    -- Results
    status VARCHAR(50), -- success, failed, skipped, partial
    conditions_met BOOLEAN,
    actions_executed JSONB, -- Which actions ran successfully
    actions_failed JSONB, -- Which actions failed
    error_message TEXT,
    stack_trace TEXT,
    
    -- Context Data
    input_data JSONB, -- Data that triggered the rule
    output_data JSONB, -- Results of rule execution
    external_responses JSONB, -- Responses from webhooks/integrations
    
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- FRAMEWORK - FORM & SCREEN BUILDER
-- =============================================================================

-- Form Definitions
CREATE TABLE framework_forms (
    id SERIAL PRIMARY KEY,
    form_name VARCHAR(100) UNIQUE NOT NULL, -- "customer_signup_form", "equipment_maintenance_form"
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Form Association
    entity_id INTEGER REFERENCES framework_entities(id), -- Which entity this form is for
    form_type VARCHAR(50) DEFAULT 'create', -- create, edit, view, search, custom
    
    -- Form Definition
    fields JSONB NOT NULL, -- [{type:"text",name:"company_name",label:"Company Name",required:true}]
    layout JSONB DEFAULT '{}', -- {rows:[{cols:[{field:"name",width:6}]}]}
    validation_rules JSONB DEFAULT '{}', -- Form-level validation
    
    -- UI Configuration
    theme JSONB DEFAULT '{}', -- {colors,fonts,spacing}
    css_classes VARCHAR(500),
    custom_css TEXT,
    
    -- Form Behavior
    submit_action VARCHAR(100) DEFAULT 'save', -- save, save_and_continue, custom
    success_message TEXT DEFAULT 'Form submitted successfully',
    error_message TEXT DEFAULT 'Please check the form for errors',
    redirect_url VARCHAR(500), -- Where to go after submit
    
    -- Permissions & Access
    access_roles JSONB DEFAULT '[]', -- Which roles can use this form
    is_public BOOLEAN DEFAULT false, -- Public form (no login required)
    requires_approval BOOLEAN DEFAULT false,
    
    -- Advanced Features
    is_multi_step BOOLEAN DEFAULT false,
    steps_config JSONB DEFAULT '{}', -- Multi-step form configuration
    conditional_logic JSONB DEFAULT '{}', -- Show/hide fields based on values
    auto_save BOOLEAN DEFAULT false,
    
    -- Integration
    webhook_on_submit VARCHAR(500), -- Call webhook on form submit
    email_notifications JSONB DEFAULT '{}', -- Who to notify on submit
    
    -- Usage Tracking
    submission_count INTEGER DEFAULT 0,
    last_submission TIMESTAMP,
    
    created_by INTEGER REFERENCES administrators(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Form Submissions
CREATE TABLE framework_form_submissions (
    id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL REFERENCES framework_forms(id) ON DELETE CASCADE,
    
    -- Submission Data
    submission_data JSONB NOT NULL, -- All form field values
    files JSONB DEFAULT '[]', -- Uploaded files
    
    -- Submission Context
    submitted_by_type VARCHAR(50), -- admin, customer, anonymous, api
    submitted_by_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    
    -- Processing
    status VARCHAR(50) DEFAULT 'pending', -- pending, processed, approved, rejected
    processed_by INTEGER REFERENCES administrators(id),
    processing_notes TEXT,
    
    -- Integration Results
    entity_record_id INTEGER, -- ID of created/updated record
    webhook_responses JSONB DEFAULT '[]',
    email_sent BOOLEAN DEFAULT false,
    
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- =============================================================================
-- FRAMEWORK - PLUGIN MARKETPLACE
-- =============================================================================

-- Plugin Registry
CREATE TABLE framework_plugins (
    id SERIAL PRIMARY KEY,
    plugin_name VARCHAR(100) UNIQUE NOT NULL, -- "QuickBooksSync", "ZapierIntegration"
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Plugin Metadata
    version VARCHAR(20) NOT NULL,
    author VARCHAR(255),
    website VARCHAR(500),
    documentation_url VARCHAR(500),
    
    -- Plugin Definition
    manifest JSONB NOT NULL, -- Complete plugin definition
    endpoints JSONB DEFAULT '[]', -- [{path,method,handler}]
    webhooks JSONB DEFAULT '[]', -- Webhook definitions
    entities JSONB DEFAULT '[]', -- New entities this plugin creates
    fields JSONB DEFAULT '[]', -- Fields it adds to existing entities
    rules JSONB DEFAULT '[]', -- Business rules it includes
    
    -- Installation & Configuration
    installation_config JSONB DEFAULT '{}', -- Settings needed for installation
    default_config JSONB DEFAULT '{}', -- Default configuration values
    config_schema JSONB DEFAULT '{}', -- Configuration validation schema
    
    -- Plugin Status
    is_installed BOOLEAN DEFAULT false,
    is_enabled BOOLEAN DEFAULT false,
    installation_date TIMESTAMP,
    installed_by INTEGER REFERENCES administrators(id),
    
    -- Plugin Health
    status VARCHAR(50) DEFAULT 'inactive', -- active, inactive, error, updating
    last_health_check TIMESTAMP,
    health_data JSONB DEFAULT '{}',
    error_log TEXT,
    
    -- Dependencies
    required_plugins JSONB DEFAULT '[]', -- Other plugins this depends on
    incompatible_plugins JSONB DEFAULT '[]', -- Plugins that conflict
    minimum_framework_version VARCHAR(20),
    
    -- Security
    permissions_required JSONB DEFAULT '[]', -- What permissions plugin needs
    security_scan_status VARCHAR(50) DEFAULT 'pending', -- pending, passed, failed
    security_scan_date TIMESTAMP,
    
    -- Usage & Analytics
    install_count INTEGER DEFAULT 0,
    active_installations INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plugin Instances (Per-ISP installations)
CREATE TABLE framework_plugin_instances (
    id SERIAL PRIMARY KEY,
    plugin_id INTEGER NOT NULL REFERENCES framework_plugins(id) ON DELETE CASCADE,
    partner_id INTEGER NOT NULL REFERENCES partners(id), -- Which ISP installed this
    
    -- Instance Configuration
    instance_config JSONB DEFAULT '{}', -- ISP-specific settings
    api_credentials JSONB DEFAULT '{}', -- Encrypted credentials
    
    -- Instance Status
    is_active BOOLEAN DEFAULT true,
    health_status VARCHAR(50) DEFAULT 'unknown',
    last_sync TIMESTAMP,
    sync_errors JSONB DEFAULT '[]',
    
    -- Usage Tracking
    request_count INTEGER DEFAULT 0,
    last_request TIMESTAMP,
    data_sync_count INTEGER DEFAULT 0,
    
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(plugin_id, partner_id)
);

-- =============================================================================
-- FRAMEWORK - REPORTING ENGINE
-- =============================================================================

-- Report Templates
CREATE TABLE framework_reports (
    id SERIAL PRIMARY KEY,
    report_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Report Definition
    data_source VARCHAR(100), -- Entity name or custom query
    fields JSONB NOT NULL, -- [{field,label,type,aggregation}]
    filters JSONB DEFAULT '[]', -- [{field,operator,value}]
    grouping JSONB DEFAULT '[]', -- Group by fields
    sorting JSONB DEFAULT '[]', -- Sort configuration
    
    -- Visualization
    chart_type VARCHAR(50) DEFAULT 'table', -- table, bar, line, pie, etc.
    chart_config JSONB DEFAULT '{}', -- Chart-specific settings
    
    -- Report Settings
    is_scheduled BOOLEAN DEFAULT false,
    schedule_cron VARCHAR(100), -- When to generate
    email_recipients JSONB DEFAULT '[]', -- Who gets scheduled reports
    
    -- Access Control
    access_roles JSONB DEFAULT '[]',
    is_public BOOLEAN DEFAULT false,
    
    -- Usage Tracking
    view_count INTEGER DEFAULT 0,
    last_viewed TIMESTAMP,
    generation_count INTEGER DEFAULT 0,
    
    created_by INTEGER REFERENCES administrators(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- FRAMEWORK - PERMISSION SYSTEM
-- =============================================================================

-- Permission Definitions
CREATE TABLE framework_permissions (
    id SERIAL PRIMARY KEY,
    permission_name VARCHAR(100) UNIQUE NOT NULL, -- "customers.read", "invoices.write"
    display_name VARCHAR(255),
    category VARCHAR(100), -- entity, system, integration, custom
    description TEXT,
    
    -- Permission Targeting
    resource_type VARCHAR(100), -- entity, field, action, api_endpoint, plugin
    resource_name VARCHAR(255), -- Specific resource identifier
    
    -- Access Definition
    actions JSONB DEFAULT '[]', -- ["read","write","delete","admin"]
    conditions JSONB DEFAULT '{}', -- {customer_location:[1,2], tier:"premium"}
    field_restrictions JSONB DEFAULT '{}', -- Field-level access rules
    
    -- Permission Metadata
    is_system_permission BOOLEAN DEFAULT false,
    is_dangerous BOOLEAN DEFAULT false, -- Requires extra confirmation
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Role Definitions
CREATE TABLE framework_roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    
    -- Role Configuration
    permissions JSONB DEFAULT '[]', -- Permission IDs or names
    inherits_from INTEGER REFERENCES framework_roles(id), -- Role inheritance
    
    -- Role Metadata
    is_system_role BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    max_users INTEGER DEFAULT 0, -- 0 = unlimited
    
    -- Role Restrictions
    ip_whitelist INET[],
    time_restrictions JSONB DEFAULT '{}', -- {hours:[9,17], days:[1,2,3,4,5]}
    session_timeout_minutes INTEGER DEFAULT 480,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Role Assignments
CREATE TABLE framework_user_roles (
    id SERIAL PRIMARY KEY,
    user_type VARCHAR(50) NOT NULL, -- admin, customer, reseller_user
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL REFERENCES framework_roles(id),
    
    -- Assignment Context
    granted_by INTEGER,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Override Settings
    custom_permissions JSONB DEFAULT '{}', -- Additional permissions
    restricted_permissions JSONB DEFAULT '[]', -- Remove specific permissions
    
    UNIQUE(user_type, user_id, role_id)
);

-- =============================================================================
-- FRAMEWORK - TEMPLATE SYSTEM
-- =============================================================================

-- Solution Templates
CREATE TABLE framework_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    
    -- Template Configuration
    template_data JSONB NOT NULL, -- Complete template definition
    version VARCHAR(20) DEFAULT '1.0.0',
    
    -- Template Metadata
    category VARCHAR(100), -- ISP, CRM, Inventory, etc.
    tags VARCHAR(100)[],
    author VARCHAR(255),
    license VARCHAR(100),
    
    -- Installation
    is_installed BOOLEAN DEFAULT false,
    installation_date TIMESTAMP,
    installation_notes TEXT,
    
    -- Updates
    update_available BOOLEAN DEFAULT false,
    latest_version VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Template Components
CREATE TABLE framework_template_components (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES framework_templates(id) ON DELETE CASCADE,
    component_type VARCHAR(100) NOT NULL, -- entity, rule, workflow, integration
    component_name VARCHAR(255) NOT NULL,
    component_data JSONB NOT NULL,
    installation_order INTEGER DEFAULT 0,
    
    -- Dependencies
    depends_on INTEGER[], -- Other component IDs
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- FRAMEWORK - USAGE & ANALYTICS
-- =============================================================================

-- Framework Usage Statistics
CREATE TABLE framework_usage_stats (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    
    -- Entity Usage
    entity_id INTEGER REFERENCES framework_entities(id),
    operation_type VARCHAR(50), -- create, read, update, delete
    operation_count INTEGER DEFAULT 0,
    
    -- Performance Metrics
    avg_response_time_ms DECIMAL(10,2),
    error_count INTEGER DEFAULT 0,
    
    -- User Activity
    active_users INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, entity_id, operation_type)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Customer indexes
CREATE INDEX idx_customers_partner_location ON customers(partner_id, location_id);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_login ON customers(login);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_custom_fields ON customers USING GIN(custom_fields);

-- Service indexes
CREATE INDEX idx_internet_services_customer ON internet_services(customer_id);
CREATE INDEX idx_internet_services_tariff ON internet_services(tariff_id);
CREATE INDEX idx_internet_services_status ON internet_services(status);
CREATE INDEX idx_internet_services_custom_fields ON internet_services USING GIN(custom_fields);
CREATE INDEX idx_voice_services_customer ON voice_services(customer_id);
CREATE INDEX idx_recurring_services_customer ON recurring_services(customer_id);
CREATE INDEX idx_bundle_services_customer ON bundle_services(customer_id);

-- Financial indexes
CREATE INDEX idx_transactions_customer ON transactions(customer_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_custom_fields ON invoices USING GIN(custom_fields);
CREATE INDEX idx_payments_customer ON payments(customer_id);
CREATE INDEX idx_credit_notes_customer ON credit_notes(customer_id);

-- Network indexes
CREATE INDEX idx_ipv4_ips_network ON ipv4_ips(ipv4_networks_id);
CREATE INDEX idx_ipv4_ips_customer ON ipv4_ips(customer_id);
CREATE INDEX idx_ipv6_ips_network ON ipv6_ips(ipv6_networks_id);
CREATE INDEX idx_radius_sessions_customer ON radius_sessions(customer_id);
CREATE INDEX idx_radius_sessions_service ON radius_sessions(service_id);
CREATE INDEX idx_monitoring_devices_ip ON monitoring_devices(ip);
CREATE INDEX idx_routers_ip ON routers(ip);

-- Support indexes
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status_id);
CREATE INDEX idx_tickets_assign ON tickets(assign_to);
CREATE INDEX idx_tickets_custom_fields ON tickets USING GIN(custom_fields);
CREATE INDEX idx_ticket_messages_ticket ON ticket_messages(ticket_id);

-- Usage tracking indexes
CREATE INDEX idx_traffic_counters_service_date ON customer_traffic_counters(service_id, date);
CREATE INDEX idx_fup_counters_service ON fup_counters(service_id);
CREATE INDEX idx_voice_cdr_customer_date ON voice_cdr(customer_id, call_date);
CREATE INDEX idx_voice_cdr_summary_customer_date ON voice_cdr_summary(customer_id, summary_date);

-- Reseller indexes
CREATE INDEX idx_reseller_customers_reseller ON reseller_customers(reseller_id);
CREATE INDEX idx_reseller_commissions_reseller ON reseller_commissions(reseller_id);
CREATE INDEX idx_reseller_users_reseller ON reseller_users(reseller_id);

-- Incident management indexes
CREATE INDEX idx_mass_incidents_status ON mass_incidents(status);
CREATE INDEX idx_incident_customer_impact_incident ON incident_customer_impact(incident_id);
CREATE INDEX idx_incident_customer_impact_customer ON incident_customer_impact(customer_id);

-- File storage indexes
CREATE INDEX idx_file_storage_uuid ON file_storage(file_uuid);
CREATE INDEX idx_file_storage_owner ON file_storage(owner_type, owner_id);
CREATE INDEX idx_file_storage_category ON file_storage(file_category);
CREATE INDEX idx_file_storage_purpose ON file_storage(file_purpose);
CREATE INDEX idx_file_storage_created ON file_storage(created_at);
CREATE INDEX idx_file_storage_expiry ON file_storage(expiry_date);
CREATE INDEX idx_file_storage_size ON file_storage(file_size);
CREATE INDEX idx_file_storage_public ON file_storage(is_public);
CREATE INDEX idx_file_storage_provider ON file_storage(storage_provider_id);

CREATE INDEX idx_file_access_logs_file ON file_access_logs(file_id);
CREATE INDEX idx_file_access_logs_accessed ON file_access_logs(accessed_at);
CREATE INDEX idx_file_access_logs_accessor ON file_access_logs(accessor_type, accessor_id);

CREATE INDEX idx_file_shares_file ON file_shares(file_id);
CREATE INDEX idx_file_shares_token ON file_shares(share_token);
CREATE INDEX idx_file_shares_expires ON file_shares(expires_at);

CREATE INDEX idx_customer_documents_customer ON customer_documents(customer_id);
CREATE INDEX idx_customer_documents_file ON customer_documents(file_id);
CREATE INDEX idx_customer_documents_type ON customer_documents(document_type);

CREATE INDEX idx_ticket_file_attachments_ticket ON ticket_file_attachments(ticket_id);
CREATE INDEX idx_ticket_file_attachments_file ON ticket_file_attachments(file_id);

CREATE INDEX idx_financial_document_files_type_id ON financial_document_files(document_type, document_id);
CREATE INDEX idx_financial_document_files_file ON financial_document_files(file_id);

-- Framework indexes
CREATE INDEX idx_framework_entities_name ON framework_entities(name);
CREATE INDEX idx_framework_entities_template ON framework_entities(is_template_entity);
CREATE INDEX idx_framework_fields_entity ON framework_fields(entity_id);
CREATE INDEX idx_framework_rules_entity ON framework_rules(entity_name);
CREATE INDEX idx_framework_rules_event ON framework_rules(trigger_event);
CREATE INDEX idx_framework_entity_data_lookup ON framework_entity_data(entity_id, record_id, field_id);
CREATE INDEX idx_framework_forms_entity ON framework_forms(entity_id);
CREATE INDEX idx_framework_form_submissions_form ON framework_form_submissions(form_id);
CREATE INDEX idx_framework_plugins_name ON framework_plugins(plugin_name);
CREATE INDEX idx_framework_plugin_instances_plugin ON framework_plugin_instances(plugin_id);

-- Audit indexes
CREATE INDEX idx_audit_logs_user ON audit_logs(user_type, user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_date ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_risk ON audit_logs(risk_level);

-- Communication indexes
CREATE INDEX idx_communication_templates_code ON communication_templates(template_code);
CREATE INDEX idx_communication_templates_type ON communication_templates(template_type);
CREATE INDEX idx_template_usage_logs_template ON template_usage_logs(template_id);
CREATE INDEX idx_message_queue_status ON message_queue(status);
CREATE INDEX idx_message_queue_scheduled ON message_queue(scheduled_for);

-- Job/Schedule indexes
CREATE INDEX idx_scheduled_jobs_type ON scheduled_jobs(job_type);
CREATE INDEX idx_scheduled_jobs_status ON scheduled_jobs(status);
CREATE INDEX idx_scheduled_jobs_next_run ON scheduled_jobs(next_run);
CREATE INDEX idx_job_execution_history_job ON job_execution_history(job_id);

-- Webhook indexes
CREATE INDEX idx_webhook_configs_event ON webhook_configs(event_type);
CREATE INDEX idx_webhook_configs_active ON webhook_configs(is_active);
CREATE INDEX idx_webhook_events_config ON webhook_events(webhook_config_id);
CREATE INDEX idx_webhook_events_status ON webhook_events(status);

-- =============================================================================
-- INITIAL DATA SETUP
-- =============================================================================

-- Insert Framework Configuration
INSERT INTO framework_config (config_key, config_value, config_type, description) VALUES 
('framework.version', '"2.0.0"', 'string', 'Current framework version with full builder capabilities'),
('framework.installation_date', to_jsonb(CURRENT_TIMESTAMP), 'string', 'Framework installation date'),
('framework.template_registry_url', '"https://templates.dotmac.ng"', 'string', 'Template registry URL'),
('framework.plugin_marketplace_url', '"https://plugins.dotmac.ng"', 'string', 'Plugin marketplace URL'),
('isp_template.enabled', 'true', 'boolean', 'ISP solution template enabled'),
('framework.auto_backup', 'true', 'boolean', 'Automatic backup enabled'),
('framework.audit_retention_days', '2555', 'number', 'Audit log retention period'),
('framework.builder_mode', 'true', 'boolean', 'Enable visual builder interfaces'),
('framework.auto_api_generation', 'true', 'boolean', 'Automatically generate APIs for new entities'),
('framework.rule_engine_enabled', 'true', 'boolean', 'Visual rule engine enabled');

-- Insert default partner
INSERT INTO partners (id, name, framework_config, branding_config) VALUES 
(1, 'Default ISP', '{"template": "isp_solution", "version": "1.0.0"}', 
 '{"primary_color": "#357bf2", "logo_url": null, "company_name": "Default ISP"}')
ON CONFLICT (id) DO NOTHING;

-- Insert default location
INSERT INTO locations (id, name, city, country, timezone) VALUES 
(1, 'Default Location', 'Lagos', 'Nigeria', 'Africa/Lagos')
ON CONFLICT (id) DO NOTHING;

-- Insert default transaction categories
INSERT INTO transaction_categories (id, name, is_base) VALUES 
(1, 'Service Charges', true),
(2, 'Payments', true),
(3, 'Adjustments', true),
(4, 'Penalties', true),
(5, 'Discounts', true)
ON CONFLICT (id) DO NOTHING;

-- Insert default taxes
INSERT INTO taxes (id, name, rate, type) VALUES 
(1, 'No Tax', 0.0000, 'single'),
(2, 'Standard VAT', 0.0750, 'single')
ON CONFLICT (id) DO NOTHING;

-- Insert default payment methods
INSERT INTO payment_methods (id, name, name_1, name_2) VALUES 
(1, 'Cash', 'Receipt Number', 'Location'),
(2, 'Bank Transfer', 'Account Number', 'Transaction ID'),
(3, 'Credit Card', 'Card Number', 'Transaction ID')
ON CONFLICT (id) DO NOTHING;

-- Insert default ticket statuses
INSERT INTO ticket_statuses (id, title_for_agent, title_for_customer, label, mark) VALUES 
(1, 'New', 'New', 'primary', ARRAY['open', 'unresolved']),
(2, 'In Progress', 'In Progress', 'warning', ARRAY['open', 'unresolved']),
(3, 'Resolved', 'Resolved', 'success', ARRAY['closed']),
(4, 'Closed', 'Closed', 'default', ARRAY['closed'])
ON CONFLICT (id) DO NOTHING;

-- Insert default ticket types
INSERT INTO ticket_types (id, title) VALUES 
(1, 'Technical Support'),
(2, 'Billing Inquiry'),
(3, 'Service Request'),
(4, 'Complaint')
ON CONFLICT (id) DO NOTHING;

-- Insert default network categories
INSERT INTO network_categories (id, name) VALUES 
(1, 'Customer Networks'),
(2, 'Infrastructure'),
(3, 'Management')
ON CONFLICT (id) DO NOTHING;

-- Insert default monitoring types
INSERT INTO monitoring_device_types (id, name) VALUES 
(1, 'Router'),
(2, 'Switch'),
(3, 'Access Point'),
(4, 'Server')
ON CONFLICT (id) DO NOTHING;

INSERT INTO monitoring_groups (id, name) VALUES 
(1, 'Core Network'),
(2, 'Access Layer'),
(3, 'Customer Equipment')
ON CONFLICT (id) DO NOTHING;

INSERT INTO monitoring_producers (id, name) VALUES 
(1, 'MikroTik'),
(2, 'Ubiquiti'),
(3, 'Cisco'),
(4, 'Generic SNMP')
ON CONFLICT (id) DO NOTHING;

-- Insert default contact types
INSERT INTO contact_types (id, name, description, is_default) VALUES
(1, 'Technical', 'Technical contact for network and service issues', true),
(2, 'Billing', 'Billing and financial contact', true),
(3, 'Administrative', 'General administrative contact', true),
(4, 'Emergency', '24/7 emergency contact', false)
ON CONFLICT (id) DO NOTHING;

-- Insert default audit categories
INSERT INTO audit_categories (id, name, code, description, default_risk_level) VALUES
(1, 'Customer Management', 'CUST_MGMT', 'Customer account operations', 'low'),
(2, 'Financial Operations', 'FIN_OPS', 'Billing, payments, and financial transactions', 'high'),
(3, 'Network Configuration', 'NET_CONFIG', 'Network and device configuration changes', 'medium'),
(4, 'User Authentication', 'USER_AUTH', 'Login, logout, and authentication events', 'medium'),
(5, 'System Configuration', 'SYS_CONFIG', 'System settings and configuration changes', 'high')
ON CONFLICT (id) DO NOTHING;

-- Insert default accounting categories
INSERT INTO accounting_categories (id, name, type, code) VALUES
(1, 'Service Revenue', 'income', 'REV001'),
(2, 'Installation Revenue', 'income', 'REV002'),
(3, 'Equipment Sales', 'income', 'REV003'),
(4, 'Network Infrastructure', 'expense', 'EXP001'),
(5, 'Salaries & Wages', 'expense', 'EXP002'),
(6, 'Utilities', 'expense', 'EXP003'),
(7, 'Cash & Bank', 'asset', 'AST001'),
(8, 'Accounts Receivable', 'asset', 'AST002'),
(9, 'Equipment', 'asset', 'AST003'),
(10, 'Accounts Payable', 'liability', 'LIA001'),
(11, 'Deferred Revenue', 'liability', 'LIA002')
ON CONFLICT (id) DO NOTHING;

-- Insert framework entity definitions for ISP template
INSERT INTO framework_entities (name, display_name, table_name, description, is_system_entity, is_template_entity, schema) VALUES
('customers', 'Customers', 'customers', 'Customer management entity', true, true, 
 '{
   "fields": [
     {"name": "name", "type": "text", "required": true},
     {"name": "email", "type": "email"},
     {"name": "phone", "type": "phone"},
     {"name": "status", "type": "select", "options": ["new", "active", "blocked", "disabled"]}
   ]
 }'),
('services', 'Services', 'internet_services', 'Service management entity', true, true,
 '{
   "fields": [
     {"name": "description", "type": "text", "required": true},
     {"name": "status", "type": "select", "options": ["active", "stopped", "disabled", "pending"]},
     {"name": "unit_price", "type": "currency"}
   ]
 }'),
('invoices', 'Invoices', 'invoices', 'Billing and invoice management', true, true,
 '{
   "fields": [
     {"name": "number", "type": "text", "required": true},
     {"name": "total", "type": "currency"},
     {"name": "status", "type": "select", "options": ["not_paid", "paid", "pending", "deleted"]}
   ]
 }'),
('tickets', 'Support Tickets', 'tickets', 'Customer support and ticketing', true, true,
 '{
   "fields": [
     {"name": "subject", "type": "text", "required": true},
     {"name": "priority", "type": "select", "options": ["low", "medium", "high", "urgent"]}
   ]
 }')
ON CONFLICT (name) DO NOTHING;

-- Insert sample business rules
INSERT INTO framework_rules (rule_name, description, entity_name, trigger_event, conditions, actions, is_active) VALUES
('Auto-suspend overdue customers', 'Automatically suspend customers with overdue payments > 30 days', 'customers', 'payment_overdue', 
 '[{"field": "overdue_days", "operator": ">=", "value": 30}]',
 '[{"action": "update_field", "params": {"field": "status", "value": "blocked"}}, {"action": "suspend_services"}]',
 true),
('Welcome new customer', 'Send welcome email to new customers', 'customers', 'create',
 '[{"field": "status", "operator": "equals", "value": "new"}]',
 '[{"action": "send_email", "params": {"template": "welcome_email"}}]',
 true)
ON CONFLICT DO NOTHING;

-- Insert framework roles
INSERT INTO framework_roles (role_name, display_name, description, is_system_role) VALUES
('framework_admin', 'Framework Administrator', 'Full framework configuration access', true),
('isp_admin', 'ISP Administrator', 'Full ISP solution access', true),
('isp_agent', 'ISP Agent', 'Customer service agent access', true),
('isp_readonly', 'ISP Read-Only', 'Read-only access to ISP data', true)
ON CONFLICT (role_name) DO NOTHING;

-- Insert ISP solution template
INSERT INTO framework_templates (template_name, display_name, description, category, template_data, is_installed) VALUES
('isp_solution', 'Complete ISP Management Solution', 
 'Full-featured ISP management system with customer management, billing, support, and network monitoring',
 'ISP', 
 '{"entities": ["customers", "services", "invoices", "tickets"], "workflows": ["customer_onboarding", "billing_cycle", "support_escalation"]}',
 true)
ON CONFLICT (template_name) DO NOTHING;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON SCHEMA public IS 'ISP Framework v2.0.0 - Complete aligned schema with all features';

COMMENT ON TABLE framework_entities IS 'Core framework table defining all dynamic entities in the system';
COMMENT ON TABLE framework_fields IS 'Dynamic field definitions for entities - enables custom fields';
COMMENT ON TABLE framework_rules IS 'Business rules engine - defines automated actions and workflows';
COMMENT ON TABLE framework_forms IS 'Form builder definitions for creating custom forms';
COMMENT ON TABLE framework_plugins IS 'Plugin marketplace registry for extensions';

COMMENT ON TABLE customers IS 'Core customer management table with framework integration';
COMMENT ON TABLE internet_services IS 'Internet service subscriptions with full lifecycle management';
COMMENT ON TABLE invoices IS 'Billing invoices with workflow and template support';
COMMENT ON TABLE tickets IS 'Support ticket system with SLA and automation';

COMMENT ON TABLE resellers IS 'Reseller management for white-label and partner operations';
COMMENT ON TABLE mass_incidents IS 'Network incident management affecting multiple customers';
COMMENT ON TABLE file_storage IS 'S3-integrated file storage system for documents and media';
COMMENT ON TABLE communication_templates IS 'Multi-channel communication template system';

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================