import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, Checkbox, Space, Alert, message, Spin } from 'antd';
import apiClient from '../../services/api';

const { Option } = Select;
const { TextArea } = Input;

const SNMPProfileForm = ({ profile, onSave, onCancel }) => {
  const [form] = Form.useForm();
  const [devices, setDevices] = useState([]);
  const [loadingDevices, setLoadingDevices] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setLoadingDevices(true);
        const response = await apiClient.get('/v1/network/monitoring-devices/', { params: { limit: 1000 } });
        setDevices(response.data.items || []);
      } catch (err) {
        message.error('Failed to load devices.');
        setError(err.message);
      } finally {
        setLoadingDevices(false);
      }
    };
    fetchDevices();
  }, []);

  useEffect(() => {
    if (profile) {
      form.setFieldsValue({
        ...profile,
        oids_to_monitor: JSON.stringify(profile.oids_to_monitor || [], null, 2),
        thresholds: JSON.stringify(profile.thresholds || {}, null, 2),
      });
    } else {
      form.resetFields();
      form.setFieldsValue({
        snmp_version: 'v2c',
        polling_interval: 300,
        is_active: true,
        oids_to_monitor: '[]',
        thresholds: '{}',
      });
    }
  }, [profile, form]);

  const validateJson = (_, value) => {
    try {
      JSON.parse(value);
      return Promise.resolve();
    } catch (e) {
      return Promise.reject(new Error('Invalid JSON format'));
    }
  };

  const onFinish = async (values) => {
    try {
      const dataToSave = {
        ...values,
        device_id: parseInt(values.device_id), // Ensure device_id is a number
        polling_interval: parseInt(values.polling_interval), // Ensure interval is a number
        oids_to_monitor: JSON.parse(values.oids_to_monitor),
        thresholds: JSON.parse(values.thresholds),
      };
      onSave(dataToSave);
    } catch (jsonError) {
      // This catch block might be redundant if validation rules handle it
      console.error("Error during form submission:", jsonError);
    }
  };

  if (loadingDevices) {
    return <Spin tip="Loading devices..."><div style={{ height: '200px' }} /></Spin>;
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={{
        snmp_version: 'v2c',
        polling_interval: 300,
        is_active: true,
        oids_to_monitor: '[]',
        thresholds: '{}',
      }}
    >
      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} />}

      <Form.Item
        name="device_id"
        label="Device"
        rules={[{ required: true, message: 'Please select a device!' }]}
      >
        <Select placeholder="Select a device">
          {devices.map(dev => (
            <Option key={dev.id} value={dev.id}>
              {dev.title} ({dev.ip})
            </Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        name="snmp_version"
        label="SNMP Version"
        rules={[{ required: true, message: 'Please select SNMP version!' }]}
      >
        <Select>
          <Option value="v1">v1</Option>
          <Option value="v2c">v2c</Option>
          <Option value="v3">v3</Option>
        </Select>
      </Form.Item>

      {(form.getFieldValue('snmp_version') === 'v1' || form.getFieldValue('snmp_version') === 'v2c') && (
        <Form.Item
          name="community_string"
          label="Community String"
          rules={[{ required: true, message: 'Please input community string!' }]}
        >
          <Input />
        </Form.Item>
      )}

      {form.getFieldValue('snmp_version') === 'v3' && (
        <>
          <Form.Item name="username" label="Username" rules={[{ required: true, message: 'Please input username!' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="auth_protocol" label="Auth Protocol">
            <Input placeholder="e.g., MD5, SHA" />
          </Form.Item>
          <Form.Item name="auth_password" label="Auth Password">
            <Input.Password />
          </Form.Item>
          <Form.Item name="priv_protocol" label="Priv Protocol">
            <Input placeholder="e.g., DES, AES" />
          </Form.Item>
          <Form.Item name="priv_password" label="Priv Password">
            <Input.Password />
          </Form.Item>
        </>
      )}

      <Form.Item
        name="polling_interval"
        label="Polling Interval (seconds)"
        rules={[{ required: true, message: 'Please input polling interval!' }]}
      >
        <Input type="number" min={10} />
      </Form.Item>

      <Form.Item
        name="oids_to_monitor"
        label="OIDs to Monitor (JSON Array)"
        rules={[{ validator: validateJson }]} // Add JSON validation rule
      >
        <TextArea rows={5} />
      </Form.Item>

      <Form.Item
        name="thresholds"
        label="Thresholds (JSON Object)"
        rules={[{ validator: validateJson }]} // Add JSON validation rule
      >
        <TextArea rows={5} />
      </Form.Item>

      <Form.Item name="is_active" valuePropName="checked">
        <Checkbox>Active</Checkbox>
      </Form.Item>

      <Form.Item>
        <Space>
          <Button onClick={onCancel}>Cancel</Button>
          <Button type="primary" htmlType="submit">
            Save Profile
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default SNMPProfileForm;