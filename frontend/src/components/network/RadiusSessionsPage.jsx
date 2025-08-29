import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Typography, Tag, Switch } from 'antd';
import apiClient from '../../api';
import moment from 'moment';

const { Title } = Typography;

function RadiusSessionsPage() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [activeOnly, setActiveOnly] = useState(true);

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);

    try {
      const response = await apiClient.get('/v1/network/radius-sessions/', {
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
          active_only: params.activeOnly,
        },
      });
      setSessions(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch RADIUS sessions.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination, activeOnly });
  }, [fetchData, pagination.current, pagination.pageSize, activeOnly]);

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const handleActiveToggle = (checked) => {
    setActiveOnly(checked);
    setPagination(prev => ({ ...prev, current: 1 })); // Reset to first page
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Login', dataIndex: 'login', key: 'login' },
    { title: 'Customer', dataIndex: ['customer', 'name'], key: 'customer' },
    { title: 'IP Address', dataIndex: 'ipv4', key: 'ipv4' },
    { title: 'MAC Address', dataIndex: 'mac', key: 'mac' },
    { title: 'NAS', dataIndex: ['nas', 'title'], key: 'nas' },
    { title: 'Start Time', dataIndex: 'start_session', key: 'start_session', render: (text) => moment(text).format('YYYY-MM-DD HH:mm:ss') },
    { title: 'End Time', dataIndex: 'end_session', key: 'end_session', render: (text) => text ? moment(text).format('YYYY-MM-DD HH:mm:ss') : '-' },
    { title: 'Status', dataIndex: 'session_status', key: 'session_status', render: (status) => <Tag color={status === 'active' ? 'green' : 'blue'}>{status?.toUpperCase()}</Tag> },
    { title: 'Terminate Cause', dataIndex: 'terminate_cause', key: 'terminate_cause' },
  ];

  return (
    <div>
      <Title level={2}>RADIUS Sessions</Title>
      <div style={{ marginBottom: 16 }}>
        <Switch checkedChildren="Active Only" unCheckedChildren="All Sessions" checked={activeOnly} onChange={handleActiveToggle} />
      </div>
      <Table
        dataSource={sessions}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        scroll={{ x: 1300 }}
      />
    </div>
  );
}

export default RadiusSessionsPage;