import React from 'react';
import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import SideBar from './Sidebar';
import TopBar from './TopBar';

const { Header, Sider, Content } = Layout;

const MainLayout = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="dark">
        <SideBar />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: '#fff' }}>
          <TopBar />
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', borderRadius: '8px' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;