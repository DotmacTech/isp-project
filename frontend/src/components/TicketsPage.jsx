import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Typography, Tag } from 'antd';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api';

const { Title } = Typography;
const { Option } = Select;

function TicketsPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [ticketConfig, setTicketConfig] = useState({ statuses: [], types: [], groups: [] });
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);

    try {
      const response = await apiClient.get('/v1/support/tickets/', {
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setTickets(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch tickets.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });

    const fetchSupportData = async () => {
      try {
        const [customersRes, statusesRes, typesRes, groupsRes] = await Promise.all([
          apiClient.get('/v1/customers/', { params: { limit: 1000 } }),
          apiClient.get('/v1/support/config/statuses/'),
          apiClient.get('/v1/support/config/types/'),
          apiClient.get('/v1/support/config/groups/'),
        ]);
        setCustomers(customersRes.data.items);
        setTicketConfig({
          statuses: statusesRes.data,
          types: typesRes.data,
          groups: groupsRes.data,
        });
      } catch (error) {
        message.error('Failed to fetch support configuration data.');
      }
    };
    fetchSupportData();
  }, [fetchData, pagination.current, pagination.pageSize]);

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const handleAdd = () => {
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleModalCancel = () => setIsModalVisible(false);

  const handleFormFinish = async (values) => {
    try {
      await apiClient.post('/v1/support/tickets/', values);
      message.success('Ticket created successfully.');
      setIsModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to create ticket.');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Subject', dataIndex: 'subject', key: 'subject' },
    { title: 'Customer', dataIndex: ['customer', 'name'], key: 'customer' },
    { title: 'Status', dataIndex: ['status', 'title_for_agent'], key: 'status', render: (text, record) => <Tag color={record.status.label}>{text}</Tag> },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', render: (p) => <Tag>{p?.toUpperCase()}</Tag> },
    { title: 'Assignee', dataIndex: ['assignee', 'user', 'full_name'], key: 'assignee' },
    { title: 'Actions', key: 'actions', render: (_, record) => <Button size="small" onClick={() => navigate(`/dashboard/support/tickets/${record.id}`)}>View</Button> },
  ];

  return (
    <div>
      <Title level={2}>Support Tickets</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Create Ticket</Button>
      <Table dataSource={tickets} columns={columns} rowKey="id" loading={loading} pagination={pagination} onChange={handleTableChange} />
      <Modal title="Create New Ticket" open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
            <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
              {customers.map(c => <Option key={c.id} value={c.id}>{c.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="subject" label="Subject" rules={[{ required: true }]}>
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="initial_message" label="Message" rules={[{ required: true }]}>
            <Input.TextArea rows={4} placeholder="Provide a detailed description of the issue." />
          </Form.Item>
          <Form.Item name="status_id" label="Status" rules={[{ required: true }]}>
            <Select>{ticketConfig.statuses.map(s => <Option key={s.id} value={s.id}>{s.title_for_agent}</Option>)}</Select>
          </Form.Item>
          <Form.Item name="type_id" label="Type" rules={[{ required: true }]}>
            <Select>{ticketConfig.types.map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}</Select>
          </Form.Item>
          <Form.Item name="group_id" label="Group">
            <Select allowClear>{ticketConfig.groups.map(g => <Option key={g.id} value={g.id}>{g.title}</Option>)}</Select>
          </Form.Item>
          <Form.Item name="priority" label="Priority" initialValue="medium">
            <Select><Option value="low">Low</Option><Option value="medium">Medium</Option><Option value="high">High</Option><Option value="urgent">Urgent</Option></Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={isSubmitting} style={{ width: '100%' }}>Create Ticket</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default TicketsPage;