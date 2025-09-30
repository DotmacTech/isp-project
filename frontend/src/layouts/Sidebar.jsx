import React from 'react';
import { Menu } from 'antd';
import { Link } from 'react-router-dom';
import {
    DashboardOutlined,
    UserOutlined,
    TeamOutlined,
    DollarOutlined,
    SettingOutlined,
    CustomerServiceOutlined,
    LineChartOutlined,
    FieldTimeOutlined,
    StockOutlined,
    KeyOutlined,
    GatewayOutlined,
    ClusterOutlined,
    TagOutlined,
} from '@ant-design/icons';

const Sidebar = () => {
    const items = [
        {
            key: 'dashboard',
            icon: <DashboardOutlined />,
            label: <Link to="/dashboard">Dashboard</Link>,
        },
        {
            key: 'crm',
            icon: <TagOutlined />,
            label: 'CRM',
            children: [
                { key: 'crm1', label: <Link to="/dashboard/crm/leads">Leads</Link> },
                { key: 'crm2', label: <Link to="/dashboard/crm/opportunities">Opportunities</Link> },
            ],
        },
        {
            key: 'customers',
            icon: <UserOutlined />,
            label: 'Customers',
            children: [
                { key: 'cust1', label: <Link to="/dashboard/customers">View Customers</Link> },
                { key: 'cust3', label: <Link to="/dashboard/sessions">Active Sessions</Link> },
            ],
        },
        {
            key: 'billing',
            icon: <DollarOutlined />,
            label: 'Billing',
            children: [
                { key: 'bill9', label: <Link to="/dashboard/billing/system-overview">System Overview</Link> },
                { key: 'bill2', label: <Link to="/dashboard/billing/invoices">Invoices</Link> },
                { key: 'bill3', label: <Link to="/dashboard/billing/services">Services</Link> },
                { key: 'bill4', label: <Link to="/dashboard/billing/tariffs">Tariffs & Plans</Link> },
                { key: 'bill5', label: <Link to="/dashboard/billing/payments">Payments</Link> },
                { key: 'bill6', label: <Link to="/dashboard/billing/analytics">Analytics</Link> },
                { key: 'bill7', label: <Link to="/dashboard/billing/cycles">Billing Cycles</Link> },
                { key: 'bill8', label: <Link to="/dashboard/billing/reports">Reports</Link> },
                
                { key: 'bill10', label: <Link to="/dashboard/billing/credit-notes">Credit Notes</Link> },
                { key: 'bill11', label: <Link to="/dashboard/billing/customer-config">Customer Config</Link> },
                { key: 'bill12', label: <Link to="/dashboard/billing/proforma-invoices">Proforma Invoices</Link> },
                { key: 'bill13', label: <Link to="/dashboard/billing/transactions">Transactions</Link> },
                { key: 'bill14', label: <Link to="/dashboard/billing/usage-tracking">Usage Tracking</Link> },
            ],
        },
        {
            key: 'network_management',
            icon: <GatewayOutlined />,
            label: 'Network Management',
            children: [
                { key: 'nm1', label: <Link to="/dashboard/network/analytics">Dashboard</Link> },
                { key: 'nm2', label: <Link to="/dashboard/network/incidents">Incidents</Link> },
                { key: 'nm3', label: <Link to="/dashboard/network/alerts">Alerts</Link> },
                { key: 'nm4', label: <Link to="/dashboard/network/topology">Topology</Link> },
                { key: 'nm5', label: <Link to="/dashboard/network/monitoring-devices">Monitoring Devices</Link> },
                { key: 'nm6', label: <Link to="/dashboard/network/snmp-profiles">SNMP Profiles</Link> },
                { key: 'nm7', label: <Link to="/dashboard/network/data">Monitoring Data</Link> },
                { key: 'nm8', label: <Link to="/dashboard/network/settings">Settings</Link> },
            ]
        },
        {
            key: 'network_infra',
            icon: <ClusterOutlined />,
            label: 'Network Infrastructure',
            children: [
                { key: 'ni1', label: <Link to="/dashboard/network/sites">Sites</Link> },
                { key: 'ni2', label: <Link to="/dashboard/network/routers">Routers</Link> },
                { key: 'ni6', label: <Link to="/dashboard/network/config">Network Configuration</Link> },
                { key: 'ni7', label: <Link to="/dashboard/network/categories">Network Categories</Link> },
                { key: 'ni3', label: <Link to="/dashboard/network/ipam/ipv4">IPv4</Link> },
                { key: 'ni4', label: <Link to="/dashboard/network/ipam/ipv6">IPv6</Link> },
                { key: 'ni5', label: <Link to="/dashboard/freeradius">RADIUS</Link> },
            ],
        },
        {
            key: 'support',
            icon: <CustomerServiceOutlined />,
            label: 'Support',
            children: [
                { key: 'sup1', label: <Link to="/dashboard/support/tickets">Tickets</Link> },
                { key: 'sup2', label: <Link to="/dashboard/knowledgebase">Knowledge Base</Link> },
            ],
        },
        {
            key: 'resellers',
            icon: <TeamOutlined />,
            label: 'Resellers',
            children: [
                { key: 'res1', label: <Link to="/dashboard/resellers">View Resellers</Link> },
                { key: 'res2', label: <Link to="/dashboard/resellers">Add Reseller</Link> },
            ],
        },
        {
            key: 'inventory',
            icon: <StockOutlined />,
            label: 'Inventory',
            children: [
                { key: 'inv1', label: <Link to="/dashboard/equipment">Equipment</Link> },
                { key: 'inv2', label: <Link to="/dashboard/stock">Stock Management</Link> },
            ],
        },
        {
            key: 'reports',
            icon: <LineChartOutlined />,
            label: 'Reports',
            children: [
                { key: 'rep1', label: <Link to="/dashboard/usage-reports">Usage Reports</Link> },
                { key: 'rep2', label: <Link to="/dashboard/financial-reports">Financial Reports</Link> },
            ],
        },
        {
            key: 'settings',
            icon: <SettingOutlined />,
            label: 'Settings',
            children: [
                { key: 'set1', icon: <UserOutlined />, label: <Link to="/dashboard/settings/users">User Management</Link> },
                { key: 'set2', icon: <KeyOutlined />, label: <Link to="/dashboard/settings/roles">Roles</Link> },
                { key: 'set3', icon: <KeyOutlined />, label: <Link to="/dashboard/settings/permissions">Permissions</Link> },
                { key: 'set4', label: <Link to="/dashboard/settings/audit-logs">Audit Logs</Link> },
                { key: 'set5', label: <Link to="/dashboard/settings/billing">Billing Settings</Link> },
            ],
        },
    ];

    return (
        <div>
            <Menu theme="dark" mode="inline" defaultSelectedKeys={['1']} items={items} />
        </div>
    );
};

export default Sidebar;