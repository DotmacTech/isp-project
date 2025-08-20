import React, { useState, useEffect } from 'react';
import { Table, message, Button, Modal, Form, Input, Popconfirm, Space } from 'antd';
import axios from 'axios';

function PermissionsTable() {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState(null);
  const [form] = Form.useForm();

  const fetchPermissions = async () => {
    setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        message.error('No access token found. Please log in.');
        setLoading(false);
        return;
      }
      try {
        const response = await axios.get('/api/v1/permissions/', {
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

  useEffect(() => {
    fetchPermissions();
  }, []);

  const handleAddPermission = () => {
    setEditingPermission(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    setEditingPermission(null);
    form.resetFields();
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');

    try {
      if (editingPermission) {
        await axios.put(`/api/v1/permissions/${editingPermission.id}`, values, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        await axios.post('/api/v1/permissions/', values, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      message.success(`Permission ${editingPermission ? 'updated' : 'added'} successfully`);
      setModalVisible(false);
      fetchPermissions();
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to ${editingPermission ? 'update' : 'add'} permission.`);
      console.error('Error submitting permission:', error);
    }
  };

  const handleEditPermission = (permission) => {
    setEditingPermission(permission);
    form.setFieldsValue(permission);
    setModalVisible(true);
  };

  const handleDeletePermission = async (permissionId) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.delete(`/api/v1/permissions/${permissionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success('Permission deleted successfully');
      setPermissions(currentPermissions => currentPermissions.filter(p => p.id !== permissionId));
    } catch (error) {
      message.error('Failed to delete permission.');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Permission Code',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Module',
      dataIndex: 'module',
      key: 'module',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEditPermission(record)}>Edit</Button>
          <Popconfirm title="Are you sure you want to delete this permission?" onConfirm={() => handleDeletePermission(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
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
        title={editingPermission ? 'Edit Permission' : 'Add Permission'}
        open={modalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="code" label="Code" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="module" label="Module" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
              {editingPermission ? 'Save Changes' : 'Add Permission'}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default PermissionsTable;