import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography, Avatar, Dropdown, message, Spin } from 'antd';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  DashboardOutlined,
  SettingOutlined,
  UserOutlined,
  SafetyCertificateOutlined,
  FileTextOutlined,
  SecurityScanOutlined,
  LogoutOutlined,
  TeamOutlined,
  DollarOutlined,
  ApartmentOutlined,
  CustomerServiceOutlined,
  StockOutlined,
  FieldTimeOutlined,
  LineChartOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;
const { SubMenu } = Menu;

function DashboardPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [openKeys, setOpenKeys] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);

  // Helper function for creating menu items
  function getItem(label, key, icon, children, type) {
    return { key, icon, children, label, type };
  }

  // This effect ensures the correct submenu opens automatically
  // when you navigate to any of its nested routes.
  useEffect(() => {
    const pathParts = location.pathname.split('/').filter(Boolean);
    if (pathParts.length > 1 && pathParts[0] === 'dashboard') {
      setOpenKeys([pathParts[1]]); // e.g., 'customers', 'billing', 'settings'
    }
  }, [location.pathname]);

  // Fetch current user data on component mount
  useEffect(() => {
    const fetchCurrentUser = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        message.error('Authentication required. Redirecting to login.');
        navigate('/login');
        return;
      }
      try {
        const response = await axios.get('/api/v1/users/me/', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setCurrentUser(response.data);
      } catch (error) {
        console.error('Failed to fetch user data:', error);
        message.error('Session expired. Please log in again.');
        localStorage.removeItem('access_token');
        navigate('/login');
      }
    };
    fetchCurrentUser();
  }, [navigate]);

  const onOpenChange = (keys) => {
    setOpenKeys(keys);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    message.success('Logged out successfully.');
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'logout',
      label: 'Logout',
      icon: <LogoutOutlined />,
      onClick: handleLogout,
    },
  ];

  const menuItems = [
    getItem(<Link to="/dashboard">Dashboard</Link>, '/dashboard', <DashboardOutlined />),
    getItem('Customers', 'customers', <UserOutlined />, [
      getItem(<Link to="/dashboard/customers/view">View Customers</Link>, '/dashboard/customers/view'),
      getItem(<Link to="/dashboard/customers/add">Add Customer</Link>, '/dashboard/customers/add'),
      getItem(<Link to="/dashboard/customers/sessions">Manage Sessions</Link>, '/dashboard/customers/sessions'),
    ]),
    getItem('Billing', 'billing', <DollarOutlined />, [
      getItem(<Link to="/dashboard/billing/services">Services</Link>, '/dashboard/billing/services'),
      getItem(<Link to="/dashboard/billing/invoices">Invoices</Link>, '/dashboard/billing/invoices'),
      getItem(<Link to="/dashboard/billing/tariffs">Tariffs</Link>, '/dashboard/billing/tariffs'),
      getItem(<Link to="/dashboard/billing/payments">Payments</Link>, '/dashboard/billing/payments'),
    ]),
    getItem('Network', 'network', <ApartmentOutlined />, [
      getItem(<Link to="/dashboard/network/devices">Monitor Devices</Link>, '/dashboard/network/devices'),
      getItem(<Link to="/dashboard/network/ips">Manage IPs</Link>, '/dashboard/network/ips'),
      getItem(<Link to="/dashboard/network/radius">RADIUS Sessions</Link>, '/dashboard/network/radius'),
    ]),
    getItem('Support', 'support', <CustomerServiceOutlined />, [
      getItem(<Link to="/dashboard/support/tickets">Tickets</Link>, '/dashboard/support/tickets'),
      getItem(<Link to="/dashboard/support/knowledgebase">Knowledge Base</Link>, '/dashboard/support/knowledgebase'),
    ]),
    getItem('Settings', 'settings', <SettingOutlined />, [
      getItem(<Link to="/dashboard/settings/users">Users</Link>, '/dashboard/settings/users', <UserOutlined />),
      getItem(<Link to="/dashboard/settings/roles">Roles</Link>, '/dashboard/settings/roles', <SafetyCertificateOutlined />),
      getItem(<Link to="/dashboard/settings/permissions">Permissions</Link>, '/dashboard/settings/permissions', <SecurityScanOutlined />),
      getItem(<Link to="/dashboard/settings/locations">Locations</Link>, '/dashboard/settings/locations', <GlobalOutlined />),
      getItem(<Link to="/dashboard/settings/billing">Billing Settings</Link>, '/dashboard/settings/billing', <DollarOutlined />),
      getItem(<Link to="/dashboard/settings/audit-logs">Audit Logs</Link>, '/dashboard/settings/audit-logs', <FileTextOutlined />),
    ]),
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div className="logo" style={{ height: '32px', margin: '16px', background: 'rgba(255, 255, 255, 0.2)', borderRadius: '6px' }}>
            <Title level={4} style={{ color: 'white', textAlign: 'center', lineHeight: '32px', margin: 0 }}>ISP</Title>
        </div>
        <Menu theme="dark" mode="inline" items={menuItems} selectedKeys={[location.pathname]} openKeys={openKeys} onOpenChange={onOpenChange} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          {currentUser ? (
            <Dropdown menu={{ items: userMenuItems }} trigger={['click']}>
              <a onClick={e => e.preventDefault()} style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <Avatar style={{ backgroundColor: '#1890ff' }} icon={<UserOutlined />} />
                <span style={{ marginLeft: 8, fontWeight: 500 }}>{currentUser.full_name}</span>
              </a>
            </Dropdown>
          ) : (
            <Spin size="small" />
          )}
        </Header>
        <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
          <div style={{ padding: 24, background: '#fff', minHeight: 360 }}>
            <Outlet /> {/* This will render the nested route components */}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}

export default DashboardPage;