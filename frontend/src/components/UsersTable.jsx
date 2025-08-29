import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Spin, Popconfirm, Space } from 'antd';
import apiClient from '../api';

function UsersTable() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [editingUser, setEditingUser] = useState(null);
  const [editRolesForm] = Form.useForm(); // Use a separate form instance for Edit Roles modal
  const [rolesMap, setRolesMap] = useState({});
  const [permissionsMap, setPermissionsMap] = useState({});
  const [editRolesModal, setEditRolesModal] = useState({ visible: false, user: null });
  const [allRoles, setAllRoles] = useState([]);
  const [assigning, setAssigning] = useState(false);

  const fetchData = useCallback(async () => { // Using useCallback to memoize the function
    setLoading(true);
    try { // Using a single try-catch block for all fetches improves error handling
      // Fetch users and all available roles in parallel for efficiency
      const [usersRes, rolesRes] = await Promise.all([
        apiClient.get('/v1/users/'),
        apiClient.get('/v1/roles/')
      ]);
      
      setUsers(usersRes.data);
      setAllRoles(rolesRes.data);

      // Fetch assigned roles for each user
      const rolesPromises = usersRes.data.map(user =>
        apiClient.get(`/v1/user-roles/${user.id}`)
          .then(res => ({ userId: user.id, roles: res.data }))
          .catch(() => ({ userId: user.id, roles: [] }))
      );
      const rolesResults = await Promise.all(rolesPromises);

      // Map userId to roles and permissions
      const newRolesMap = {};
      const newPermissionsMap = {};
      for (const { userId, roles } of rolesResults) {
        const userRoles = roles.map(r => r.role?.name || `RoleID: ${r.role_id}`).filter(Boolean);
        newRolesMap[userId] = userRoles;
        
        const userPermissions = roles.flatMap(r => r.role?.permissions?.map(p => p.code) || []);
        newPermissionsMap[userId] = [...new Set(userPermissions)]; // <-- FIX: Added closing bracket and semicolon
      }
      setRolesMap(newRolesMap);
      setPermissionsMap(newPermissionsMap);

    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to view users or roles.');
      } else {
        message.error('Failed to fetch data.');
      }
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []); // Empty dependency array is correct as it doesn't depend on props or state

  useEffect(() => {
    fetchData();
  }, [fetchData]); // Run fetchData when the component mounts

  const handleAddUser = () => {
    setModalVisible(true);
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    form.resetFields();
  };

  const handleFormFinish = async (values) => {
    // When editing, if the password field is empty, don't send it in the payload
    if (editingUser && !values.password) {
      delete values.password;
    }

    try {
      if (editingUser) {
        // Update existing user
        await apiClient.put(`/v1/users/${editingUser.id}`, values);
      } else {
        // Create new user
        await apiClient.post('/v1/users/', values);
      }
      message.success(`User ${editingUser ? 'updated' : 'added'} successfully`);
      setModalVisible(false);
      setEditingUser(null);
      form.resetFields();
      fetchData(); // Refresh all data efficiently
    } catch (error) {
      const errorDetail = error.response?.data?.detail;
      const errorMessage = Array.isArray(errorDetail) ? errorDetail.map(e => `${e.loc[1]}: ${e.msg}`).join('; ') : errorDetail || `Failed to ${editingUser ? 'update' : 'add'} user`;
      message.error(errorMessage);
      console.error('Error submitting user:', error);
    }
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
    form.setFieldsValue({
      ...user,
      password: '', // Clear password field for editing
    });
    setModalVisible(true);
  };

  const handleDeleteUser = async (userId) => {
    try {
      await apiClient.delete(`/v1/users/${userId}`);
      message.success('User deleted successfully');
      // Manually filter out the deleted user from the local state
      // to provide immediate UI feedback without a full re-fetch.
      setUsers(currentUsers => currentUsers.filter(user => user.id !== userId));
    } catch (error) {
      message.error('Failed to delete user.');
    }
  };

  const handleEditRoles = (user) => {
    // Get the role IDs for the user's current roles to populate the form
    const userRoleIds = allRoles
      .filter(role => (rolesMap[user.id] || []).includes(role.name))
      .map(role => role.id);

    setEditRolesModal({ visible: true, user });
    editRolesForm.setFieldsValue({ role_ids: userRoleIds });
  };

  const handleEditRolesCancel = () => {
    setEditRolesModal({ visible: false, user: null });
    editRolesForm.resetFields();
  };

  // Refactored to use the single, efficient sync-roles endpoint
  const handleEditRolesFinish = async (values) => {
    if (!editRolesModal.user) return;
    setAssigning(true);
    try {
      await apiClient.put(
        `/v1/user-roles/${editRolesModal.user.id}/sync-roles`,
        { role_ids: values.role_ids } // Send the array of role IDs
      );

      message.success('Roles updated successfully');
      setEditRolesModal({ visible: false, user: null });
      editRolesForm.resetFields();
      fetchData(); // Refresh all data
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to edit roles.');
      } else {
        message.error('Failed to update roles');
      }
      console.error('Error updating roles:', error);
    } finally {
      setAssigning(false);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Full Name',
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: 'Kind',
      dataIndex: 'kind',
      key: 'kind',
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (text) => (text ? 'Yes' : 'No'),
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: 'Roles',
      dataIndex: 'id',
      key: 'roles',
      render: (userId, record) =>
        <>
          {rolesMap[userId] ? rolesMap[userId].join(', ') : <Spin size="small" />}
          <Button size="small" style={{ marginLeft: 8 }} onClick={() => handleEditRoles(record)}>
            Edit Roles
          </Button>
        </>,
    },
    {
      title: 'Permissions',
      dataIndex: 'id',
      key: 'permissions',
      render: (userId) =>
        permissionsMap[userId] && permissionsMap[userId].length > 0
          ? permissionsMap[userId].join(', ')
          : <Spin size="small" />,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="middle">
          <Button size="small" onClick={() => handleEditUser(record)}>
            Edit User
          </Button>
          <Popconfirm title="Are you sure you want to delete this user?" onConfirm={() => handleDeleteUser(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2>Users</h2>
      <Button type="primary" onClick={handleAddUser} style={{ marginBottom: 16 }}>
        Add User
      </Button>
      <Table dataSource={users} columns={columns} rowKey="id" loading={loading} />
      <Modal
        title={editingUser ? 'Edit User' : 'Add User'}
        open={modalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password" help={editingUser ? 'Leave blank to keep current password' : ''} rules={[{ required: !editingUser }]}>
            <Input.Password placeholder="New Password" />
          </Form.Item>
          <Form.Item name="full_name" label="Full Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
              {editingUser ? 'Save Changes' : 'Add User'}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
      {/* Edit Roles Modal */}
      <Modal
        title={`Edit Roles for ${editRolesModal.user?.email || ''}`}
        open={editRolesModal.visible}
        onCancel={handleEditRolesCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={editRolesForm} layout="vertical" onFinish={handleEditRolesFinish}>
          <Form.Item name="role_ids" label="Roles" rules={[{ required: true }]}>
            <Select mode="multiple" placeholder="Select roles">
              {allRoles.map(role => (
                <Select.Option key={role.id} value={role.id}>{role.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={assigning} style={{ width: '100%' }}>
              Save
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default UsersTable;