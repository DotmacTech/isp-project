import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Typography, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import PermissionsTable from '../../components/PermissionsTable';
import PermissionForm from '../../components/PermissionForm';
import apiClient from '../../services/api';

const { Title } = Typography;

const PermissionsPage = () => {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState(null);

  const fetchPermissions = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/v1/permissions/');
      setPermissions(response.data);
    } catch (error) {
      message.error('Failed to fetch permissions.');
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
    setIsModalVisible(true);
  };

  const handleEditPermission = (permission) => {
    setEditingPermission(permission);
    setIsModalVisible(true);
  };

  const handleDeletePermission = async (permissionId) => {
    try {
      await apiClient.delete(`/v1/permissions/${permissionId}`);
      message.success('Permission deleted successfully.');
      fetchPermissions();
    } catch (error) {
      message.error('Failed to delete permission.');
      console.error('Error deleting permission:', error);
    }
  };

  const handleFormSubmit = () => {
    fetchPermissions();
    setIsModalVisible(false);
  };

  return (
    <div>
     
      <Card className="mb-6">
        <PermissionsTable
          permissions={permissions}
          loading={loading}
          onEdit={handleEditPermission}
          onDelete={handleDeletePermission}
        />
      </Card>
    </div>
  );
};

export default PermissionsPage;