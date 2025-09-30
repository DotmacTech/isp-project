import React, { useState, useEffect, useCallback } from 'react';
import {
  Table, message, Button, Modal, Form, Input, Typography, Space, Popconfirm, Card, InputNumber, Select
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, NodeIndexOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Option } = Select;

const IPv6NetworksPage = () => {
  const [networks, setNetworks] = useState([]);
  const [locations, setLocations] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingNetwork, setEditingNetwork] = useState(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [networksRes, locationsRes, categoriesRes] = await Promise.all([
        apiClient.get('/v1/network/ipam/ipv6/'),
        apiClient.get('/v1/locations/'),
        apiClient.get('/v1/network/ipam/categories/')
      ]);
      setNetworks(networksRes.data);
      setLocations(locationsRes.data.items || []);
      setCategories(categoriesRes.data);
    } catch (error) {
      message.error('Failed to fetch data.');
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdd = () => {
    setEditingNetwork(null);
    form.resetFields();
    form.setFieldsValue({ network_type: 'endnet', type_of_usage: 'static' });
    setIsModalVisible(true);
  };

  const handleEdit = (network) => {
    setEditingNetwork(network);
    form.setFieldsValue(network);
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/v1/network/ipam/ipv6/${id}`);
      message.success('IPv6 Network deleted successfully');
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete IPv6 Network.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormFinish = async (values) => {
    const url = editingNetwork
      ? `/v1/network/ipam/ipv6/${editingNetwork.id}`
      : '/v1/network/ipam/ipv6/';
    const method = editingNetwork ? 'put' : 'post';

    try {
      await apiClient({ method, url, data: values });
      message.success(`IPv6 Network ${editingNetwork ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save IPv6 Network.');
    }
  };

  const columns = [
    { title: 'Network', dataIndex: 'network', key: 'network', render: (text, record) => `${record.network}/${record.prefix}` },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Usage Type', dataIndex: 'type_of_usage', key: 'type_of_usage' },
    { title: 'Comment', dataIndex: 'comment', key: 'comment' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)}>
            <Button icon={<DeleteOutlined />} danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}><NodeIndexOutlined /> IPv6 Networks</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          Add IPv6 Network
        </Button>
      </div>
      <Table dataSource={networks} columns={columns} rowKey="id" loading={loading} />
      <Modal title={editingNetwork ? 'Edit IPv6 Network' : 'Add IPv6 Network'} open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="network" label="Network Address" rules={[{ required: true }]}><Input placeholder="e.g., 2001:db8::" /></Form.Item>
          <Form.Item name="prefix" label="Prefix" rules={[{ required: true }]}><InputNumber min={0} max={128} style={{ width: '100%' }} placeholder="e.g., 48" /></Form.Item>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input placeholder="e.g., Customer Prefix Pool A" /></Form.Item>
          <Form.Item name="comment" label="Comment"><Input.TextArea rows={2} placeholder="Optional comment" /></Form.Item>
          <Form.Item name="location_id" label="Location" rules={[{ required: true }]}>
            <Select placeholder="Select a location" showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>{locations.map(loc => <Option key={loc.id} value={loc.id}>{loc.name}</Option>)}</Select>
          </Form.Item>
          <Form.Item name="network_category" label="Category" rules={[{ required: true }]}>
            <Select placeholder="Select a category">{categories.map(cat => <Option key={cat.id} value={cat.id}>{cat.name}</Option>)}</Select>
          </Form.Item>
          <Form.Item name="network_type" label="Network Type" rules={[{ required: true }]}><Select><Option value="endnet">Endnet</Option><Option value="rootnet">Rootnet</Option></Select></Form.Item>
          <Form.Item name="type_of_usage" label="Type of Usage" rules={[{ required: true }]}><Select><Option value="static">Static</Option><Option value="management">Management</Option></Select></Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editingNetwork ? 'Save Changes' : 'Create Network'}</Button></Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default IPv6NetworksPage;