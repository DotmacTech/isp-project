import React, { useState, useEffect, useCallback } from 'react';
import { Layout, Typography, Button, Table, Space, Alert, Spin, Select, Tag, Form, Card, Empty, message } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Content } = Layout;
const { Option } = Select;

const MonitoringDataPage = () => {
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [monitoringData, setMonitoringData] = useState([]);
  
  const [loadingProfiles, setLoadingProfiles] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [error, setError] = useState(null);

  // Fetch SNMP profiles for the dropdown
  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        setLoadingProfiles(true);
        const response = await apiClient.get('/v1/network/snmp-profiles/', { params: { limit: 1000 } });
        const data = response.data;
        setProfiles(data.items || []);
        if (data.items && data.items.length > 0) {
          setSelectedProfile(data.items[0].id);
        }
      } catch (err) {
        message.error('Failed to load SNMP profiles.');
        setError(err.message);
      } finally {
        setLoadingProfiles(false);
      }
    };
    fetchProfiles();
  }, []);

  // Fetch monitoring data when a profile is selected
  const fetchMonitoringData = useCallback(async () => {
    if (!selectedProfile) return;

    try {
      setLoadingData(true);
      setError(null);
      const response = await apiClient.get(`/v1/network/snmp-data/${selectedProfile}`);
      const data = response.data;
      setMonitoringData(data.items || []);
    } catch (err) {
      message.error('Failed to fetch monitoring data.');
      setError(err.message);
      setMonitoringData([]); // Clear data on error
    } finally {
      setLoadingData(false);
    }
  }, [selectedProfile]);

  useEffect(() => {
    fetchMonitoringData();
  }, [fetchMonitoringData]);

  const handleExportCSV = () => {
    if (monitoringData.length === 0) {
      message.info('No data to export.');
      return;
    }

    const headers = ['Timestamp', 'OID', 'Value', 'Type', 'Status'];
    const rows = monitoringData.map(row => 
      [
        `"${new Date(row.timestamp).toLocaleString()}"`,
        `"${row.oid}"`,
        `"${row.value}"`,
        `"${row.value_type}"`,
        `"${row.collection_status}"` // Use collection_status as per model
      ].join(',')
    );

    const csvContent = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `monitoring_data_profile_${selectedProfile}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatDate = (dateString) => {
    return dateString ? new Date(dateString).toLocaleString() : 'N/A';
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text) => formatDate(text),
    },
    {
      title: 'OID',
      dataIndex: 'oid',
      key: 'oid',
      render: (text) => <Text code>{text}</Text>, // Use Ant Design Typography.Text code
    },
    {
      title: 'Value',
      dataIndex: 'value_numeric',
      key: 'value_numeric',
      render: (text, record) => record.value_numeric || record.value_text || record.value_boolean,
    },
    {
      title: 'Type',
      dataIndex: 'metric_type',
      key: 'metric_type',
    },
    {
      title: 'Status',
      dataIndex: 'collection_status',
      key: 'collection_status',
      render: (status) => {
        let color;
        if (status === 'success') {
          color = 'green';
        } else if (status === 'timeout') {
          color = 'orange';
        } else if (status === 'error') {
          color = 'red';
        } else {
          color = 'default';
        }
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
  ];

  return (
    <Content className="p-6">
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: '16px' }}>
        <Title level={2} style={{ margin: 0 }}>Monitoring Data</Title>
        <Button 
          type="primary" 
          icon={<DownloadOutlined />}
          onClick={handleExportCSV} 
          disabled={monitoringData.length === 0 || loadingData}
        >
          Export to CSV
        </Button>
      </Space>

      <Card className="mb-6">
        <Form layout="inline">
          <Form.Item label="SNMP Profile">
            <Select 
              value={selectedProfile} 
              style={{ width: 250 }} 
              onChange={setSelectedProfile}
              loading={loadingProfiles}
              placeholder="Select a profile"
            >
              {loadingProfiles ? (
                <Option value="" disabled>Loading profiles...</Option>
              ) : (
                profiles.map(p => (
                  <Option key={p.id} value={p.id}>
                    Profile #{p.id} (Device ID: {p.device_id})
                  </Option>
                ))
              )}
            </Select>
          </Form.Item>
        </Form>
      </Card>

      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} className="mb-6" />}

      <Table
        columns={columns}
        dataSource={monitoringData}
        loading={loadingData}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        locale={{ emptyText: <Empty description="No monitoring data found for the selected profile." /> }}
      />
    </Content>
  );
};

export default MonitoringDataPage;
