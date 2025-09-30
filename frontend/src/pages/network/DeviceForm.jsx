import React, { useState, useEffect } from 'react';
import { Form, Input, InputNumber, Switch, Button, Space } from 'antd';

const DeviceForm = ({ device, onSave, onCancel }) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (device) {
      form.setFieldsValue({
        title: device.title || '',
        ip: device.ip || '',
        description: device.description || '',
        device_type_id: device.device_type_id,
        group_id: device.group_id,
        producer_id: device.producer_id,
        site_id: device.site_id,
        is_active: device.is_active !== undefined ? device.is_active : true,
      });
    } else {
      form.resetFields();
      form.setFieldsValue({ is_active: true }); // Default for new device
    }
  }, [device, form]);

  const onFinish = (values) => {
    // Convert empty strings for IDs to null for the backend
    const dataToSave = {
      ...values,
      device_type_id: values.device_type_id || null,
      group_id: values.group_id || null,
      producer_id: values.producer_id || null,
      site_id: values.site_id || null,
    };
    onSave(dataToSave);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={{ is_active: true }}
    >
      <Form.Item
        name="title"
        label="Title"
        rules={[{ required: true, message: 'Please input the device title!' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="ip"
        label="IP Address"
        rules={[{ required: true, message: 'Please input the IP address!' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="description"
        label="Description"
      >
        <Input.TextArea rows={4} />
      </Form.Item>
      
      <Space>
        <Form.Item
          name="device_type_id"
          label="Device Type ID"
        >
          <InputNumber placeholder="e.g., 1" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item
          name="group_id"
          label="Group ID"
        >
          <InputNumber placeholder="e.g., 1" style={{ width: '100%' }} />
        </Form.Item>
      </Space>
      <Space>
        <Form.Item
          name="producer_id"
          label="Producer ID"
        >
          <InputNumber placeholder="e.g., 1" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item
          name="site_id"
          label="Site ID"
        >
          <InputNumber placeholder="e.g., 1" style={{ width: '100%' }} />
        </Form.Item>
      </Space>

      <Form.Item name="is_active" label="Active" valuePropName="checked">
        <Switch />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit">
            Save Device
          </Button>
          <Button htmlType="button" onClick={onCancel}>
            Cancel
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default DeviceForm;