import React, { useState, useEffect } from 'react';
import { Layout, Menu, Dropdown, Avatar, Spin, message } from 'antd';
import { 
  DashboardOutlined, 
  SolutionOutlined, 
  UserOutlined, 
  DollarOutlined, 
  ApartmentOutlined, 
  CustomerServiceOutlined, 
  SettingOutlined, 
  SafetyCertificateOutlined, 
  SecurityScanOutlined, 
  TeamOutlined, 
  GlobalOutlined, 
  FileTextOutlined, 
  LogoutOutlined 
} from '@ant-design/icons';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import apiClient from '../api';
import { Typography } from 'antd';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

// Helper function to create menu items
function getItem(label, key, icon, children) {
  return { key, icon, children, label };
}

function DashboardPage() {
  const [openKeys, setOpenKeys] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await apiClient.get('/v1/users/me');
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

  useEffect(() => {
    const pathParts = location.pathname.split('/').filter(Boolean);
    if (pathParts.length > 1 && pathParts[0] === 'dashboard') {
      setOpenKeys([pathParts[1]]); // e.g., 'customers', 'billing', 'settings'
    }
  }, [location.pathname]);

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
    getItem('CRM', 'crm', <SolutionOutlined />, [
      getItem(<Link to="/dashboard/crm/leads">Leads</Link>, '/dashboard/crm/leads'),
      getItem(<Link to="/dashboard/crm/opportunities">Opportunities</Link>, '/dashboard/crm/opportunities'),
    ]),
    getItem('Customers', 'customers', <UserOutlined />, [
      getItem(<Link to="/dashboard/customers/view">View Customers</Link>, '/dashboard/customers/view'),
      getItem(<Link to="/dashboard/customers/sessions">Manage Sessions</Link>, '/dashboard/customers/sessions'),
    ]),
    getItem('Billing', 'billing', <DollarOutlined />, [
      getItem(<Link to="/dashboard/billing/services">Services</Link>, '/dashboard/billing/services'),
      getItem(<Link to="/dashboard/billing/invoices">Invoices</Link>, '/dashboard/billing/invoices'),
      getItem(<Link to="/dashboard/billing/tariffs">Tariffs</Link>, '/dashboard/billing/tariffs'),
      getItem(<Link to="/dashboard/billing/payments">Payments</Link>, '/dashboard/billing/payments'),
    ]),
    getItem('Network', 'network', <ApartmentOutlined />, [
      getItem(<Link to="/dashboard/network/sites">Network Sites</Link>, '/dashboard/network/sites'),
      getItem(<Link to="/dashboard/network/routers">Routers (NAS)</Link>, '/dashboard/network/routers'),
      getItem(<Link to="/dashboard/network/monitoring-devices">Monitoring Devices</Link>, '/dashboard/network/monitoring-devices'),
      getItem(<Link to="/dashboard/network/radius-sessions">RADIUS Sessions</Link>, '/dashboard/network/radius-sessions'),
      getItem(<Link to="/dashboard/network/config">Monitoring Config</Link>, '/dashboard/network/config'),
    ]),
    getItem('Support', 'support', <CustomerServiceOutlined />, [
      getItem(<Link to="/dashboard/support/tickets">Tickets</Link>, '/dashboard/support/tickets'),
      getItem(<Link to="/dashboard/support/knowledgebase">Knowledge Base</Link>, '/dashboard/support/knowledgebase'),
    ]),
    getItem('Settings', 'settings', <SettingOutlined />, [
      getItem(<Link to="/dashboard/settings/users">Users</Link>, '/dashboard/settings/users', <UserOutlined />),
      getItem(<Link to="/dashboard/settings/roles">Roles</Link>, '/dashboard/settings/roles', <SafetyCertificateOutlined />),
      getItem(<Link to="/dashboard/settings/permissions">Permissions</Link>, '/dashboard/settings/permissions', <SecurityScanOutlined />),
      getItem(<Link to="/dashboard/settings/partners">Partners</Link>, '/dashboard/settings/partners', <TeamOutlined />),
      getItem(<Link to="/dashboard/settings/locations">Locations</Link>, '/dashboard/settings/locations', <GlobalOutlined />),
      getItem(<Link to="/dashboard/settings/billing">Billing Settings</Link>, '/dashboard/settings/billing', <DollarOutlined />),
      getItem(<Link to="/dashboard/settings/ticket-config">Ticket Settings</Link>, '/dashboard/settings/ticket-config', <CustomerServiceOutlined />),
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