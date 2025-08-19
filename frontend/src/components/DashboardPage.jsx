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
        const response = await axios.get('/api/users/me/', {
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

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div className="logo" style={{ height: '32px', margin: '16px', background: 'rgba(255, 255, 255, 0.2)', borderRadius: '6px' }}>
            <Title level={4} style={{ color: 'white', textAlign: 'center', lineHeight: '32px', margin: 0 }}>ISP</Title>
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[location.pathname]} openKeys={openKeys} onOpenChange={onOpenChange}>
          <Menu.Item key="/dashboard" icon={<DashboardOutlined />}>
            <Link to="/dashboard">Dashboard</Link>
          </Menu.Item>

          <SubMenu key="customers" icon={<UserOutlined />} title="Customers">
            <Menu.Item key="/dashboard/customers/view"><Link to="/dashboard/customers/view">View Customers</Link></Menu.Item>
            <Menu.Item key="/dashboard/customers/add"><Link to="/dashboard/customers/add">Add Customer</Link></Menu.Item>
            <Menu.Item key="/dashboard/customers/sessions"><Link to="/dashboard/customers/sessions">Manage Sessions</Link></Menu.Item>
          </SubMenu>

          <SubMenu key="resellers" icon={<TeamOutlined />} title="Resellers">
            <Menu.Item key="/dashboard/resellers/view"><Link to="/dashboard/resellers/view">View Resellers</Link></Menu.Item>
            <Menu.Item key="/dashboard/resellers/add"><Link to="/dashboard/resellers/add">Add Reseller</Link></Menu.Item>
          </SubMenu>

          <SubMenu key="billing" icon={<DollarOutlined />} title="Billing">
            <Menu.Item key="/dashboard/billing/invoices"><Link to="/dashboard/billing/invoices">Invoices</Link></Menu.Item>
            <Menu.Item key="/dashboard/billing/tariffs"><Link to="/dashboard/billing/tariffs">Tariffs & Plans</Link></Menu.Item>
            <Menu.Item key="/dashboard/billing/payments"><Link to="/dashboard/billing/payments">Payments</Link></Menu.Item>
          </SubMenu>

          <SubMenu key="network" icon={<ApartmentOutlined />} title="Network">
            <Menu.Item key="/dashboard/network/devices"><Link to="/dashboard/network/devices">Monitor Devices</Link></Menu.Item>
            <Menu.Item key="/dashboard/network/ips"><Link to="/dashboard/network/ips">Manage IPs</Link></Menu.Item>
            <Menu.Item key="/dashboard/network/radius"><Link to="/dashboard/network/radius">RADIUS Sessions</Link></Menu.Item>
          </SubMenu>

          <SubMenu key="support" icon={<CustomerServiceOutlined />} title="Support">
            <Menu.Item key="/dashboard/support/tickets"><Link to="/dashboard/support/tickets">Tickets</Link></Menu.Item>
            <Menu.Item key="/dashboard/support/knowledgebase"><Link to="/dashboard/support/knowledgebase">Knowledge Base</Link></Menu.Item>
          </SubMenu>

          <SubMenu key="inventory" icon={<StockOutlined />} title="Inventory">
            <Menu.Item key="/dashboard/inventory/equipment"><Link to="/dashboard/inventory/equipment">Equipment</Link></Menu.Item>
            <Menu.Item key="/dashboard/inventory/stock"><Link to="/dashboard/inventory/stock">Stock Management</Link></Menu.Item>
          </SubMenu>

          <SubMenu key="field-ops" icon={<FieldTimeOutlined />} title="Field Operations">
            <Menu.Item key="/dashboard/field-ops/jobs"><Link to="/dashboard/field-ops/jobs">Assign Jobs</Link></Menu.Item>
            <Menu.Item key="/dashboard/field-ops/technicians"><Link to="/dashboard/field-ops/technicians">Technician Tracking</Link></Menu.Item>
          </SubMenu>

          <SubMenu key="reports" icon={<LineChartOutlined />} title="Reports">
            <Menu.Item key="/dashboard/reports/usage"><Link to="/dashboard/reports/usage">Usage Reports</Link></Menu.Item>
            <Menu.Item key="/dashboard/reports/financial"><Link to="/dashboard/reports/financial">Financial Reports</Link></Menu.Item>
          </SubMenu>

          {/* Settings Submenu */}
          <SubMenu key="settings" icon={<SettingOutlined />} title="Settings" >
            <Menu.Item key="/dashboard/settings/users" icon={<UserOutlined />}>
              <Link to="/dashboard/settings/users">Users</Link>
            </Menu.Item>
            <Menu.Item key="/dashboard/settings/roles" icon={<SafetyCertificateOutlined />}>
              <Link to="/dashboard/settings/roles">Roles</Link>
            </Menu.Item>
            <Menu.Item key="/dashboard/settings/permissions" icon={<SecurityScanOutlined />}>
              <Link to="/dashboard/settings/permissions">Permissions</Link>
            </Menu.Item>
            <Menu.Item key="/dashboard/settings/audit-logs" icon={<FileTextOutlined />}>
              <Link to="/dashboard/settings/audit-logs">Audit Logs</Link>
            </Menu.Item>
          </SubMenu>
        </Menu>
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