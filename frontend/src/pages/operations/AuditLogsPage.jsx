import React, { useState, useEffect, useCallback } from 'react';
import { Card, Typography, message, Modal } from 'antd';
import AuditLogsTable from '../../components/AuditLogsTable';
import apiClient from '../../services/api';

const { Title } = Typography;

const AuditLogsPage = () => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 15,
    total: 0,
  });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchAuditLogs = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const response = await apiClient.get('/v1/audit-logs/', {
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setAuditLogs(response.data.items);
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

  useEffect(() => {
    fetchAuditLogs({ pagination: { current: pagination.current, pageSize: pagination.pageSize } });
  }, [fetchAuditLogs, pagination.current, pagination.pageSize]);

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const handleViewDetails = (record) => {
    setSelectedLog(record);
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setSelectedLog(null);
  };

  return (
    <div className="p-6">
      <Title level={2}>Audit Logs</Title>
      <Card className="mb-6">
        <AuditLogsTable
          auditLogs={auditLogs}
          loading={loading}
          pagination={pagination}
          onTableChange={handleTableChange}
          onViewDetails={handleViewDetails}
          isModalVisible={isModalVisible}
          selectedLog={selectedLog}
          onModalCancel={handleModalCancel}
        />
      </Card>
    </div>
  );
};

export default AuditLogsPage;