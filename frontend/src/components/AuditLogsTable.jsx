import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Spin, Typography, Modal, Descriptions, Tag, Button } from 'antd';
import axios from 'axios';

const { Title, Text } = Typography;

function AuditLogsTable() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 15,
    total: 0,
  });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      message.error('Authentication token not found. Please log in.');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get('/api/v1/audit-logs/', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setLogs(response.data.items);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
      }));
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to view audit logs.');
      } else {
        message.error('Failed to fetch audit logs.');
      }
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Destructure pagination values to use as stable, primitive dependencies in useEffect
  const { current, pageSize } = pagination;

  useEffect(() => {
    fetchData({ pagination: { current, pageSize } });
  }, [fetchData, current, pageSize]);

  const handleTableChange = (newPagination) => {
    // Only update the parts of pagination that antd gives us on change
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const showDetailsModal = (record) => {
    setSelectedLog(record);
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setSelectedLog(null);
  };

  const renderChangedFields = (changedFields) => {
    if (!changedFields || Object.keys(changedFields).length === 0) {
      return <Text type="secondary">No fields were changed.</Text>;
    }
    return (
      <Descriptions bordered column={1} size="small">
        {Object.entries(changedFields).map(([field, values]) => (
          <Descriptions.Item key={field} label={field}>
            <Text delete>{JSON.stringify(values.before)}</Text>
            <br />
            <Text strong style={{ color: '#52c41a' }}>{JSON.stringify(values.after)}</Text>
          </Descriptions.Item>
        ))}
      </Descriptions>
    );
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    {
      title: 'Timestamp',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
    },
    { title: 'User', dataIndex: 'user_name', key: 'user_name' },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      render: (action) => {
        const color = action.includes('update') ? 'orange' : action.includes('create') ? 'green' : 'volcano';
        return <Tag color={color}>{action.toUpperCase()}</Tag>;
      },
    },
    { title: 'Resource', dataIndex: 'table_name', key: 'table_name' },
    { title: 'Record ID', dataIndex: 'record_id', key: 'record_id' },
    { title: 'IP Address', dataIndex: 'ip_address', key: 'ip_address' },
    {
      title: 'Details',
      key: 'details',
      render: (_, record) => (
        <Button size="small" onClick={() => showDetailsModal(record)} disabled={!record.changed_fields}>
          View Changes
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>System Audit Logs</Title>
      <Table
        dataSource={logs}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        style={{ marginTop: 20 }}
      />
      {selectedLog && (
        <Modal
          title={`Details for Log #${selectedLog.id}`}
          open={isModalVisible}
          onCancel={handleModalCancel}
          footer={null}
          width={800}
        >
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="User">{selectedLog.user_name} (ID: {selectedLog.user_id})</Descriptions.Item>
            <Descriptions.Item label="Timestamp">{new Date(selectedLog.created_at).toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="Action">{selectedLog.action.toUpperCase()}</Descriptions.Item>
            <Descriptions.Item label="Risk Level">{selectedLog.risk_level}</Descriptions.Item>
            <Descriptions.Item label="Resource">{selectedLog.table_name}</Descriptions.Item>
            <Descriptions.Item label="Record ID">{selectedLog.record_id}</Descriptions.Item>
            <Descriptions.Item label="Request URL" span={2}>{selectedLog.request_url}</Descriptions.Item>
          </Descriptions>
          <Title level={4} style={{ marginTop: 24 }}>Changed Fields</Title>
          {renderChangedFields(selectedLog.changed_fields)}
        </Modal>
      )}
    </div>
  );
}

export default AuditLogsTable;