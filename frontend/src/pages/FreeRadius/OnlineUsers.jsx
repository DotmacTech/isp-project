import React, { useState, useEffect, useCallback } from 'react';
import { Table, Tooltip, message, Typography, Tag, Space, Alert } from 'antd';
import { WifiOutlined, ClockCircleOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { getOnlineUsersDetailed } from '../../services/freeRadiusApi';
import moment from 'moment';

const { Text } = Typography;

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = 2;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

const formatDuration = (seconds) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const duration = moment.duration(seconds, 'seconds');
    const days = duration.days();
    const hours = duration.hours();
    const minutes = duration.minutes();
    
    let durationStr = '';
    if (days > 0) durationStr += `${days}d `;
    if (hours > 0) durationStr += `${hours}h `;
    if (minutes > 0) durationStr += `${minutes}m`;
    
    if (durationStr.trim() === '' && seconds > 0) {
        return `${Math.round(seconds)}s`;
    }
    return durationStr.trim() || '0s';
};

const OnlineUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [error, setError] = useState(null);

  const fetchUsers = useCallback((page = pagination.current, pageSize = pagination.pageSize) => {
    setLoading(true);
    setError(null);
    getOnlineUsersDetailed({ skip: (page - 1) * pageSize, limit: pageSize })
      .then(response => {
        setUsers(response.data.items);
        setPagination({ ...pagination, current: page, total: response.data.total });
      })
      .catch(error => {
        setError('Failed to fetch online sessions. Please try again later.');
        console.error(error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [pagination]);

  useEffect(() => {
    fetchUsers(pagination.current, pagination.pageSize);
    const interval = setInterval(() => fetchUsers(pagination.current, pagination.pageSize), 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchUsers, pagination.current, pagination.pageSize]);

  const handleTableChange = (newPagination) => {
    fetchUsers(newPagination.current, newPagination.pageSize);
  };

  const columns = [
    {
      title: 'Customer',
      dataIndex: 'customer_name',
      key: 'customer_name',
      render: (text, record) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          <Text type="secondary">{record.login}</Text>
        </Space>
      ),
    },
    {
      title: 'IP / MAC Address',
      key: 'addresses',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <Text><WifiOutlined /> {record.ip_address || 'N/A'}</Text>
          <Text type="secondary">{record.mac_address || 'N/A'}</Text>
        </Space>
      ),
    },
    {
      title: 'Data Usage (Down / Up)',
      key: 'usage',
      render: (_, record) => (
        <Space direction="vertical" size="small">
            <Text>
                <ArrowDownOutlined style={{ color: '#1890ff' }} /> {formatBytes(record.data_downloaded_mb * 1024 * 1024)}
            </Text>
            <Text>
                <ArrowUpOutlined style={{ color: '#52c41a' }} /> {formatBytes(record.data_uploaded_mb * 1024 * 1024)}
            </Text>
        </Space>
      ),
    },
    {
      title: 'Session Time',
      dataIndex: 'session_time',
      key: 'session_time',
      render: (seconds) => (
        <Tooltip title={`${Math.round(seconds)} seconds`}>
          <Tag color="blue" icon={<ClockCircleOutlined />}>
            {formatDuration(seconds)}
          </Tag>
        </Tooltip>
      ),
    },
    {
        title: 'Started',
        dataIndex: 'session_start_time',
        key: 'session_start_time',
        render: (text) => (
            <Tooltip title={moment(text).format('YYYY-MM-DD HH:mm:ss')}>
                {moment(text).fromNow()}
            </Tooltip>
        ),
    },
    {
        title: 'Service',
        dataIndex: 'service_description',
        key: 'service_description',
    }
  ];

  return (
    <>
      {error && <Alert message="Error" description={error} type="error" showIcon style={{ marginBottom: 16 }} />}
      <Table
        columns={columns}
        dataSource={users}
        rowKey={(record) => `${record.customer_id}-${record.login}`}
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        title={() => <Text>Real-time view of active user sessions on the network. Refreshes automatically.</Text>}
      />
    </>
  );
};

export default OnlineUsers;