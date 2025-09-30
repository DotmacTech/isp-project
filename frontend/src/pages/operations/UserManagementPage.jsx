import React, { useState, useEffect, useCallback } from 'react';
import { Table, Spin, message, Typography, Tag, Button, Modal, Form, Input, Select, Popconfirm, Space } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;

const UserManagementPage = () => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [userRoles, setUserRoles] = useState({});
  const [userPermissions, setUserPermissions] = useState({});
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // Modal states
  const [isUserModalVisible, setIsUserModalVisible] = useState(false);
  const [isRolesModalVisible, setIsRolesModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingRolesUser, setEditingRolesUser] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [form] = Form.useForm();
  const [rolesForm] = Form.useForm();


  const fetchData = useCallback(async (params = {}) => {
      try {
        setLoading(true);
        const usersResponse = await apiClient.get('/v1/users/', {
          params: {
            skip: (params.pagination.current - 1) * params.pagination.pageSize,
            limit: params.pagination.pageSize,
          },
        });
        
        // The API returns a paginated response: { items: [], total: ... }
        const pageUsers = Array.isArray(usersResponse.data.items) ? usersResponse.data.items : [];
        setUsers(pageUsers);
        setPagination(prev => ({ ...prev, total: usersResponse.data.total, current: params.pagination.current }));

        if (pageUsers.length > 0) {
          const rolesPromises = pageUsers.map(user =>
            user && user.id ? apiClient.get(`/v1/user-roles/${user.id}`)
              .then(res => ({ userId: user.id, roles: res.data }))
              .catch(() => ({ userId: user.id, roles: [] })) : Promise.resolve({ userId: undefined, roles: [] })
          );
          const rolesResults = await Promise.all(rolesPromises);

          const newUserRoles = {};
          const newUserPermissions = {};
          for (const { userId, roles } of rolesResults) {
            if (!userId) continue;
            newUserRoles[userId] = Array.isArray(roles) ? roles.map(ur => ur.role && ur.role.name ? ur.role.name : '') : [];
            const permissions = Array.isArray(roles) ? roles.flatMap(ur => ur.role && ur.role.permissions ? ur.role.permissions.map(p => p.code) : []) : [];
            newUserPermissions[userId] = [...new Set(permissions)];
          }
          setUserRoles(prev => ({ ...prev, ...newUserRoles }));
          setUserPermissions(prev => ({ ...prev, ...newUserPermissions }));
        }

      } catch (error) {
        console.error('Failed to fetch users:', error);
        message.error('Could not fetch users. You may not have the required permissions.');
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    fetchData({ pagination });
  }, [fetchData, pagination.current, pagination.pageSize]);

  useEffect(() => {
    const fetchAllRoles = async () => {
      try {
        const response = await apiClient.get('/v1/roles/');
        setRoles(response.data);
      } catch (error) {
        message.error('Failed to fetch roles.');
      }
    };
    fetchAllRoles();
  }, []);

  const handleAdd = () => {
    setEditingUser(null);
    form.resetFields();
    setIsUserModalVisible(true);
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    form.setFieldsValue({ ...user, password: '' });
    setIsUserModalVisible(true);
  };

  const handleDelete = async (userId) => {
    try {
      await apiClient.delete(`/v1/users/${userId}`);
      message.success('User deleted successfully');
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete user.');
    }
  };

  const handleEditRoles = (user) => {
    setEditingRolesUser(user);
    const userRoleIds = roles
      .filter(role => (userRoles[user.id] || []).includes(role.name))
      .map(role => role.id);
    rolesForm.setFieldsValue({ role_ids: userRoleIds });
    setIsRolesModalVisible(true);
  };

  const handleUserModalCancel = () => {
    setIsUserModalVisible(false);
    setEditingUser(null);
  };

  const handleRolesModalCancel = () => {
    setIsRolesModalVisible(false);
    setEditingRolesUser(null);
  };

  const handleUserFormFinish = async (values) => {
    setIsSubmitting(true);
    const method = editingUser ? 'put' : 'post';
    const url = editingUser ? `/v1/users/${editingUser.id}` : '/v1/users/';

    if (editingUser && !values.password) {
      delete values.password;
    }

    try {
      await apiClient[method](url, values);
      message.success(`User ${editingUser ? 'updated' : 'created'} successfully.`);
      setIsUserModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save user.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRolesFormFinish = async (values) => {
    if (!editingRolesUser) return;
    setIsSubmitting(true);
    try {
      await apiClient.put(
        `/v1/user-roles/${editingRolesUser.id}/sync-roles`,
        { role_ids: values.role_ids }
      );
      message.success('Roles updated successfully');
      setIsRolesModalVisible(false);
      // Manually update local state for immediate feedback before refetch
      const updatedRoleNames = roles.filter(r => values.role_ids.includes(r.id)).map(r => r.name);
      setUserRoles(prev => ({...prev, [editingRolesUser.id]: updatedRoleNames}));
      fetchData({ pagination }); // Refetch to get updated permissions etc.
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to update roles.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTableChange = (newPagination) => {
    fetchData({ pagination: newPagination });
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', sorter: (a, b) => a.id - b.id },
    { title: 'Full Name', dataIndex: 'full_name', key: 'full_name', sorter: (a, b) => (a.full_name || '').localeCompare(b.full_name || '') },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Kind', dataIndex: 'kind', key: 'kind', render: kind => <Tag>{kind ? kind.toUpperCase() : ''}</Tag> },
    { 
      title: 'Status', 
      dataIndex: 'is_active', 
      key: 'is_active', 
      render: isActive => (
        <Tag color={isActive ? 'green' : 'red'}>{isActive ? 'Active' : 'Inactive'}</Tag>
      ),
      filters: [
        { text: 'Active', value: true },
        { text: 'Inactive', value: false },
      ],
      onFilter: (value, record) => record.is_active === value,
    },
    {
      title: 'Roles',
      dataIndex: 'id',
      key: 'roles',
      render: (userId) => Array.isArray(userRoles[userId]) && userRoles[userId].length > 0 ? userRoles[userId].join(', ') : <Spin size="small" />,
    },
    {
      title: 'Permissions',
      dataIndex: 'id',
      key: 'permissions',
      render: (userId) => {
        const perms = Array.isArray(userPermissions[userId]) ? userPermissions[userId] : [];
        if (perms.length > 3) {
          return `${perms.slice(0, 3).join(', ')}...`;
        }
        return perms.length > 0 ? perms.join(', ') : <Spin size="small" />;
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)}>Edit</Button>
          <Button size="small" onClick={() => handleEditRoles(record)}>Roles</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>User Management</Title>
      <Button onClick={handleAdd} type="primary" style={{ marginBottom: 16 }}>
        Create User
      </Button>
      <Table
        dataSource={users}
        columns={columns}
        rowKey="id"
        pagination={pagination}
        loading={loading}
        onChange={handleTableChange}
      />
      <Modal title={editingUser ? 'Edit User' : 'Create User'} open={isUserModalVisible} onCancel={handleUserModalCancel} footer={null} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={handleUserFormFinish} initialValues={{ is_active: true, kind: 'staff' }}>
          <Form.Item name="full_name" label="Full Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}><Input /></Form.Item>
          <Form.Item name="password" label="Password" help={editingUser ? 'Leave blank to keep current password' : ''} rules={[{ required: !editingUser }]}><Input.Password /></Form.Item>
          <Form.Item name="kind" label="User Kind" rules={[{ required: true }]}>
            <Select><Select.Option value="staff">Staff</Select.Option><Select.Option value="customer">Customer</Select.Option></Select>
          </Form.Item>
          <Form.Item name="is_active" label="Active" valuePropName="checked"><Select><Select.Option value={true}>Yes</Select.Option><Select.Option value={false}>No</Select.Option></Select></Form.Item>
          <Button type="primary" htmlType="submit" loading={isSubmitting} style={{ width: '100%' }}>{editingUser ? 'Save Changes' : 'Create User'}</Button>
        </Form>
      </Modal>
      <Modal title={`Edit Roles for ${editingRolesUser?.full_name}`} open={isRolesModalVisible} onCancel={handleRolesModalCancel} footer={null} destroyOnHidden>
        <Form form={rolesForm} layout="vertical" onFinish={handleRolesFormFinish}>
          <Form.Item name="role_ids" label="Roles">
            <Select mode="multiple" placeholder="Select roles" style={{ width: '100%' }} loading={!roles.length}>
              {roles.map(role => <Select.Option key={role.id} value={role.id}>{role.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={isSubmitting} style={{ width: '100%' }}>Save Roles</Button>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagementPage;