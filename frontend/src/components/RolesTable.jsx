import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Table, Button, Modal, Form, Checkbox, message, Spin, Typography, Row, Col, Tag, Input, Select, Popconfirm, Space } from 'antd';
import axios from 'axios';

const { Title } = Typography;

function RolesTable() {
  const [roles, setRoles] = useState([]);
  const [allPermissions, setAllPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isRoleModalVisible, setIsRoleModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form] = Form.useForm();
  const [roleForm] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      message.error('Authentication token not found. Please log in.');
      setLoading(false);
      return;
    }

    try {
      const [rolesRes, permissionsRes] = await Promise.all([
        axios.get('/api/v1/roles/', { headers: { Authorization: `Bearer ${token}` } }),
        axios.get('/api/v1/permissions/', { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setRoles(rolesRes.data);
      setAllPermissions(permissionsRes.data);
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to manage roles.');
      } else {
        message.error('Failed to fetch roles and permissions.');
      }
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const groupedPermissions = useMemo(() => {
    return allPermissions.reduce((acc, permission) => {
      const module = permission.module || 'general';
      if (!acc[module]) {
        acc[module] = [];
      }
      acc[module].push({ label: permission.description, value: permission.code });
      return acc;
    }, {});
  }, [allPermissions]);

  const handleAddRole = () => {
    setEditingRole(null);
    roleForm.resetFields();
    setIsRoleModalVisible(true);
  };

  const handleEditPermissions = (role) => {
    setEditingRole(role);
    form.setFieldsValue({
      permission_codes: role.permissions.map(p => p.code),
    });
    setIsModalVisible(true);
  };

  const handleEditRole = (role) => {
    setEditingRole(role);
    roleForm.setFieldsValue(role);
    setIsRoleModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingRole(null);
    form.resetFields();
  };

  const handleFormFinish = async (values) => {
    setIsSubmitting(true);
    const token = localStorage.getItem('access_token');

    try {
      await axios.put(
        `/api/v1/roles/${editingRole.id}`,
        { permission_codes: values.permission_codes },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      message.success(`Permissions for role "${editingRole.name}" updated successfully.`);
      handleModalCancel();
      fetchData(); // Refresh data to show updated permissions
    } catch (error) {
      message.error('Failed to update permissions.');
      console.error('Error updating role permissions:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRoleFormFinish = async (values) => {
    setIsSubmitting(true);
    const token = localStorage.getItem('access_token');

    try {
      if (editingRole) {
        await axios.put(`/api/v1/roles/${editingRole.id}`, values, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        await axios.post('/api/v1/roles/', values, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      message.success(`Role ${editingRole ? 'updated' : 'created'} successfully.`);
      setIsRoleModalVisible(false);
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to ${editingRole ? 'update' : 'create'} role.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteRole = async (roleId) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.delete(`/api/v1/roles/${roleId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success('Role deleted successfully');
      setRoles(currentRoles => currentRoles.filter(role => role.id !== roleId));
    } catch (error) {
      message.error('Failed to delete role.');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Role Name', dataIndex: 'name', key: 'name' },
    { title: 'Description', dataIndex: 'description', key: 'description' },
    {
      title: 'Scope',
      dataIndex: 'scope',
      key: 'scope',
      render: (scope) => <Tag>{scope.toUpperCase()}</Tag>,
    },
    {
      title: 'Permissions Count',
      dataIndex: 'permissions',
      key: 'permissions_count',
      render: (permissions) => permissions.length,
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEditRole(record)}>
            Edit Role
          </Button>
          <Button size="small" onClick={() => handleEditPermissions(record)}>
            Permissions
          </Button>
          <Popconfirm title="Are you sure you want to delete this role?" onConfirm={() => handleDeleteRole(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Role Management</Title>
      <Button type="primary" onClick={handleAddRole} style={{ marginBottom: 16 }}>Add Role</Button>
      <Table
        dataSource={roles}
        columns={columns}
        rowKey="id"
        loading={loading}
      />
      {editingRole && (
        <Modal
          title={`Edit Permissions for "${editingRole.name}"`}
          open={isModalVisible}
          onCancel={handleModalCancel}
          footer={[
            <Button key="back" onClick={handleModalCancel}>
              Cancel
            </Button>,
            <Button key="submit" type="primary" loading={isSubmitting} onClick={() => form.submit()}>
              Save Permissions
            </Button>,
          ]}
          width={800}
          destroyOnClose
        >
          <Form form={form} layout="vertical" onFinish={handleFormFinish} initialValues={{ permission_codes: editingRole.permissions.map(p => p.code) }}>
            <Form.Item name="permission_codes">
              <Checkbox.Group style={{ width: '100%' }}>
                {Object.entries(groupedPermissions).map(([module, perms]) => (
                  <div key={module} style={{ marginBottom: '16px' }}>
                    <Title level={5} style={{ textTransform: 'capitalize', borderBottom: '1px solid #f0f0f0', paddingBottom: '8px' }}>
                      {module}
                    </Title>
                    <Row>
                      {perms.map(perm => (
                        <Col span={12} key={perm.value}>
                          <Checkbox value={perm.value}>{perm.label}</Checkbox>
                        </Col>
                      ))}
                    </Row>
                  </div>
                ))}
              </Checkbox.Group>
            </Form.Item>
          </Form>
        </Modal>
      )}
      <Modal
        title={editingRole ? 'Edit Role' : 'Add Role'}
        open={isRoleModalVisible}
        onCancel={() => setIsRoleModalVisible(false)}
        footer={null}
        destroyOnClose
      >
        <Form form={roleForm} layout="vertical" onFinish={handleRoleFormFinish}>
          <Form.Item name="name" label="Role Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="scope" label="Scope" rules={[{ required: true }]} initialValue="system">
            <Select>
              <Select.Option value="system">System</Select.Option>
              <Select.Option value="customer">Customer</Select.Option>
              <Select.Option value="reseller">Reseller</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={isSubmitting} style={{ width: '100%' }}>
              {editingRole ? 'Save Role' : 'Create Role'}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default RolesTable;