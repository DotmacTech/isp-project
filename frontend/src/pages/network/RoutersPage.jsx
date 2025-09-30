import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Typography, Tag, Space, Popconfirm, Row, Col, Checkbox, Divider, InputNumber } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Option } = Select;

function RoutersPage() {
  const [routers, setRouters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRouter, setEditingRouter] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lookupData, setLookupData] = useState({
    locations: [],
    partners: [],
    nasTypes: [], // Assuming there's a way to get these, maybe hardcoded for now
  });
  const [form] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);

    try {
      const response = await apiClient.get('/v1/network/routers/', {
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setRouters(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch routers.');
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
        const [locationsRes, partnersRes] = await Promise.all([
          apiClient.get('/v1/locations/', { params: { limit: 1000 } }),
          apiClient.get('/v1/partners/', { params: { limit: 1000 } }),
        ]);
        setLookupData({
          locations: locationsRes.data,
          partners: partnersRes.data.items,
          nasTypes: [ // Hardcoding for now as there's no endpoint for this
            { id: 1, name: 'MikroTik' },
            { id: 2, name: 'Cisco' },
          ],
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
    setEditingRouter(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (router) => {
    setEditingRouter(router);
    form.setFieldsValue({
      ...router,
      location_id: router.location?.id,
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (routerId) => {
    try {
      await apiClient.delete(`/v1/network/routers/${routerId}`);
      message.success('Router deleted successfully');
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete router.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingRouter(null);
  };

  const handleFormFinish = async (values) => {
    setIsSubmitting(true);
    const method = editingRouter ? 'put' : 'post';
    const url = editingRouter
      ? `/v1/network/routers/${editingRouter.id}`
      : '/v1/network/routers/';

    try {
      await apiClient[method](url, values);
      message.success(`Router ${editingRouter ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      setEditingRouter(null);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to ${editingRouter ? 'update' : 'create'} router.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'IP Address', dataIndex: 'ip', key: 'ip' },
    { title: 'Location', dataIndex: ['location', 'name'], key: 'location' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: state => <Tag color={state === 'online' ? 'green' : 'red'}>{state?.toUpperCase()}</Tag> },
    { title: 'Version', dataIndex: 'version', key: 'version' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="middle">
          <Button size="small" onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure you want to delete this router?" onConfirm={() => handleDelete(record.id)} okText="Yes" cancelText="No">
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Routers (NAS)</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Add Router</Button>
      <Table dataSource={routers} columns={columns} rowKey="id" loading={loading} pagination={pagination} onChange={handleTableChange} />
      <Modal title={editingRouter ? 'Edit Router' : 'Add Router'} open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnHidden width={800}>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Row gutter={16}><Col span={12}><Form.Item name="title" label="Router Title" rules={[{ required: true }]}><Input placeholder="e.g., Main POP Router" /></Form.Item></Col><Col span={12}><Form.Item name="ip" label="IP Address" rules={[{ required: true }]}><Input placeholder="e.g., 192.168.88.1" /></Form.Item></Col></Row>
          <Row gutter={16}><Col span={12}><Form.Item name="location_id" label="Location" rules={[{ required: true }]}><Select>{lookupData.locations.map(l => <Option key={l.id} value={l.id}>{l.name}</Option>)}</Select></Form.Item></Col><Col span={12}><Form.Item name="nas_type" label="NAS Type" rules={[{ required: true }]}><Select>{lookupData.nasTypes.map(t => <Option key={t.name} value={t.id}>{t.name}</Option>)}</Select></Form.Item></Col></Row>
          <Form.Item name="model" label="Model"><Input placeholder="e.g., MikroTik CCR1036" /></Form.Item>
          <Form.Item name="partners_ids" label="Partners" rules={[{ required: true }]}><Select mode="multiple">{lookupData.partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select></Form.Item>
          <Divider>RADIUS</Divider>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="radius_secret" label="RADIUS Secret"><Input.Password placeholder="Enter RADIUS secret" /></Form.Item></Col>
            <Col span={12}><Form.Item name="nas_ip" label="NAS IP Address (Optional)"><Input placeholder="Leave blank to use main IP" /></Form.Item></Col>
          </Row>
          <Divider>API</Divider>
          <Row gutter={16}><Col span={12}><Form.Item name="api_login" label="API Login"><Input /></Form.Item></Col><Col span={12}><Form.Item name="api_password" label="API Password"><Input.Password /></Form.Item></Col></Row>
          <Row gutter={16}><Col span={12}><Form.Item name="api_port" label="API Port" initialValue={8728}><InputNumber style={{ width: '100%' }} /></Form.Item></Col><Col span={12}><Form.Item name="api_enable" label="Enable API" valuePropName="checked"><Checkbox /></Form.Item></Col></Row>
          <Divider>Shaping</Divider>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="shaping_type" label="Shaping Type" initialValue="simple"><Select><Option value="simple">Simple Queues</Option><Option value="pcq">PCQ</Option><Option value="api">API</Option></Select></Form.Item></Col>
            <Col span={12}><Form.Item name="shaper" label="Enable Shaper" valuePropName="checked"><Checkbox /></Form.Item></Col>
          </Row>
          <Form.Item><Button type="primary" htmlType="submit" loading={isSubmitting} style={{ width: '100%' }}>{editingRouter ? 'Save Changes' : 'Create Router'}</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default RoutersPage;