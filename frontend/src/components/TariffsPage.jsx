import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Spin, Typography, Button, Modal, Form, Input, InputNumber, Popconfirm } from 'antd';
import axios from 'axios';

const { Title } = Typography;

function TariffsPage() {
  const [tariffs, setTariffs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingTariff, setEditingTariff] = useState(null);
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
      const response = await axios.get('/api/v1/tariffs/internet/', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setTariffs(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch tariffs.');
      console.error('Error fetching tariffs:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });
  }, [fetchData, pagination.current, pagination.pageSize]);

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const handleAdd = () => {
    setEditingTariff(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (tariff) => {
    setEditingTariff(tariff);
    form.setFieldsValue(tariff);
    setIsModalVisible(true);
  };

  const handleDelete = async (tariffId) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.delete(`/api/v1/tariffs/internet/${tariffId}`, { headers: { Authorization: `Bearer ${token}` } });
      message.success('Tariff deleted successfully');
      setTariffs(currentTariffs => currentTariffs.filter(tariff => tariff.id !== tariffId));
    } catch (error) {
      message.error('Failed to delete tariff.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingTariff(null);
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');

    try {
      if (editingTariff) {
        await axios.put(`/api/v1/tariffs/internet/${editingTariff.id}`, values, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        await axios.post('/api/v1/tariffs/internet/', values, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      message.success(`Tariff ${editingTariff ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      const errorMsg = error.response?.data?.detail || `Failed to ${editingTariff ? 'update' : 'create'} tariff.`;
      message.error(errorMsg);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price) => `$${Number(price).toFixed(2)}`,
    },
    { title: 'Download Speed (Kbps)', dataIndex: 'speed_download', key: 'speed_download' },
    { title: 'Upload Speed (Kbps)', dataIndex: 'speed_upload', key: 'speed_upload' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <span>
          <Button size="small" onClick={() => handleEdit(record)} style={{ marginRight: 8 }}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Internet Tariffs</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Add Tariff</Button>
      <Table
        dataSource={tariffs}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
      <Modal
        title={editingTariff ? 'Edit Tariff' : 'Add Tariff'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="price" label="Price" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} step="0.01" />
          </Form.Item>
          <Form.Item name="speed_download" label="Download Speed (Kbps)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Form.Item name="speed_upload" label="Upload Speed (Kbps)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save</Button>
        </Form>
      </Modal>
    </div>
  );
}

export default TariffsPage;