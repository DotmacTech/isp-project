import React, { useState, useEffect } from 'react';
import { Table, message, Button, Modal, Form, Input } from 'antd';
import axios from 'axios';

function PermissionsTable() {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    const fetchPermissions = async () => {
      const token = localStorage.getItem('access_token');
      console.log('access_token:', token); // Debug: log the token
      if (!token) {
        message.error('No access token found. Please log in.');
        setLoading(false);
        return;
      }
      try {
        const response = await axios.get('/api/permissions/', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setPermissions(response.data);
      } catch (error) {
        if (error.response && error.response.status === 401) {
          message.error('Session expired or unauthorized. Please log in again.');
        } else {
          message.error('Failed to fetch permissions.');
        }
        console.error('Error fetching permissions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPermissions();
  }, []);

  const handleAddPermission = () => {
    setModalVisible(true);
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    form.resetFields();
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.post('/api/permissions/', values, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      message.success('Permission added successfully');
      setModalVisible(false);
      form.resetFields();
      // Refresh permissions list
      setLoading(true);
      const response = await axios.get('/api/permissions', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setPermissions(response.data);
    } catch (error) {
      message.error('Failed to add permission');
      console.error('Error adding permission:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Code',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
  ];

  return (
    <div>
      <h2>Permissions</h2>
      <Button type="primary" onClick={handleAddPermission} style={{ marginBottom: 16 }}>
        Add Permission
      </Button>
      <Table dataSource={permissions} columns={columns} rowKey="id" loading={loading} />
      <Modal
        title="Add Permission"
        open={modalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="code" label="Code" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input />
          </Form.Item>
          {/* Add more fields as needed */}
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
              Add
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default PermissionsTable;