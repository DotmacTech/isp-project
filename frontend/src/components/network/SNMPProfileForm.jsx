import React, { useEffect } from 'react';
import { Form, Input, Select, InputNumber, Switch, Button } from 'antd';

const { Option } = Select;

const SNMPProfileForm = ({ profile, onSave, onCancel }) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (profile) {
      form.setFieldsValue({
        device_id: profile.device_id || '',
        snmp_version: profile.snmp_version || 'v2c',
        community_string: profile.community_string || '',
        username: profile.username || '',
        polling_interval: profile.polling_interval || 60,
        is_active: profile.is_active !== undefined ? profile.is_active : true,
      });
    } else {
      form.resetFields();
    }
  }, [profile, form]);

  const handleSubmit = (values) => {
    onSave(values);
  };

  return (
    <Form form={form} onFinish={handleSubmit} layout="vertical">
      <Form.Item
        name="device_id"
        label="Device ID"
        rules={[{ required: true, message: 'Please input the device ID!' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="snmp_version"
        label="SNMP Version"
        rules={[{ required: true, message: 'Please select an SNMP version!' }]}
      >
        <Select>
          <Option value="v1">v1</Option>
          <Option value="v2c">v2c</Option>
          <Option value="v3">v3</Option>
        </Select>
      </Form.Item>
      <Form.Item
        noStyle
        shouldUpdate={(prevValues, currentValues) => prevValues.snmp_version !== currentValues.snmp_version}
      >
        {({ getFieldValue }) =>
          getFieldValue('snmp_version') !== 'v3' ? (
            <Form.Item
              name="community_string"
              label="Community String"
              rules={[{ required: true, message: 'Please input the community string!' }]}
            >
              <Input />
            </Form.Item>
          ) : (
            <Form.Item
              name="username"
              label="Username"
              rules={[{ required: true, message: 'Please input the username!' }]}
            >
              <Input />
            </Form.Item>
          )
        }
      </Form.Item>
      <Form.Item
        name="polling_interval"
        label="Polling Interval (seconds)"
        rules={[{ required: true, message: 'Please input the polling interval!' }]}
      >
        <InputNumber min={1} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item name="is_active" label="Active" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" style={{ marginRight: 8 }}>
          Save
        </Button>
        <Button onClick={onCancel}>
          Cancel
        </Button>
      </Form.Item>
    </Form>
  );
};

export default SNMPProfileForm;