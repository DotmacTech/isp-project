import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message, Divider } from 'antd';
import { UserOutlined, LockOutlined, IdcardOutlined, TeamOutlined } from '@ant-design/icons';

const { Title } = Typography;

function SetupPage() {
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const onFinish = async (values) => {
        setLoading(true);

        const setupData = {
            partner_name: values.partnerName,
            admin_email: values.adminEmail,
            admin_password: values.adminPassword,
            admin_full_name: values.adminFullName,
        };

        try {
            const response = await fetch('/api/setup/create-admin', { // Use relative URL with /api prefix
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(setupData),
            });

            if (response.ok) {
                message.success('Setup completed successfully!');
                navigate('/login');
            } else {
                let errorMessage = 'An error occurred during setup.';
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.detail) {
                        if (typeof errorData.detail === 'string') {
                            errorMessage = errorData.detail;
                        } else if (Array.isArray(errorData.detail)) {
                            errorMessage = errorData.detail
                                .map(err => (err.msg && err.loc) ? `${err.loc.join('.')} - ${err.msg}` : JSON.stringify(err))
                                .join('; ');
                        } else if (typeof errorData.detail === 'object') {
                            errorMessage = JSON.stringify(errorData.detail);
                        }
                    }
                } catch (e) {
                    errorMessage = `Server returned ${response.status}: ${response.statusText}`;
                }
                message.error(errorMessage);
            }
        } catch (error) {
            message.error('Network error or server is unreachable.');
            console.error('Error during setup:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
            <Card style={{ width: 500 }}>
                <Title level={2} style={{ textAlign: 'center' }}>Initial Setup</Title>
                <Form name="setup" onFinish={onFinish} layout="vertical" autoComplete="off">
                    <Divider>Partner Details</Divider>
                    <Form.Item
                        name="partnerName"
                        label="Partner Name"
                        rules={[{ required: true, message: 'Please input the Partner Name!' }]}
                    >
                        <Input prefix={<TeamOutlined />} placeholder="Your Company Name" />
                    </Form.Item>

                    <Divider>Administrator Details</Divider>
                    <Form.Item
                        name="adminFullName"
                        label="Full Name"
                        rules={[{ required: true, message: 'Please input your Full Name!' }]}
                    >
                        <Input prefix={<IdcardOutlined />} placeholder="e.g., John Doe" />
                    </Form.Item>

                    <Form.Item
                        name="adminEmail"
                        label="Email Address"
                        rules={[{ required: true, type: 'email', message: 'Please input a valid Email Address!' }]}
                    >
                        <Input prefix={<UserOutlined />} placeholder="e.g., admin@company.com" />
                    </Form.Item>

                    <Form.Item
                        name="adminPassword"
                        label="Password"
                        rules={[{ required: true, message: 'Please input your Password!' }]}
                        hasFeedback
                    >
                        <Input.Password prefix={<LockOutlined />} placeholder="Password" />
                    </Form.Item>

                    <Form.Item
                        name="confirmPassword"
                        label="Confirm Password"
                        dependencies={['adminPassword']}
                        hasFeedback
                        rules={[
                            { required: true, message: 'Please confirm your password!' },
                            ({ getFieldValue }) => ({
                                validator(_, value) {
                                    if (!value || getFieldValue('adminPassword') === value) {
                                        return Promise.resolve();
                                    }
                                    return Promise.reject(new Error('The two passwords that you entered do not match!'));
                                },
                            }),
                        ]}
                    >
                        <Input.Password prefix={<LockOutlined />} placeholder="Confirm Password" />
                    </Form.Item>

                    <Form.Item>
                        <Button type="primary" htmlType="submit" loading={loading} style={{ width: '100%' }}>
                            Complete Setup
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
}

export default SetupPage;