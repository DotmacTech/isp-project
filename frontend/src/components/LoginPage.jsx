import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Alert } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';

const { Title } = Typography;

function LoginPage() {
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const onFinish = async (values) => {
        setError('');
        setLoading(true);

        const formData = new FormData();
        formData.append('username', values.email); // The backend expects a 'username' field for OAuth2
        formData.append('password', values.password);

        try {
            const response = await fetch('/token', { // Use relative URL without /api prefix
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                navigate('/dashboard');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Invalid login credentials');
            }
        } catch (error) {
            setError('An error occurred during login. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
            <Card style={{ width: 400, textAlign: 'center' }}>
                <Title level={2}>Login</Title>
                {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 24 }} />}
                <Form
                    name="login"
                    onFinish={onFinish}
                    initialValues={{ remember: true }}
                    autoComplete="off"
                >
                    <Form.Item
                        name="email"
                        rules={[{ required: true, type: 'email', message: 'Please input your Email Address!' }]}
                    >
                        <Input prefix={<UserOutlined />} placeholder="Email Address" />
                    </Form.Item>

                    <Form.Item
                        name="password"
                        rules={[{ required: true, message: 'Please input your Password!' }]}
                    >
                        <Input.Password prefix={<LockOutlined />} placeholder="Password" />
                    </Form.Item>

                    <Form.Item>
                        <Button type="primary" htmlType="submit" loading={loading} style={{ width: '100%' }}>
                            Log in
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
}

export default LoginPage;