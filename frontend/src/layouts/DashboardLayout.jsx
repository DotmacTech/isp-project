import React from 'react';
import { Layout } from 'antd';
import TopBar from './TopBar';
import Sidebar from './Sidebar';

const { Header, Sider, Content } = Layout;

const DashboardLayout = ({ children }) => {
    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider width={250}>
                <Sidebar />
            </Sider>
            <Layout>
                <Header style={{ padding: 0, background: '#fff' }}>
                    <TopBar />
                </Header>
                <Content style={{ margin: '24px 16px 0' }}>
                    <div style={{ padding: 24, minHeight: 360, background: '#fff' }}>
                        {children}
                    </div>
                </Content>
            </Layout>
        </Layout>
    );
};

export default DashboardLayout;
