import React from 'react';
import { Table, message, Spin, Typography, Modal, Descriptions, Tag, Button } from 'antd';
import { EyeOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const AuditLogsTable = ({ auditLogs, loading, pagination, onTableChange, onViewDetails, isModalVisible, selectedLog, onModalCancel }) => {
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
        <Button size="small" icon={<EyeOutlined />} onClick={() => onViewDetails(record)} disabled={!record.changed_fields}>
          View Changes
        </Button>
      ),
    },
  ];

  return (
    <>
      <Table
        dataSource={auditLogs}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={onTableChange}
        style={{ marginTop: 20 }}
      />
      {selectedLog && (
        <Modal
          title={`Details for Log #${selectedLog.id}`}
          open={isModalVisible}
          onCancel={onModalCancel}
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
    </>
  );
};

export default AuditLogsTable;