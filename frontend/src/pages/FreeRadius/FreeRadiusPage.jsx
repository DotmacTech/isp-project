import React from 'react';
import { Card, Tabs, Typography } from 'antd';
import { WifiOutlined, UserOutlined, HddOutlined, BookOutlined } from '@ant-design/icons';
import OnlineUsers from './OnlineUsers';
import RadiusUsers from './RadiusUsers';
import AccountingLogs from './AccountingLogs'
import NasDevices from './NasDevices.jsx';

const { Title } = Typography;

const FreeRadiusPage = () => {
  const items = [
    {
      label: (
        <span>
          <WifiOutlined /> Online Users
        </span>
      ),
      key: '1',
      children: <OnlineUsers />,
    },
    {
      label: (
        <span>
          <UserOutlined /> User Management
        </span>
      ),
      key: '2',
      children: <RadiusUsers />,
    },
    {
      label: (
        <span>
          <BookOutlined /> Accounting Logs
        </span>
      ),
      key: '3',
      children: <AccountingLogs />,
    },
    {
      label: (
        <span>
          <HddOutlined /> NAS Devices
        </span>
      ),
      key: '4',
      children: <NasDevices />,
    },
  ];

  return (
    <Card>
      <Title level={2}>FreeRADIUS Management</Title>
      <Tabs defaultActiveKey="1" items={items} />
    </Card>
  );
};

export default FreeRadiusPage;