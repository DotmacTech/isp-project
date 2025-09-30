import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message, Row, Col, Select } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';
import apiClient from '../../../services/api';

const { Title } = Typography;
const { Option } = Select;

const RegistrationPage = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      // Get partner and location data (for demo, we'll use the first available)
      const [partnersRes, locationsRes] = await Promise.all([
        apiClient.get('/v1/partners/'),
        apiClient.get('/v1/locations/')
      ]);

      const partnerId = partnersRes.data.items.length > 0 ? partnersRes.data.items[0].id : 1;
      const locationId = locationsRes.data.length > 0 ? locationsRes.data[0].id : 1;

      const registrationData = {
        name: values.name,
        email: values.email,
        phone: values.phone,
        login: values.email, // Using email as login for simplicity
        password: values.password,
        partner_id: partnerId,
        location_id: locationId,
        status: 'new',
        category: 'person'
      };

      await apiClient.post('/v1/customers/', registrationData);
      message.success('Registration successful! Please login.');
      navigate('/customer/login');
    } catch (error) {
      message.error(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 450, textAlign: 'center' }}>
        <Title level={2}>Customer Registration</Title>
        <Form
          name="registration"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="Full Name"
            rules={[{ required: true, message: 'Please input your full name!' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Full Name" />
          </Form.Item>

          <Form.Item
            name="email"
            label="Email Address"
            rules={[
              { required: true, message: 'Please input your email!' },
              { type: 'email', message: 'Please enter a valid email!' }
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="Email Address" />
          </Form.Item>

          <Form.Item
            name="phone"
            label="Phone Number"
            rules={[{ required: true, message: 'Please input your phone number!' }]}
          >
            <Input prefix={<PhoneOutlined />} placeholder="Phone Number" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[
              { required: true, message: 'Please input your password!' },
              { min: 6, message: 'Password must be at least 6 characters!' }
            ]}
            hasFeedback
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Password" />
          </Form.Item>

          <Form.Item
            name="confirm"
            label="Confirm Password"
            dependencies={['password']}
            hasFeedback
            rules={[
              { required: true, message: 'Please confirm your password!' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('The two passwords do not match!'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Confirm Password" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} style={{ width: '100%' }}>
              Register
            </Button>
          </Form.Item>
        </Form>
        <div style={{ marginTop: 16 }}>
          Already have an account? <a href="/customer/login">Login here</a>
        </div>
      </Card>
    </div>
  );
};

export default RegistrationPage;