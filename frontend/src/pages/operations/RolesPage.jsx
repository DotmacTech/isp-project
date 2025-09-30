import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Typography, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import RolesTable from '../../components/RolesTable';
import RoleForm from '../../components/RoleForm';
import apiClient from '../../services/api';

const { Title } = Typography;

const RolesPage = () => {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState(null);

  const fetchRoles = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/v1/roles/');
      setRoles(response.data);
    } catch (error) {
      message.error('Failed to fetch roles.');
      console.error('Error fetching roles:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleAddRole = () => {
    setEditingRole(null);
    setIsModalVisible(true);
  };

  const handleEditRole = (role) => {
    setEditingRole(role);
    setIsModalVisible(true);
  };

  const handleDeleteRole = async (roleId) => {
    try {
      await apiClient.delete(`/v1/roles/${roleId}`);
      message.success('Role deleted successfully.');
      fetchRoles();
    } catch (error) {
      message.error('Failed to delete role.');
      console.error('Error deleting role:', error);
    }
  };

  const handleFormSubmit = () => {
    fetchRoles();
    setIsModalVisible(false);
  };

  return (
    <div>
      
      <Card className="mb-6">
        <RolesTable
          roles={roles}
          loading={loading}
          onEdit={handleEditRole}
          onDelete={handleDeleteRole}
        />
      </Card>
    </div> 
  );
};

export default RolesPage;