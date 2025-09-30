import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Layout, Typography, Button, Select, Space, Alert, Spin, Card, Descriptions, Tag, List } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';
import IncidentTimeline from './IncidentTimeline';
import AddIncidentUpdateForm from './AddIncidentUpdateForm';

const { Title, Text } = Typography;
const { Content } = Layout;
const { Option } = Select;

const STATUS_LEVELS = ['open', 'investigating', 'resolved', 'closed'];

const IncidentDetailPage = () => {
  const { incidentId } = useParams();
  const [incident, setIncident] = useState(null);
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchIncidentData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [incidentData, updatesData] = await Promise.all([
        apiClient.get(`/v1/network/incidents/${incidentId}`),
        apiClient.get(`/v1/network/incidents/${incidentId}/updates/`),
      ]);
      setIncident(incidentData.data);
      setUpdates(updatesData.data.items || []);
    } catch (err) {
      message.error('Failed to fetch incident data.');
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    fetchIncidentData();
  }, [fetchIncidentData]);

  const handleAddUpdate = async (updateContent) => {
    try {
      await apiClient.post(`/v1/network/incidents/${incidentId}/updates/`, {
        content: updateContent,
        update_type: 'comment',
        is_internal: false, // Assuming updates from UI are not internal
      });
      message.success('Update added successfully.');
      fetchIncidentData(); // Refresh data after adding an update
    } catch (err) {
      message.error(`Failed to add update: ${err.message}`);
      setError(`Failed to add update: ${err.message}`);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await apiClient.put(`/v1/network/incidents/${incidentId}`, { status: newStatus });
      message.success('Incident status updated successfully.');
      fetchIncidentData(); // Refresh data
    } catch (err) {
      message.error(`Failed to update status: ${err.message}`);
      setError(`Failed to update status: ${err.message}`);
    }
  };

  const formatDate = (dateString) => {
    return dateString ? new Date(dateString).toLocaleString() : 'N/A';
  };

  if (loading) return <Spin tip="Loading incident details..."><div style={{ height: '200px' }} /></Spin>;
  if (error && !incident) return <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} className="mb-6" />;

  return (
    <Content className="p-6">
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: '16px' }} wrap>
        <Link to="/dashboard/network/incidents" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ArrowLeftOutlined /> Back to Incidents
        </Link>
        <Title level={2} style={{ margin: 0 }}>Incident: {incident.incident_number}</Title>
        <Space>
          <Text>Change Status:</Text>
          <Select value={incident.status} onChange={handleStatusChange} style={{ width: 150 }}>
            {STATUS_LEVELS.map(s => <Option key={s} value={s}>{s}</Option>)}
          </Select>
        </Space>
      </Space>
      
      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} className="mb-6" />}

      <Card className="mb-6">
        <Descriptions bordered column={{ xs: 1, sm: 2, md: 3 }} size="small">
          <Descriptions.Item label="Title" span={3}>{incident.title}</Descriptions.Item>
          <Descriptions.Item label="Description" span={3}>{incident.description}</Descriptions.Item>
          <Descriptions.Item label="Severity">
            <Tag color={incident.severity === 'critical' || incident.severity === 'high' ? 'volcano' : incident.severity === 'medium' ? 'orange' : 'green'}>
              {incident.severity.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={incident.status === 'open' || incident.status === 'investigating' ? 'blue' : incident.status === 'resolved' ? 'green' : 'default'}>
              {incident.status.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Type">{incident.incident_type}</Descriptions.Item>
          <Descriptions.Item label="Source">{incident.source}</Descriptions.Item>
          <Descriptions.Item label="Priority">{incident.priority}</Descriptions.Item>
          <Descriptions.Item label="Customer Impact">{incident.customer_impact ? 'Yes' : 'No'}</Descriptions.Item>
          <Descriptions.Item label="Created">{formatDate(incident.created_at)}</Descriptions.Item>
          <Descriptions.Item label="Last Updated">{formatDate(incident.updated_at)}</Descriptions.Item>
          <Descriptions.Item label="Resolved">{formatDate(incident.resolved_at)}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Affected Resources" className="mb-6">
        <List
          size="small"
          header={<div>Affected Devices</div>}
          bordered
          dataSource={incident.affected_devices || []}
          renderItem={item => <List.Item>Device ID: {item}</List.Item>}
        />
        <List
          size="small"
          header={<div>Affected Services</div>}
          bordered
          dataSource={incident.affected_services || []}
          renderItem={item => <List.Item>Service: {item}</List.Item>}
          style={{ marginTop: '16px' }}
        />
      </Card>

      <Card title="Incident History" className="mb-6">
        <IncidentTimeline updates={updates} />
      </Card>

      <Card title="Add an Update" className="mb-6">
        <AddIncidentUpdateForm onAddUpdate={handleAddUpdate} />
      </Card>
    </Content>
  );
};

export default IncidentDetailPage;