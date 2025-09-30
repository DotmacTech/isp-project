import React from 'react';
import { Form, Input, Select, Button, Card, Row, Col, DatePicker, InputNumber, Switch } from 'antd';
import { UserOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;

export default {
  title: 'Design System/Form Components',
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export const BasicForm = () => {
  const [form] = Form.useForm();
  
  const onFinish = (values) => {
    console.log('Form values:', values);
  };

  return (
    <Card title="Basic Form Example" style={{ maxWidth: 600 }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          status: 'active',
          notifications: true,
        }}
      >
        <Form.Item
          name="name"
          label="Full Name"
          rules={[{ required: true, message: 'Please input your name!' }]}
        >
          <Input prefix={<UserOutlined />} placeholder="Enter your full name" />
        </Form.Item>

        <Form.Item
          name="email"
          label="Email"
          rules={[
            { required: true, message: 'Please input your email!' },
            { type: 'email', message: 'Please enter a valid email!' },
          ]}
        >
          <Input prefix={<MailOutlined />} placeholder="Enter your email" />
        </Form.Item>

        <Form.Item
          name="phone"
          label="Phone Number"
          rules={[{ required: true, message: 'Please input your phone number!' }]}
        >
          <Input prefix={<PhoneOutlined />} placeholder="Enter your phone number" />
        </Form.Item>

        <Form.Item
          name="status"
          label="Status"
          rules={[{ required: true, message: 'Please select a status!' }]}
        >
          <Select placeholder="Select status">
            <Option value="active">Active</Option>
            <Option value="inactive">Inactive</Option>
            <Option value="pending">Pending</Option>
          </Select>
        </Form.Item>

        <Form.Item name="notifications" label="Enable Notifications" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
            Submit
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export const BillingForm = () => {
  const [form] = Form.useForm();

  return (
    <Card title="Billing Configuration Form" style={{ maxWidth: 800 }}>
      <Form form={form} layout="vertical">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="customer_name"
              label="Customer Name"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="Enter customer name" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="plan_type"
              label="Plan Type"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Select placeholder="Select plan type">
                <Option value="basic">Basic Plan</Option>
                <Option value="premium">Premium Plan</Option>
                <Option value="enterprise">Enterprise Plan</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="monthly_fee"
              label="Monthly Fee"
              rules={[{ required: true, message: 'Required' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="0.00"
                min={0}
                step={0.01}
                formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value.replace(/\$\s?|(,*)/g, '')}
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="bandwidth_limit"
              label="Bandwidth Limit (GB)"
              rules={[{ required: true, message: 'Required' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="100"
                min={1}
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="billing_cycle"
              label="Billing Cycle"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Select placeholder="Select cycle">
                <Option value="monthly">Monthly</Option>
                <Option value="quarterly">Quarterly</Option>
                <Option value="yearly">Yearly</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="notes" label="Additional Notes">
          <TextArea rows={4} placeholder="Enter any additional notes..." />
        </Form.Item>

        <Form.Item name="start_date" label="Service Start Date">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Button style={{ width: '100%' }}>Cancel</Button>
            </Col>
            <Col span={12}>
              <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
                Save Configuration
              </Button>
            </Col>
          </Row>
        </Form.Item>
      </Form>
    </Card>
  );
};

export const NetworkForm = () => {
  const [form] = Form.useForm();

  return (
    <Card title="Network Device Configuration" style={{ maxWidth: 700 }}>
      <Form form={form} layout="vertical">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="device_name"
              label="Device Name"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="e.g., Router-Main-01" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="device_type"
              label="Device Type"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Select placeholder="Select device type">
                <Option value="router">Router</Option>
                <Option value="switch">Switch</Option>
                <Option value="access_point">Access Point</Option>
                <Option value="firewall">Firewall</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="ip_address"
              label="IP Address"
              rules={[
                { required: true, message: 'Required' },
                { pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/, message: 'Invalid IP format' },
              ]}
            >
              <Input placeholder="192.168.1.1" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="snmp_community"
              label="SNMP Community"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="public" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="location" label="Physical Location">
          <Input placeholder="e.g., Server Room A, Rack 3" />
        </Form.Item>

        <Form.Item name="monitoring_enabled" label="Enable Monitoring" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
            Add Device
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};