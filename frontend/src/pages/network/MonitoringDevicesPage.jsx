import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Typography, Tag, Space, Popconfirm, Row, Col, Checkbox, Divider, InputNumber } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Option } = Select;

function MonitoringDevicesPage() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lookupData, setLookupData] = useState({
    sites: [],
    producers: [],
    types: [],
    groups: [],
    locations: [],
    partners: [],
  });
  const [form] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);

    try {
      const response = await apiClient.get('/v1/network/monitoring/devices/', {
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setDevices(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch monitoring devices.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });
  }, [fetchData, pagination.current, pagination.pageSize]);

  useEffect(() => {
    const fetchLookups = async () => {
      try {
        const [sitesRes, producersRes, typesRes, groupsRes, locationsRes, partnersRes] = await Promise.all([
          apiClient.get('/v1/network/sites/', { params: { limit: 1000 } }),
          apiClient.get('/v1/network/monitoring/producers/'),
          apiClient.get('/v1/network/monitoring/types/'),
          apiClient.get('/v1/network/monitoring/groups/'),
          apiClient.get('/v1/locations/', { params: { limit: 1000 } }),
          apiClient.get('/v1/partners/', { params: { limit: 1000 } }),
        ]);
        setLookupData({
          sites: sitesRes.data?.items || [],
          producers: producersRes.data || [],
          types: typesRes.data || [],
          groups: groupsRes.data || [],
          locations: locationsRes.data || [],
          partners: partnersRes.data?.items || [],
        });
      } catch (error) {
        message.error('Failed to fetch configuration data for form.');
      }
    };
    fetchLookups();
  }, []);

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const handleAdd = () => {
    setEditingDevice(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (device) => {
    setEditingDevice(device);
    form.setFieldsValue({
      ...device,
      producer_id: device.producer?.id,
      type_id: device.device_type?.id,
      monitoring_group_id: device.monitoring_group?.id,
      network_site_id: device.network_site?.id,
      location_id: device.location?.id,
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (deviceId) => {
    try {
      await apiClient.delete(`/v1/network/monitoring/devices/${deviceId}`);
      message.success('Device deleted successfully');
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete device.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingDevice(null);
  };

  const handleFormFinish = async (values) => {
    setIsSubmitting(true);
    const method = editingDevice ? 'put' : 'post';
    const url = editingDevice
      ? `/v1/network/monitoring/devices/${editingDevice.id}`
      : '/v1/network/monitoring/devices/';

    try {
      await apiClient[method](url, values);
      message.success(`Device ${editingDevice ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      setEditingDevice(null);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to ${editingDevice ? 'update' : 'create'} device.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'IP Address', dataIndex: 'ip', key: 'ip' },
    { title: 'Producer', dataIndex: ['producer', 'name'], key: 'producer' },
    { title: 'Type', dataIndex: ['device_type', 'name'], key: 'type' },
    { title: 'Site', dataIndex: ['network_site', 'title'], key: 'site' },
    { title: 'Ping', dataIndex: 'ping_state', key: 'ping_state', render: state => <Tag color={state === 'up' ? 'green' : 'red'}>{state?.toUpperCase()}</Tag> },
    { title: 'SNMP', dataIndex: 'snmp_state', key: 'snmp_state', render: state => <Tag color={state === 'up' ? 'green' : 'red'}>{state?.toUpperCase()}</Tag> },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="middle">
          <Button size="small" onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure you want to delete this device?" onConfirm={() => handleDelete(record.id)} okText="Yes" cancelText="No">
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Monitoring Devices</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Add Device</Button>
      <Table dataSource={devices} columns={columns} rowKey="id" loading={loading} pagination={pagination} onChange={handleTableChange} />
      <Modal title={editingDevice ? 'Edit Monitoring Device' : 'Add Monitoring Device'} open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnHidden width={900}>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Row gutter={16}><Col span={12}><Form.Item name="title" label="Device Title" rules={[{ required: true }]}><Input placeholder="e.g., Core Router A" /></Form.Item></Col><Col span={12}><Form.Item name="ip" label="IP Address" rules={[{ required: true }]}><Input placeholder="e.g., 192.168.1.1" /></Form.Item></Col></Row>
          <Row gutter={16}><Col span={12}><Form.Item name="producer_id" label="Producer" rules={[{ required: true }]}><Select>{lookupData.producers.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select></Form.Item></Col><Col span={12}><Form.Item name="model" label="Model"><Input placeholder="e.g., CCR1036-8G-2S+" /></Form.Item></Col></Row>
          <Row gutter={16}><Col span={12}><Form.Item name="type_id" label="Device Type" rules={[{ required: true }]}><Select>{lookupData.types.map(t => <Option key={t.id} value={t.id}>{t.name}</Option>)}</Select></Form.Item></Col><Col span={12}><Form.Item name="monitoring_group_id" label="Monitoring Group" rules={[{ required: true }]}><Select>{lookupData.groups.map(g => <Option key={g.id} value={g.id}>{g.name}</Option>)}</Select></Form.Item></Col></Row>
          <Row gutter={16}><Col span={12}><Form.Item name="network_site_id" label="Network Site"><Select allowClear>{lookupData.sites.map(s => <Option key={s.id} value={s.id}>{s.title}</Option>)}</Select></Form.Item></Col><Col span={12}><Form.Item name="location_id" label="Location" rules={[{ required: true }]}><Select>{lookupData.locations.map(l => <Option key={l.id} value={l.id}>{l.name}</Option>)}</Select></Form.Item></Col></Row>
          <Form.Item name="partners_ids" label="Partners" rules={[{ required: true }]}><Select mode="multiple">{lookupData.partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select></Form.Item>
          <Divider>Monitoring Settings</Divider>
          <Row gutter={16}>
            <Col span={8}><Form.Item name="snmp_port" label="SNMP Port" initialValue={161}><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="snmp_community" label="SNMP Community" initialValue="public"><Input /></Form.Item></Col>
            <Col span={8}><Form.Item name="snmp_version" label="SNMP Version" initialValue={1}><Select><Option value={1}>v1</Option><Option value={2}>v2c</Option><Option value={3}>v3</Option></Select></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}><Form.Item name="active" label="Active" valuePropName="checked" initialValue={true}><Checkbox /></Form.Item></Col>
            <Col span={8}><Form.Item name="is_ping" label="Enable Ping" valuePropName="checked" initialValue={true}><Checkbox /></Form.Item></Col>
            <Col span={8}><Form.Item name="send_notifications" label="Send Notifications" valuePropName="checked" initialValue={true}><Checkbox /></Form.Item></Col>
          </Row>
          <Form.Item><Button type="primary" htmlType="submit" loading={isSubmitting} style={{ width: '100%' }}>{editingDevice ? 'Save Changes' : 'Create Device'}</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default MonitoringDevicesPage;
