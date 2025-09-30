import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Modal, message, Space, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import SNMPProfileForm from '../../components/network/SNMPProfileForm';

const SNMPProfileManagementPage = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentProfile, setCurrentProfile] = useState(null);

  const fetchProfiles = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/v1/network/snmp-profiles/');
      setProfiles(response.data.items || []);
    } catch (err) {
      message.error(`Failed to fetch SNMP profiles: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const handleOpenModal = (profile = null) => {
    setCurrentProfile(profile);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCurrentProfile(null);
  };

  const handleSaveProfile = async (profileData) => {
    try {
      if (currentProfile) {
        await apiClient.put(`/v1/network/snmp-profiles/${currentProfile.id}`, profileData);
        message.success('SNMP profile updated successfully');
      } else {
        await apiClient.post('/v1/network/snmp-profiles/', profileData);
        message.success('SNMP profile created successfully');
      }
      fetchProfiles();
      handleCloseModal();
    } catch (err) {
      message.error(`Failed to save SNMP profile: ${err.message}`);
    }
  };

  const handleDeleteProfile = async (profileId) => {
    try {
      await apiClient.delete(`/v1/network/snmp-profiles/${profileId}`);
      message.success('SNMP profile deleted successfully');
      fetchProfiles();
    } catch (err) {
      message.error(`Failed to delete SNMP profile: ${err.message}`);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Device ID', dataIndex: 'device_id', key: 'device_id' },
    { title: 'Version', dataIndex: 'snmp_version', key: 'snmp_version' },
    {
      title: 'Community/Username',
      key: 'community_username',
      render: (_, record) => (
        <span>
          {record.snmp_version === 'v3'
            ? record.username
            : record.community_string}
        </span>
      ),
    },
    { title: 'Polling Interval', dataIndex: 'polling_interval', key: 'polling_interval', render: (interval) => `${interval}s` },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>{isActive ? 'Yes' : 'No'}</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="middle">
          <Button icon={<EditOutlined />} onClick={() => handleOpenModal(record)}>
            Edit
          </Button>
          <Button icon={<DeleteOutlined />} danger onClick={() => handleDeleteProfile(record.id)}>
            Delete
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>SNMP Profile Management</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
          Add SNMP Profile
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={profiles}
        loading={loading}
        rowKey="id"
      />
      <Modal
        title={currentProfile ? 'Edit SNMP Profile' : 'Add New SNMP Profile'}
        visible={isModalOpen}
        onCancel={handleCloseModal}
        footer={null}
      >
        <SNMPProfileForm
          profile={currentProfile}
          onSave={handleSaveProfile}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  );
};

export default SNMPProfileManagementPage;