import React from 'react';
import { Menu } from 'antd';
import { Link } from 'react-router-dom';
import {
    DashboardOutlined,
    UserOutlined,
    TeamOutlined,
    DollarOutlined,
    ApartmentOutlined,
    SettingOutlined,
    CustomerServiceOutlined,
    LineChartOutlined,
    FieldTimeOutlined,
    StockOutlined,
    KeyOutlined,
} from '@ant-design/icons';

const Sidebar = () => {
    const items = [
        {
            key: '1',
            icon: <DashboardOutlined />,
            label: <Link to="/dashboard">Dashboard</Link>,
        },
        {
            key: 'sub1',
            icon: <UserOutlined />,
            label: 'Customers',
            children: [
                { key: '2', label: <Link to="/dashboard/customers">View Customers</Link> },
                { key: '3', label: <Link to="/dashboard/customers/add">Add Customer</Link> },
                { key: '4', label: <Link to="/dashboard/sessions">Manage Sessions</Link> },
            ],
        },
        {
            key: 'sub2',
            icon: <TeamOutlined />,
            label: 'Resellers',
            children: [
                { key: '5', label: <Link to="/dashboard/resellers">View Resellers</Link> },
                { key: '6', label: <Link to="/dashboard/resellers/add">Add Reseller</Link> },
            ],
        },
        {
            key: 'sub3',
            icon: <DollarOutlined />,
            label: 'Billing',
            children: [
                { key: '7', label: <Link to="/dashboard/invoices">Invoices</Link> },
                { key: '8', label: <Link to="/dashboard/tariffs">Tariffs & Plans</Link> },
                { key: '9', label: <Link to="/dashboard/payments">Payments</Link> },
            ],
        },
        {
            key: 'sub4',
            icon: <ApartmentOutlined />,
            label: 'Network',
            children: [
                { key: '10', label: <Link to="/dashboard/devices">Monitor Devices</Link> },
                { key: '11', label: <Link to="/dashboard/ips">Manage IPs</Link> },
                { key: '12', label: <Link to="/dashboard/radius">RADIUS Sessions</Link> },
            ],
        },
        {
            key: 'sub5',
            icon: <CustomerServiceOutlined />,
            label: 'Support',
            children: [
                { key: '13', label: <Link to="/dashboard/tickets">Tickets</Link> },
                { key: '14', label: <Link to="/dashboard/knowledgebase">Knowledge Base</Link> },
            ],
        },
        {
            key: 'sub6',
            icon: <StockOutlined />,
            label: 'Inventory',
            children: [
                { key: '15', label: <Link to="/dashboard/equipment">Equipment</Link> },
                { key: '16', label: <Link to="/dashboard/stock">Stock Management</Link> },
            ],
        },
        {
            key: 'sub7',
            icon: <FieldTimeOutlined />,
            label: 'Field Operations',
            children: [
                { key: '17', label: <Link to="/dashboard/jobs">Assign Jobs</Link> },
                { key: '18', label: <Link to="/dashboard/technicians">Technician Tracking</Link> },
            ],
        },
        {
            key: 'sub8',
            icon: <LineChartOutlined />,
            label: 'Reports',
            children: [
                { key: '19', label: <Link to="/dashboard/usage-reports">Usage Reports</Link> },
                { key: '20', label: <Link to="/dashboard/financial-reports">Financial Reports</Link> },
            ],
        },
        {
            key: 'sub9',
            icon: <SettingOutlined />,
            label: 'Settings',
            children: [
                { key: '21', icon: <UserOutlined />, label: <Link to="/dashboard/users">User Management</Link> },
                { key: '22', icon: <KeyOutlined />, label: <Link to="/dashboard/roles">Roles & Permissions</Link> },
                { key: '23', label: <Link to="/dashboard/system-config">System Config</Link> },
            ],
        },
    ];

    return (
        <div>
            <div style={{ height: '32px', margin: '16px', background: 'rgba(255, 255, 255, 0.3)' }}>
                {/* Logo placeholder */}
            </div>
            <Menu theme="dark" mode="inline" defaultSelectedKeys={['1']} items={items} />
        </div>
    );
};

export default Sidebar;