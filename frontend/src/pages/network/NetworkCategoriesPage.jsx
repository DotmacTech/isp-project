import React, { useState, useEffect, useCallback } from 'react';
import {
  Table, message, Button, Modal, Form, Input, Typography, Space, Popconfirm, Card
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, TagsOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';

const { Title } = Typography;

const NetworkCategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/v1/network/ipam/categories/');
      setCategories(response.data);
    } catch (error) {
      message.error('Failed to fetch network categories.');
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdd = () => {
    setEditingCategory(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (category) => {
    setEditingCategory(category);
    form.setFieldsValue(category);
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/v1/network/ipam/categories/${id}`);
      message.success('Network category deleted successfully');
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete network category.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormFinish = async (values) => {
    const url = editingCategory
      ? `/v1/network/ipam/categories/${editingCategory.id}`
      : '/v1/network/ipam/categories/';
    const method = editingCategory ? 'put' : 'post';

    try {
      await apiClient({ method, url, data: values });
      message.success(`Network category ${editingCategory ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save network category.');
    }
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
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
        <Title level={2} style={{ margin: 0 }}><TagsOutlined /> Network Categories</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>Add Category</Button>
      </div>
      <Table dataSource={categories} columns={columns} rowKey="id" loading={loading} />
      <Modal title={editingCategory ? 'Edit Network Category' : 'Add Network Category'} open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="name" label="Category Name" rules={[{ required: true }]}><Input placeholder="e.g., Customer Networks" /></Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editingCategory ? 'Save Changes' : 'Create Category'}</Button></Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default NetworkCategoriesPage;