import React, { useState, useEffect, useCallback } from 'react';
import { Table, Tag, Tooltip, Typography, Alert, Card, Space } from 'antd';
import { WifiOutlined, ClockCircleOutlined, ArrowUpOutlined, ArrowDownOutlined, UserOutlined, HddOutlined } from '@ant-design/icons';
import { formatDistanceToNow, parseISO } from 'date-fns';
import apiClient from '../../services/api';

const { Title, Text } = Typography;

const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

const formatDuration = (seconds) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const days = Math.floor(seconds / (3600 * 24));
    seconds %= 3600 * 24;
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    
    let durationStr = '';
    if (days > 0) durationStr += `${days}d `;
    if (hours > 0) durationStr += `${hours}h `;
    if (minutes > 0) durationStr += `${minutes}m`;
    
    return durationStr.trim();
};

const OnlineSessionsPage = () => {
  const [data, setData] = useState([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/v1/freeradius/sessions/online/detailed/', {
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setData(response.data.items);
      setPagination({
        ...params.pagination,
        total: response.data.total,
      });
    } catch (err) {
      setError('Failed to fetch online sessions. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });
  }, [fetchData]);

  const handleTableChange = (newPagination) => {
    fetchData({ pagination: newPagination });
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
          <Text type="secondary"><HddOutlined /> {record.mac_address || 'N/A'}</Text>
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
            <Tooltip title={new Date(text).toLocaleString()}>
                {formatDistanceToNow(parseISO(text), { addSuffix: true })}
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
    <Card>
      <Title level={2}>
        <UserOutlined /> Online Customer Sessions
      </Title>
      <Text type="secondary">Real-time view of active user sessions on the network.</Text>
      
      {error && <Alert message="Error" description={error} type="error" showIcon style={{ margin: '16px 0' }} />}
      
      <Table
        columns={columns}
        rowKey={(record) => `${record.customer_id}-${record.login}`}
        dataSource={data}
        pagination={pagination}
        loading={loading}
        onChange={handleTableChange}
        style={{ marginTop: 20 }}
      />
    </Card>
  );
};

export default OnlineSessionsPage;