import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Typography, Tag, Input, DatePicker, Space } from 'antd';
import { getAccountingLogs } from '../../services/freeRadiusApi';
import moment from 'moment';

const { Text } = Typography;
const { Search } = Input;
const { RangePicker } = DatePicker;

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDuration = (seconds) => {
  if (!seconds || seconds < 0) return '0s';
  const d = Math.floor(seconds / (3600 * 24));
  const h = Math.floor(seconds % (3600 * 24) / 3600);
  const m = Math.floor(seconds % 3600 / 60);
  const s = Math.floor(seconds % 60);

  let result = '';
  if (d > 0) result += `${d}d `;
  if (h > 0) result += `${h}h `;
  if (m > 0) result += `${m}m `;
  if (s > 0 || result === '') result += `${s}s`;
  return result.trim();
};

const AccountingLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [filters, setFilters] = useState({ username: null, dateRange: null });

  const fetchLogs = useCallback(() => {
    setLoading(true);
    const params = {
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      username: filters.username || undefined,
      start_date: filters.dateRange ? filters.dateRange[0].toISOString() : undefined,
      end_date: filters.dateRange ? filters.dateRange[1].toISOString() : undefined,
    };

    getAccountingLogs(params)
      .then((response) => {
        setLogs(response.data.items);
        setPagination((p) => ({ ...p, total: response.data.total }));
      })
      .catch((error) => {
        message.error('Failed to fetch accounting logs.');
        console.error(error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [pagination.current, pagination.pageSize, filters]);

  useEffect(() => {
    fetchLogs(); // Fetch data on component mount and when dependencies change
    const intervalId = setInterval(fetchLogs, 60000); // Set up polling every 60 seconds

    return () => clearInterval(intervalId); // Clean up interval on unmount or when dependencies change
  }, [fetchLogs]);

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    // Reset to page 1 when filters change
    setPagination(p => ({ ...p, current: 1 }));
  };

  const handleTableChange = (newPagination) => {
    setPagination(p => ({ ...p, current: newPagination.current, pageSize: newPagination.pageSize }));
  };
  
  const handleSearch = (username) => {
    handleFilterChange('username', username);
  };

  const handleDateChange = (dates) => {
    handleFilterChange('dateRange', dates);
  };

  const columns = [
    { title: 'Username', dataIndex: 'username', key: 'username', render: (text) => <Text strong>{text}</Text> },
    { title: 'IP Address', dataIndex: 'framedipaddress', key: 'ip' },
    { title: 'Start Time', dataIndex: 'acctstarttime', key: 'start_time', render: (time) => time ? moment(time).format('YYYY-MM-DD HH:mm:ss') : '-', sorter: true },
    { title: 'Stop Time', dataIndex: 'acctstoptime', key: 'stop_time', render: (time) => time ? moment(time).format('YYYY-MM-DD HH:mm:ss') : '-' },
    { title: 'Duration', dataIndex: 'acctsessiontime', key: 'duration', render: (seconds) => formatDuration(seconds) },
    { title: 'Downloaded', dataIndex: 'acctinputoctets', key: 'download', render: (bytes) => formatBytes(bytes) },
    { title: 'Uploaded', dataIndex: 'acctoutputoctets', key: 'upload', render: (bytes) => formatBytes(bytes) },
    { title: 'Terminate Cause', dataIndex: 'acctterminatecause', key: 'terminate_cause', render: (cause) => <Tag>{cause || 'Unknown'}</Tag> },
    { title: 'NAS IP', dataIndex: 'nasipaddress', key: 'nas_ip' },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Search
          placeholder="Filter by username"
          onSearch={handleSearch}
          style={{ width: 200 }}
          allowClear
        />
        <RangePicker onChange={handleDateChange} />
      </Space>
      <Table
        columns={columns}
        dataSource={logs}
        rowKey="radacctid"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        scroll={{ x: true }}
        title={() => <Text>Historical RADIUS accounting records.</Text>}
      />
    </div>
  );
};

export default AccountingLogs;