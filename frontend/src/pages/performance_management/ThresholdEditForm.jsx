import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Space, Typography, message } from 'antd';

const { Text } = Typography;

const ThresholdEditForm = ({ metric, onSave, onCancel }) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (metric && metric.thresholds) {
      form.setFieldsValue({
        warning: metric.thresholds.warning,
        critical: metric.thresholds.critical,
      });
    } else {
      form.resetFields();
    }
  }, [metric, form]);

  const onFinish = (values) => {
    const dataToSave = {
      thresholds: {
        warning: values.warning !== undefined && values.warning !== null && values.warning !== '' ? parseFloat(values.warning) : null,
        critical: values.critical !== undefined && values.critical !== null && values.critical !== '' ? parseFloat(values.critical) : null,
      },
    };
    onSave(dataToSave);
  };

  if (!metric) return null;

  return (
    <Form form={form} layout="vertical" onFinish={onFinish}>
      <Text strong>
        Editing thresholds for: {metric.name} (Unit: {metric.unit})
      </Text>
      <Form.Item
        name="warning"
        label="Warning Threshold"
        rules={[
          {
            validator: async (_, value) => {
              if (value === undefined || value === null || value === '') {
                return Promise.resolve();
              }
              if (isNaN(parseFloat(value))) {
                return Promise.reject(new Error('Please enter a valid number'));
              }
              return Promise.resolve();
            },
          },
        ]}
      >
        <Input type="number" step="any" />
      </Form.Item>
      <Form.Item
        name="critical"
        label="Critical Threshold"
        rules={[
          {
            validator: async (_, value) => {
              if (value === undefined || value === null || value === '') {
                return Promise.resolve();
              }
              if (isNaN(parseFloat(value))) {
                return Promise.reject(new Error('Please enter a valid number'));
              }
              return Promise.resolve();
            },
          },
        ]}
      >
        <Input type="number" step="any" />
      </Form.Item>
      <Form.Item>
        <Space>
          <Button onClick={onCancel}>Cancel</Button>
          <Button type="primary" htmlType="submit">
            Save Thresholds
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default ThresholdEditForm;