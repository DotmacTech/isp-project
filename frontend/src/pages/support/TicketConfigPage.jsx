import React, { useState, useEffect, useCallback } from 'react';
import {
  Tabs,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Typography,
  Space,
  Popconfirm,
  message,
  Card,
  Tag,
  Switch,
  ColorPicker
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, BuildOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';

const { Title } = Typography;
const { TabPane } = Tabs;

// A generic component for managing a config type (status, type, group)
const ConfigSection = ({ title, dataSource, columns, onAdd, loading }) => (
  <Card>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
      <Title level={4} style={{ margin: 0 }}>Manage {title}</Title>
      <Button type="primary" icon={<PlusOutlined />} onClick={onAdd}>
        Add {title.slice(0, -1)}
      </Button>
    </div>
    <Table
      dataSource={dataSource}
      columns={columns}
      rowKey="id"
      loading={loading}
      pagination={{ pageSize: 10 }}
    />
  </Card>
);

const TicketConfigPage = () => {
  const [statuses, setStatuses] = useState([]);
  const [types, setTypes] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [activeTab, setActiveTab] = useState('statuses');
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statusesRes, typesRes, groupsRes] = await Promise.all([
        apiClient.get('/v1/support/statuses/'),
        apiClient.get('/v1/support/types/'),
        apiClient.get('/v1/support/groups')
      ]);
      setStatuses(statusesRes.data);
      setTypes(typesRes.data);
      setGroups(groupsRes.data);
    } catch (error) {
      message.error('Failed to fetch ticket configurations. You may not have the required permissions.');
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getEndpoint = (tab) => {
    const endpoints = {
      statuses: '/v1/support/statuses/',
      types: '/v1/support/types/',
      groups: '/v1/support/groups/',
    };
    return endpoints[tab];
  };

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
    form.setFieldsValue({ view_on_dashboard: true });
    setIsModalVisible(true);
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    const values = { ...item };
    if (item.mark && Array.isArray(item.mark)) {
      values.mark = item.mark.join(',');
    }
    form.setFieldsValue(values);
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    const endpoint = getEndpoint(activeTab);
    try {
      await apiClient.delete(`${endpoint}${id}`);
      message.success('Item deleted successfully');
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete item.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormFinish = async (values) => {
    const endpoint = getEndpoint(activeTab);
    const url = editingItem ? `${endpoint}${editingItem.id}/` : endpoint;
    const method = editingItem ? 'put' : 'post';

    let payload = { ...values };
    if (activeTab === 'statuses' && payload.mark && typeof payload.mark === 'string') {
      payload.mark = payload.mark.split(',').map(s => s.trim()).filter(Boolean);
    }

    try {
      await apiClient({ method, url, data: payload });
      message.success(`Item ${editingItem ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      fetchData();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save item.');
    }
  };

  const getColumns = (type) => {
    const baseColumns = [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
      { title: 'Title', dataIndex: type === 'statuses' ? 'title_for_agent' : 'title', key: 'title' },
    ];

    if (type === 'statuses') {
      baseColumns.push(
        { title: 'Customer Title', dataIndex: 'title_for_customer', key: 'title_for_customer' },
        { title: 'Label', dataIndex: 'label', key: 'label', render: label => <Tag>{label}</Tag> },
        { title: 'Mark', dataIndex: 'mark', key: 'mark', render: marks => (marks || []).map(m => <Tag key={m}>{m}</Tag>) }
      );
    } else if (type === 'types') {
      baseColumns.push({ title: 'Color', dataIndex: 'background_color', key: 'background_color', render: color => <Tag color={color}>{color}</Tag> });
    } else if (type === 'groups') {
      baseColumns.push({ title: 'Description', dataIndex: 'description', key: 'description' });
    }

    baseColumns.push({
      title: 'Actions',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)}>
            <Button icon={<DeleteOutlined />} danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    });

    return baseColumns;
  };

  const getFormFields = () => {
    switch (activeTab) {
      case 'statuses':
        return (
          <>
            <Form.Item name="title_for_agent" label="Title for Agent" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="title_for_customer" label="Title for Customer" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="label" label="UI Label Style"><Input placeholder="e.g., default, primary, success, warning" /></Form.Item>
            <Form.Item name="mark" label="Marks (comma-separated)" help="e.g., open,unresolved or closed"><Input /></Form.Item>
            <Form.Item name="icon" label="Icon Name"><Input placeholder="e.g., fa-tasks" /></Form.Item>
            <Form.Item name="view_on_dashboard" label="View on Dashboard" valuePropName="checked"><Switch /></Form.Item>
          </>
        );
      case 'types':
        return (
          <>
            <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="background_color" label="Background Color"><ColorPicker showText />
            </Form.Item>
          </>
        );
      case 'groups':
        return (
          <>
            <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="description" label="Description"><Input.TextArea /></Form.Item>
          </>
        );
      default:
        return null;
    }
  };

  const getModalTitle = () => {
    const action = editingItem ? 'Edit' : 'Add';
    const entity = { statuses: 'Status', types: 'Type', groups: 'Group' }[activeTab];
    return `${action} ${entity}`;
  };

  return (
    <div>
      <Title level={2}><BuildOutlined /> Ticket Configuration</Title>
      <Tabs activeKey={activeTab} onChange={setActiveTab} type="card">
        <TabPane tab="Statuses" key="statuses">
          <ConfigSection title="Statuses" dataSource={statuses} columns={getColumns('statuses')} onAdd={handleAdd} loading={loading} />
        </TabPane>
        <TabPane tab="Types" key="types">
          <ConfigSection title="Types" dataSource={types} columns={getColumns('types')} onAdd={handleAdd} loading={loading} />
        </TabPane>
        <TabPane tab="Groups" key="groups">
          <ConfigSection title="Groups" dataSource={groups} columns={getColumns('groups')} onAdd={handleAdd} loading={loading} />
        </TabPane>
      </Tabs>

      <Modal title={getModalTitle()} open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          {getFormFields()}
          <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editingItem ? 'Save Changes' : 'Create'}</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TicketConfigPage;