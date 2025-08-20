import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Spin, Typography, Tag, Button, Modal, Form, Input, Select } from 'antd';
import axios from 'axios';

const { Title } = Typography;

function ServicesPage() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [tariffs, setTariffs] = useState([]);
  const [form] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      message.error('Authentication required.');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get('/api/v1/services/internet/', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setServices(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch services.');
      console.error('Error fetching services:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });
    
    const fetchDropdownData = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      try {
        const [customersRes, tariffsRes] = await Promise.all([
          axios.get('/api/v1/customers/', { headers: { Authorization: `Bearer ${token}` }, params: { limit: 1000 } }),
          axios.get('/api/v1/tariffs/internet/', { headers: { Authorization: `Bearer ${token}` }, params: { limit: 1000 } })
        ]);
        setCustomers(customersRes.data.items);
        setTariffs(tariffsRes.data.items);
      } catch (error) {
        message.error('Failed to fetch customers or tariffs for dropdowns.');
      }
    };
    fetchDropdownData();
  }, [fetchData, pagination.current, pagination.pageSize]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const handleAdd = () => {
    setEditingService(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (service) => {
    setEditingService(service);
    form.setFieldsValue({
      ...service,
      customer_id: service.customer.id,
      tariff_id: service.tariff.id,
    });
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingService(null);
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');

    try {
      if (editingService) {
        await axios.put(`/api/v1/services/internet/${editingService.id}`, values, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        await axios.post('/api/v1/services/internet/', values, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      message.success(`Service ${editingService ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to ${editingService ? 'update' : 'create'} service.`);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Customer', dataIndex: ['customer', 'name'], key: 'customer' },
    { title: 'Description', dataIndex: 'description', key: 'description' },
    { title: 'Tariff', dataIndex: ['tariff', 'title'], key: 'tariff' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const color = status === 'active' ? 'green' : 'red';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    { title: 'Login', dataIndex: 'login', key: 'login' },
    { title: 'IP Address', dataIndex: 'ipv4', key: 'ipv4' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => <Button size="small" onClick={() => handleEdit(record)}>Edit</Button>,
    },
  ];

  return (
    <div>
      <Title level={2}>Internet Services</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Add Service</Button>
      <Table
        dataSource={services}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
      <Modal
        title={editingService ? 'Edit Service' : 'Add Service'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
            <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
              {customers.map(c => <Select.Option key={c.id} value={c.id}>{c.name} (ID: {c.id})</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="tariff_id" label="Tariff" rules={[{ required: true }]}>
            <Select>
              {tariffs.map(t => <Select.Option key={t.id} value={t.id}>{t.title}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="description" label="Description" rules={[{ required: true }]}>
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="login" label="Login" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password">
            <Input.Password />
          </Form.Item>
          <Form.Item name="ipv4" label="Static IP"><Input /></Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Service</Button>
        </Form>
      </Modal>
    </div>
  );
}

export default ServicesPage;