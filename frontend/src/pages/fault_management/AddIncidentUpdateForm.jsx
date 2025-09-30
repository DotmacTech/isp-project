import React, { useState } from 'react';
import { Form, Input, Button, Space } from 'antd';

const { TextArea } = Input;

const AddIncidentUpdateForm = ({ onAddUpdate }) => {
  const [form] = Form.useForm();

  const handleSubmit = (values) => {
    if (!values.content.trim()) return;
    onAddUpdate(values.content);
    form.resetFields();
  };

  return (
    <Form form={form} onFinish={handleSubmit} layout="vertical">
      <Form.Item name="content" rules={[{ required: true, message: 'Please enter update content!' }]}>
        <TextArea rows={4} placeholder="Add a comment or update..." />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Post Update
        </Button>
      </Form.Item>
    </Form>
  );
};

export default AddIncidentUpdateForm;