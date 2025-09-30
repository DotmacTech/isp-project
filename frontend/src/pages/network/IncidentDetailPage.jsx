import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Layout, Card, Button, Alert, Tag, Select, Space, Typography, Descriptions, List } from 'antd';
import apiClient from '../../services/apiClient';
import IncidentTimeline from '../../components/network/IncidentTimeline';
import AddIncidentUpdateForm from '../../components/network/AddIncidentUpdateForm';

const { Content } = Layout;
const { Title, Text } = Typography;
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
      fetchIncidentData(); // Refresh data after adding an update
    } catch (err) {
      setError(`Failed to add update: ${err.message}`);
    }
  };

  const handleStatusChange = async (value) => {
    try {
      await apiClient.put(`/v1/network/incidents/${incidentId}`, { status: value });
      fetchIncidentData(); // Refresh data
    } catch (err) {
      setError(`Failed to update status: ${err.message}`);
    }
  };

  const formatDate = (dateString) => {
    return dateString ? new Date(dateString).toLocaleString() : 'N/A';
  };

  if (loading) return <p>Loading incident details...</p>;
  if (error && !incident) return <Alert message={`Error: ${error}`} type="error" showIcon />;

  return (
    <Content style={{ padding: '20px' }}>
      <Card style={{ marginBottom: '20px' }}>
        <Space style={{ width: '100%', justifyContent: 'space-between', alignItems: 'center' }}>
          <Link to="/dashboard/network/incidents">
            <Button type="link">&larr; Back to Incidents</Button>
          </Link>
          <Title level={2} style={{ margin: 0 }}>Incident: {incident.incident_number}</Title>
          <Space>
            <Text strong>Change Status:</Text>
            <Select value={incident.status} style={{ width: 150 }} onChange={handleStatusChange}>
              {STATUS_LEVELS.map(s => <Option key={s} value={s}>{s}</Option>)}
            </Select>
          </Space>
        </Space>
      </Card>
      
      {error && <Alert message={`Error: ${error}`} type="error" showIcon style={{ marginBottom: '20px' }} />}

      <Card title="Incident Details" style={{ marginBottom: '20px' }}>
        <Descriptions bordered column={{ xxl: 4, xl: 3, lg: 3, md: 3, sm: 2, xs: 1 }}>
          <Descriptions.Item label="Title" span={3}>{incident.title}</Descriptions.Item>
          <Descriptions.Item label="Description" span={3}>{incident.description}</Descriptions.Item>
          <Descriptions.Item label="Severity">
            <Tag color={incident.severity === 'high' ? 'red' : incident.severity === 'medium' ? 'orange' : 'green'}>
              {incident.severity?.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={incident.status === 'open' ? 'red' : incident.status === 'resolved' ? 'green' : 'blue'}>
              {incident.status?.toUpperCase()}
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

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card title="Affected Devices">
          <List
            bordered
            dataSource={incident.affected_devices || []}
            renderItem={item => <List.Item>Device ID: {item}</List.Item>}
            locale={{ emptyText: "No affected devices" }}
          />
        </Card>
        <Card title="Affected Services">
          <List
            bordered
            dataSource={incident.affected_services || []}
            renderItem={item => <List.Item>{item}</List.Item>}
            locale={{ emptyText: "No affected services" }}
          />
        </Card>
      </Space>

      <Card title="Incident History" style={{ marginTop: '20px' }}>
        <IncidentTimeline updates={updates} />
      </Card>

      <Card title="Add an Update" style={{ marginTop: '20px' }}>
        <AddIncidentUpdateForm onAddUpdate={handleAddUpdate} />
      </Card>
    </Content>
  );
};

export default IncidentDetailPage;
