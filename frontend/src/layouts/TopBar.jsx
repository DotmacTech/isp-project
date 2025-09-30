import React from 'react';
import { Avatar, Badge, Space, Dropdown } from 'antd';
import { BellOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import GlobalSearchBar from '../components/GlobalSearchBar';

const TopBar = () => {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        navigate('/login');
    };

    const menu = {
        items: [
            {
                key: 'logout',
                icon: <LogoutOutlined />,
                label: 'Logout',
                onClick: handleLogout,
            },
        ],
    };

    return (
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', paddingRight: '24px', height: '100%' }}>
            <GlobalSearchBar />
            <Space size="large">
                <Badge count={5}>
                    <BellOutlined style={{ fontSize: '20px' }} />
                </Badge>
                <Dropdown menu={menu} placement="bottomRight" arrow>
                    <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
                </Dropdown>
            </Space>
        </div>
    );
};

export default TopBar;