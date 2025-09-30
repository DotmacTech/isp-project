import React, { useState, useEffect, useCallback } from 'react';
import { Layout, Typography, Button, Table, Space, Alert, Spin, Select, Tag, message, Form, Card } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Content } = Layout;
const { Option } = Select;

const SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical'];
const STATUS_LEVELS = ['active', 'acknowledged', 'resolved'];

const AlertManagementPage = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    status: 'active', // Default to showing active alerts
    severity: '',
  });

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        limit: 100,
        ...filters,
      };
      Object.keys(params).forEach(key => {
        if (!params[key]) {
          delete params[key];
        }
      });

      const response = await apiClient.get('/v1/network/alerts/', { params });
      const data = response.data;
      setAlerts(data.items || []);
    } catch (err) {
      message.error('Failed to fetch alerts.');
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleFilterChange = (name, value) => {
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await apiClient.put(`/v1/network/alerts/${alertId}/acknowledge`);
      message.success('Alert acknowledged successfully.');
      fetchAlerts(); // Refresh the list
    } catch (err) {
      message.error(`Failed to acknowledge alert: ${err.message}`);
      setError(`Failed to acknowledge alert: ${err.message}`);
    }
  };

  const formatDate = (dateString) => {
    return dateString ? new Date(dateString).toLocaleString() : 'N/A';
  };

  const columns = [
    {
      title: 'Alert Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity) => {
        let color;
        if (severity === 'high' || severity === 'critical') {
          color = 'volcano';
        } else if (severity === 'medium') {
          color = 'orange';
        } else {
          color = 'green';
        }
        return <Tag color={color}>{severity.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        let color;
        if (status === 'active') {
          color = 'red';
        } else if (status === 'acknowledged') {
          color = 'blue';
        } else {
          color = 'green';
        }
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Last Triggered',
      dataIndex: 'last_triggered',
      key: 'last_triggered',
      render: (text) => formatDate(text),
    },
    {
      title: 'Device ID',
      dataIndex: 'target_id',
      key: 'target_id',
      render: (text) => text || 'N/A',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (text, record) => (
        <Button
          type="primary"
          icon={<CheckCircleOutlined />}
          onClick={() => handleAcknowledge(record.id)}
          disabled={record.status !== 'active'}
        >
          Acknowledge
        </Button>
      ),
    },
  ];

  return (
    <Content className="p-6">
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: '16px' }}>
        <Title level={2} style={{ margin: 0 }}>Alert Management</Title>
      </Space>

      <Card className="mb-6">
        <Form layout="inline">
          <Form.Item label="Status">
            <Select value={filters.status} style={{ width: 120 }} onChange={(value) => handleFilterChange('status', value)}>
              <Option value="">All</Option>
              {STATUS_LEVELS.map(s => <Option key={s} value={s}>{s}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item label="Severity">
            <Select value={filters.severity} style={{ width: 120 }} onChange={(value) => handleFilterChange('severity', value)}>
              <Option value="">All</Option>
              {SEVERITY_LEVELS.map(s => <Option key={s} value={s}>{s}</Option>)}
            </Select>
          </Form.Item>
        </Form>
      </Card>

      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} className="mb-6" />}

      <Table
        columns={columns}
        dataSource={alerts}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </Content>
  );
};

export default AlertManagementPage;