import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  message,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Popconfirm,
  Space,
  Typography,
  Tabs,
  Tag,
  Row,
  Col,
} from 'antd';
import axios from 'axios';

const { Title } = Typography;
const { TabPane } = Tabs;

const API_BASE_URL = '/api/v1/support/config';

function TicketConfigPage() {
  const [loading, setLoading] = useState(true);
  const [statuses, setStatuses] = useState([]);
  const [types, setTypes] = useState([]);
  const [groups, setGroups] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [modalType, setModalType] = useState(null); // 'status', 'type', or 'group'
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      message.error('Authentication required.');
      setLoading(false);
      return;
    }
    try {
      const [statusesRes, typesRes, groupsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/statuses/`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_BASE_URL}/types/`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_BASE_URL}/groups/`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      setStatuses(statusesRes.data);
      setTypes(typesRes.data);
      setGroups(groupsRes.data);
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to fetch support configuration.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdd = (type) => {
    setEditingRecord(null);
    setModalType(type);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (record, type) => {
    setEditingRecord(record);
    setModalType(type);
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  const handleDelete = async (id, type) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.delete(`${API_BASE_URL}/${type}s/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      message.success(`${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully.`);
      fetchData(); // Refresh data
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to delete ${type}.`);
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingRecord(null);
    setModalType(null);
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');
    const method = editingRecord ? 'put' : 'post';
    const url = editingRecord
      ? `${API_BASE_URL}/${modalType}s/${editingRecord.id}`
      : `${API_BASE_URL}/${modalType}s/`;

    try {
      await axiosmethod;
      message.success(`${modalType.charAt(0).toUpperCase() + modalType.slice(1)} ${editingRecord ? 'updated' : 'created'} successfully.`);
      handleModalCancel();
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to save ${modalType}.`);
    }
  };

  const renderModalContent = () => {
    if (!modalType) return null;

    switch (modalType) {
      case 'status':
        return (
          <>
            <Form.Item name="title_for_agent" label="Title for Agent" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="title_for_customer" label="Title for Customer" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="label" label="Label Color" help="e.g., default, primary, success, warning, error">
              <Input />
            </Form.Item>
            <Form.Item name="mark" label="Marks (Tags)" help="e.g., open, unresolved, closed">
              <Select mode="tags" placeholder="Type and press enter" />
            </Form.Item>
          </>
        );
      case 'type':
        return (
          <>
            <Form.Item name="title" label="Title" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="background_color" label="Background Color" help="e.g., #ff0000 or red">
              <Input />
            </Form.Item>
          </>
        );
      case 'group':
        return (
          <>
            <Form.Item name="title" label="Title" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="description" label="Description">
              <Input.TextArea />
            </Form.Item>
          </>
        );
      default:
        return null;
    }
  };

  const statusColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title for Agent', dataIndex: 'title_for_agent', key: 'title_for_agent' },
    { title: 'Title for Customer', dataIndex: 'title_for_customer', key: 'title_for_customer' },
    { title: 'Label', dataIndex: 'label', key: 'label', render: (label) => <Tag color={label}>{label}</Tag> },
    { title: 'Marks', dataIndex: 'mark', key: 'mark', render: (marks) => (marks || []).map(m => <Tag key={m}>{m}</Tag>) },
    {
      title: 'Actions', key: 'actions', render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record, 'status')}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id, 'status')}><Button size="small" danger>Delete</Button></Popconfirm>
        </Space>
      ),
    },
  ];

  const typeColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Color', dataIndex: 'background_color', key: 'background_color', render: (color) => <Tag color={color}>{color}</Tag> },
    {
      title: 'Actions', key: 'actions', render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record, 'type')}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id, 'type')}><Button size="small" danger>Delete</Button></Popconfirm>
        </Space>
      ),
    },
  ];

  const groupColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Description', dataIndex: 'description', key: 'description' },
    {
      title: 'Actions', key: 'actions', render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record, 'group')}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id, 'group')}><Button size="small" danger>Delete</Button></Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Support System Configuration</Title>
      <Tabs defaultActiveKey="1">
        <TabPane tab="Statuses" key="1">
          <Row justify="end" style={{ marginBottom: 16 }}><Col><Button type="primary" onClick={() => handleAdd('status')}>Add Status</Button></Col></Row>
          <Table dataSource={statuses} columns={statusColumns} rowKey="id" loading={loading} />
        </TabPane>
        <TabPane tab="Types" key="2">
          <Row justify="end" style={{ marginBottom: 16 }}><Col><Button type="primary" onClick={() => handleAdd('type')}>Add Type</Button></Col></Row>
          <Table dataSource={types} columns={typeColumns} rowKey="id" loading={loading} />
        </TabPane>
        <TabPane tab="Groups" key="3">
          <Row justify="end" style={{ marginBottom: 16 }}><Col><Button type="primary" onClick={() => handleAdd('group')}>Add Group</Button></Col></Row>
          <Table dataSource={groups} columns={groupColumns} rowKey="id" loading={loading} />
        </TabPane>
      </Tabs>

      <Modal
        title={`${editingRecord ? 'Edit' : 'Add'} ${modalType ? modalType.charAt(0).toUpperCase() + modalType.slice(1) : ''}`}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={[<Button key="back" onClick={handleModalCancel}>Cancel</Button>, <Button key="submit" type="primary" onClick={() => form.submit()}>Save</Button>]}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>{renderModalContent()}</Form>
      </Modal>
    </div>
  );
}

export default TicketConfigPage;