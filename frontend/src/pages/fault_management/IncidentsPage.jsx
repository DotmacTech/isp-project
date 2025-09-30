import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Table, Alert, Spin, Typography, Tag, Button } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';

const { Title } = Typography;

const IncidentsPage = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchIncidents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/v1/network/incidents/');
      setIncidents(response.data.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  const columns = [
    {
      title: 'Incident Number',
      dataIndex: 'incident_number',
      key: 'incident_number',
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: status => {
        let color = 'geekblue';
        if (status === 'resolved') {
          color = 'green';
        } else if (status === 'acknowledged') {
          color = 'orange';
        }
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: severity => {
        let color = 'blue';
        if (severity === 'critical') {
          color = 'red';
        } else if (severity === 'high') {
          color = 'orange';
        } else if (severity === 'medium') {
          color = 'yellow';
        }
        return <Tag color={color}>{severity.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: text => new Date(text).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Link to={`/dashboard/network/incidents/${record.id}`}>
          <Button icon={<EyeOutlined />}>View</Button>
        </Link>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>Incidents</Title>
      {error && <Alert message={`Error: ${error}`} type="error" showIcon style={{ marginBottom: 16 }} />}
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={incidents}
          rowKey="id"
        />
      </Spin>
    </div>
  );
};

export default IncidentsPage;