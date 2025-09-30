import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Layout, Typography, Button, Table, Space, Alert, Spin, Select, Tag, Form } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Content } = Layout;
const { Option } = Select;

const SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical'];
const STATUS_LEVELS = ['open', 'investigating', 'resolved', 'closed'];

const FaultManagementPage = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
  });

  const fetchIncidents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        limit: 100,
        ...filters,
      };
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (!params[key]) {
          delete params[key];
        }
      });

      const response = await apiClient.get('/v1/network/incidents/', { params });
      const data = response.data;
      setIncidents(data.items || []);
    } catch (err) {
      message.error('Failed to fetch incidents.');
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  const handleFilterChange = (name, value) => {
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const columns = [
    {
      title: 'Incident #',
      dataIndex: 'incident_number',
      key: 'incident_number',
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity) => {
        let color;
        if (severity === 'critical' || severity === 'high') {
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
        if (status === 'open' || status === 'investigating') {
          color = 'blue';
        } else if (status === 'resolved') {
          color = 'green';
        } else {
          color = 'default'; // closed
        }
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => formatDate(text),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (text, record) => (
        <Link to={`/dashboard/network/incidents/${record.id}`}>
          <Button type="primary" icon={<EyeOutlined />}>
            View Details
          </Button>
        </Link>
      ),
    },
  ];

  return (
    <Content className="p-6">
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: '16px' }}>
        <Title level={2} style={{ margin: 0 }}>Fault & Incident Management</Title>
      </Space>

      <Card className="mb-6">
        <Form layout="inline">
          <Form.Item label="Status">
            <Select value={filters.status} style={{ width: 150 }} onChange={(value) => handleFilterChange('status', value)}>
              <Option value="">All</Option>
              {STATUS_LEVELS.map(s => <Option key={s} value={s}>{s}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item label="Severity">
            <Select value={filters.severity} style={{ width: 150 }} onChange={(value) => handleFilterChange('severity', value)}>
              <Option value="">All</Option>
              {SEVERITY_LEVELS.map(s => <Option key={s} value={s}>{s}</Option>)}
            </Select>
          </Form.Item>
        </Form>
      </Card>

      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} className="mb-6" />}

      {loading ? (
        <Spin tip="Loading incidents...">
          <div style={{ height: '200px' }} />
        </Spin>
      ) : (
        <Table
          columns={columns}
          dataSource={incidents}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      )}
    </Content>
  );
};

export default FaultManagementPage;