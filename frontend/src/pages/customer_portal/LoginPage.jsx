import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Alert, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';

const { Title } = Typography;

const CustomerLoginPage = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const onFinish = async (values) => {
    setError('');
    setLoading(true);

    const formData = new FormData();
    formData.append('username', values.email);
    formData.append('password', values.password);
    formData.append('grant_type', 'password');

    try {
      const response = await fetch('/api/v1/customer/token', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('customer_access_token', data.access_token);
        const from = location.state?.from?.pathname || '/customer/dashboard';
        navigate(from);
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
        <Title level={2}>Customer Login</Title>
        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 24 }} />}
        <Form
          name="customer_login"
          onFinish={onFinish}
          initialValues={{ remember: true }}
          autoComplete="off"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Please input your Email Address!' },
              { type: 'email', message: 'Please enter a valid email!' }
            ]}
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
        <div style={{ marginTop: 16 }}>
          Don't have an account? <a href="/customer/register">Register here</a>
        </div>
      </Card>
    </div>
  );
};

export default CustomerLoginPage;