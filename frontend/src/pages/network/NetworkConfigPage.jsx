import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Typography, Space, Popconfirm, Tabs } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;
const { TabPane } = Tabs;

const LookupTable = ({ title, endpoint }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/v1/network/monitoring/${endpoint}/`);
      setData(response.data);
    } catch (error) {
      message.error(`Failed to fetch ${title}.`);
    } finally {
      setLoading(false);
    }
  }, [title, endpoint]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    form.setFieldsValue(item);
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/v1/network/monitoring/config/${endpoint}/${id}`);
      message.success(`${title.slice(0, -1)} deleted successfully.`);
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to delete ${title.slice(0, -1)}.`);
    }
  };

 const handleFormFinish = async (values) => {
  const method = editingItem ? 'put' : 'post';
  const url = editingItem
    ? `/v1/network/monitoring/config/${endpoint}/${editingItem.id}`
    : `/v1/network/monitoring/config/${endpoint}/`;

  try {
    await apiClient({
      method,
      url,
      data: values,
    });

    message.success(`${title.slice(0, -1)} ${editingItem ? 'updated' : 'created'} successfully.`);
    form.resetFields();          // ✅ clear form after save
    setIsModalVisible(false);    // ✅ close modal
    fetchData();                 // ✅ refresh table
  } catch (error) {
    message.error(
      error.response?.data?.detail ||
      `Failed to save ${title.slice(0, -1)}.`
    );
  }
};

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>
        Add {title.slice(0, -1)}
      </Button>
      <Table dataSource={data} columns={columns} rowKey="id" loading={loading} />
      <Modal title={`${editingItem ? 'Edit' : 'Add'} ${title.slice(0, -1)}`} open={isModalVisible} onCancel={() => setIsModalVisible(false)} footer={null} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save</Button>
        </Form>
      </Modal>
    </div>
  );
};

function NetworkConfigPage() {
  return (
    <div>
      <Title level={2}>Network Monitoring Configuration</Title>
      <Tabs defaultActiveKey="1">
        <TabPane tab="Device Producers" key="1"><LookupTable title="Producers" endpoint="producers" /></TabPane>
        <TabPane tab="Device Types" key="2"><LookupTable title="Types" endpoint="types" /></TabPane>
        <TabPane tab="Monitoring Groups" key="3"><LookupTable title="Groups" endpoint="groups" /></TabPane>
      </Tabs>
    </div>
  );
}

export default NetworkConfigPage;