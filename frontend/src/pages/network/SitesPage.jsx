import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Typography, Tag, Space, Popconfirm, Row, Col } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Option } = Select;

function NetworkSitesPage() {
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingSite, setEditingSite] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lookupData, setLookupData] = useState({
    locations: [],
    partners: [],
  });
  const [form] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);

    try {
      const response = await apiClient.get('/v1/network/sites/', {
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setSites(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch network sites.');
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
    setEditingSite(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (site) => {
    setEditingSite(site);
    form.setFieldsValue({
      ...site,
      location_id: site.location?.id,
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (siteId) => {
    try {
      await apiClient.delete(`/v1/network/sites/${siteId}`);
      message.success('Network site deleted successfully');
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete network site.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingSite(null);
  };

  const handleFormFinish = async (values) => {
    setIsSubmitting(true);
    const method = editingSite ? 'put' : 'post';
    const url = editingSite
      ? `/v1/network/sites/${editingSite.id}`
      : '/v1/network/sites/';

    try {
      await apiClient[method](url, values);
      message.success(`Network site ${editingSite ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      setEditingSite(null);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to ${editingSite ? 'update' : 'create'} network site.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Location', dataIndex: ['location', 'name'], key: 'location' },
    { title: 'Address', dataIndex: 'address', key: 'address' },
    { title: 'GPS', dataIndex: 'gps', key: 'gps' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="middle">
          <Button size="small" onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure you want to delete this site?" onConfirm={() => handleDelete(record.id)} okText="Yes" cancelText="No">
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Network Sites</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Add Site</Button>
      <Table dataSource={sites} columns={columns} rowKey="id" loading={loading} pagination={pagination} onChange={handleTableChange} />
      <Modal title={editingSite ? 'Edit Network Site' : 'Add Network Site'} open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnHidden width={800}>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="title" label="Site Title" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="location_id" label="Location" rules={[{ required: true }]}><Select>{lookupData.locations.map(l => <Option key={l.id} value={l.id}>{l.name}</Option>)}</Select></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}><Form.Item name="description" label="Description"><Input.TextArea /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="address" label="Address"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="gps" label="GPS Coordinates"><Input placeholder="e.g., 6.5244, 3.3792" /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}><Form.Item name="partners_ids" label="Partners" rules={[{ required: true }]}><Select mode="multiple">{lookupData.partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select></Form.Item></Col>
          </Row>
          <Form.Item><Button type="primary" htmlType="submit" loading={isSubmitting} style={{ width: '100%' }}>{editingSite ? 'Save Changes' : 'Create Site'}</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default NetworkSitesPage;