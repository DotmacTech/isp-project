import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Table, Button, Modal, Form, Checkbox, message, Spin, Typography, Row, Col, Tag } from 'antd';
import axios from 'axios';

const { Title } = Typography;

function RolesTable() {
  const [roles, setRoles] = useState([]);
  const [allPermissions, setAllPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form] = Form.useForm();

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
        axios.get('/api/roles/', { headers: { Authorization: `Bearer ${token}` } }),
        axios.get('/api/permissions/', { headers: { Authorization: `Bearer ${token}` } })
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

  const handleEditPermissions = (role) => {
    setEditingRole(role);
    form.setFieldsValue({
      permission_codes: role.permissions.map(p => p.code),
    });
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingRole(null);
    form.resetFields();
  };

  const handleFormFinish = async (values) => {
    if (!editingRole) return;
    setIsSubmitting(true);
    const token = localStorage.getItem('access_token');

    try {
      await axios.put(
        `/api/roles/${editingRole.id}`,
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
        <Button onClick={() => handleEditPermissions(record)}>
          Edit Permissions
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Roles & Permissions Management</Title>
      <Table
        dataSource={roles}
        columns={columns}
        rowKey="id"
        loading={loading}
        style={{ marginTop: 20 }}
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
          <Form form={form} layout="vertical" onFinish={handleFormFinish}>
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
    </div>
  );
}

export default RolesTable;