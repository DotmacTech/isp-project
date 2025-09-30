import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Table, message, Button, Modal, Form, Input, Checkbox, Row, Col, Tag, Popconfirm, Space, Typography, Select, Alert, Spin } from 'antd';
import apiClient from '../services/api';

const { Title } = Typography;

function RolesTable() {
  console.log('RolesTable component is rendering');
  
  const [roles, setRoles] = useState([]);
  const [allPermissions, setAllPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isRoleModalVisible, setIsRoleModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form] = Form.useForm();
  const [roleForm] = Form.useForm();

  const fetchData = useCallback(async () => {
    console.log('RolesTable: fetchData called');
    setLoading(true);
    setError(null);

    try {
      console.log('Fetching roles and permissions...');
      const [rolesRes, permissionsRes] = await Promise.all([
        apiClient.get('/v1/roles/'),
        apiClient.get('/v1/permissions/')
      ]);
      console.log('Roles data:', rolesRes.data);
      console.log('Permissions data:', permissionsRes.data);
      setRoles(rolesRes.data);
      setAllPermissions(permissionsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch roles and permissions';
      setError(errorMessage);
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to manage roles. Please contact your system administrator.');
      } else {
        message.error('Failed to fetch roles and permissions: ' + errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log('RolesTable: useEffect called');
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

    try {
      await apiClient.put(
        `/v1/roles/${editingRole.id}`,
        { permission_codes: values.permission_codes }
      );
      message.success(`Permissions for role "${editingRole.name}" updated successfully.`);
      handleModalCancel();
      fetchData(); // Refresh data to show updated permissions
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to update permissions';
      message.error('Failed to update permissions: ' + errorMessage);
      console.error('Error updating role permissions:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRoleFormFinish = async (values) => {
    setIsSubmitting(true);

    try {
      if (editingRole) {
        await apiClient.put(`/v1/roles/${editingRole.id}`, values);
      } else {
        await apiClient.post('/v1/roles/', values);
      }
      message.success(`Role ${editingRole ? 'updated' : 'created'} successfully.`);
      setIsRoleModalVisible(false);
      fetchData();
    } catch (error) {
      const errorMessage = error.response?.data?.detail || `Failed to ${editingRole ? 'update' : 'create'} role`;
      message.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteRole = async (roleId) => {
    try {
      await apiClient.delete(`/v1/roles/${roleId}`);
      message.success('Role deleted successfully');
      setRoles(currentRoles => currentRoles.filter(role => role.id !== roleId));
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete role';
      message.error('Failed to delete role: ' + errorMessage);
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
      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <p>Loading roles and permissions...</p>
        </div>
      ) : (
        <Table
          dataSource={roles}
          columns={columns}
          rowKey="id"
          locale={{ emptyText: error ? 'Error loading data: ' + error : 'No roles found' }}
          pagination={{ pageSize: 10 }}
        />
      )}
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
          destroyOnHidden
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
        destroyOnHidden
      >
        <Form form={roleForm} layout="vertical" onFinish={handleRoleFormFinish}>
          <Form.Item name="name" label="Role Name" rules={[{ required: true, message: 'Please input role name!' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="scope" label="Scope" rules={[{ required: true, message: 'Please select scope!' }]} initialValue="system">
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