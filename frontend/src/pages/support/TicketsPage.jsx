import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Typography,
  Space,
  Popconfirm,
  message,
  Card,
  Tag,
  Row,
  Col,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, MailOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';
import moment from 'moment';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const priorityColors = {
  low: 'blue',
  medium: 'green',
  high: 'orange',
  urgent: 'red',
};

const TicketsPage = () => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [filters, setFilters] = useState({});
  const [sorter, setSorter] = useState({});

  // Data for forms and filters
  const [supportData, setSupportData] = useState({
    statuses: [],
    types: [],
    groups: [],
    customers: [],
    admins: [],
  });
  const [supportDataLoading, setSupportDataLoading] = useState(true);

  // Modal state
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingTicket, setEditingTicket] = useState(null);
  const [form] = Form.useForm();

  const fetchSupportData = useCallback(async () => {
    setSupportDataLoading(true);
    try {
      const [statusesRes, typesRes, groupsRes, customersRes, adminsRes] = await Promise.all([
        apiClient.get('/v1/support/statuses/'),
        apiClient.get('/v1/support/types/'),
        apiClient.get('/v1/support/groups'),
        apiClient.get('/v1/customers/?limit=1000'), // Fetch customers for dropdown
        apiClient.get('/v1/administrators/?limit=1000'), // Fetch admins for dropdown
      ]);
      setSupportData({
        statuses: statusesRes.data,
        types: typesRes.data,
        groups: groupsRes.data,
        customers: customersRes.data.items || [],
        admins: adminsRes.data || [],
      });
    } catch (error) {
      message.error('Failed to fetch support configuration data.');
      console.error('Support data fetch error:', error);
    } finally {
      setSupportDataLoading(false);
    }
  }, []);

  const fetchTickets = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const queryParams = {
        skip: (params.pagination.current - 1) * params.pagination.pageSize,
        limit: params.pagination.pageSize,
        sort_by: params.sorter.field,
        sort_order: params.sorter.order === 'ascend' ? 'asc' : 'desc',
        ...params.filters,
      };
      const response = await apiClient.get('/v1/support/tickets', { params: queryParams });
      setTickets(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        current: params.pagination.current,
        pageSize: params.pagination.pageSize,
      }));
    } catch (error) {
      message.error('Failed to fetch tickets.');
      console.error('Fetch tickets error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSupportData();
  }, [fetchSupportData]);

  useEffect(() => {
    fetchTickets({ pagination, filters, sorter });
  }, [fetchTickets, pagination.current, pagination.pageSize, filters, sorter]);

  const handleTableChange = (newPagination, newFilters, newSorter) => {
    setPagination(newPagination);
    setFilters(newFilters);
    setSorter(newSorter);
  };

  const handleAdd = () => {
    setEditingTicket(null);
    form.resetFields();
    form.setFieldsValue({ priority: 'medium' });
    setIsModalVisible(true);
  };

  const handleEdit = (ticket) => {
    setEditingTicket(ticket);
    form.setFieldsValue({
      ...ticket,
      // Ensure related fields are set by ID
      customer_id: ticket.customer?.id,
      assign_to: ticket.assignee?.id,
      status_id: ticket.status?.id,
      group_id: ticket.group?.id,
      type_id: ticket.ticket_type?.id,
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/v1/support/tickets/${id}`);
      message.success('Ticket deleted successfully');
      fetchTickets({ pagination, filters, sorter });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete ticket.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormFinish = async (values) => {
    const url = editingTicket
      ? `/v1/support/tickets/${editingTicket.id}/`
      : '/v1/support/tickets/';
    const method = editingTicket ? 'put' : 'post';

    try {
      await apiClient({ method, url, data: values });
      message.success(`Ticket ${editingTicket ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      fetchTickets({ pagination, filters, sorter });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save ticket.');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', sorter: true },
    {
      title: 'Subject',
      dataIndex: 'subject',
      key: 'subject',
      sorter: true,
      render: (text, record) => <a onClick={() => handleEdit(record)}>{text}</a>,
    },
    {
      title: 'Customer',
      dataIndex: ['customer', 'name'],
      key: 'customer',
      sorter: true,
      filters: supportData.customers.map(c => ({ text: c.name, value: c.id })),
      filteredValue: filters.customer_id || null,
    },
    {
      title: 'Assignee',
      dataIndex: ['assignee', 'user', 'full_name'],
      key: 'assignee',
      sorter: true,
      filters: supportData.admins.map(a => ({ text: a.user.full_name, value: a.id })),
      filteredValue: filters.assign_to || null,
    },
    {
      title: 'Status',
      dataIndex: ['status', 'title_for_agent'],
      key: 'status',
      sorter: true,
      render: (text, record) => <Tag color={record.status?.label || 'default'}>{text}</Tag>,
      filters: supportData.statuses.map(s => ({ text: s.title_for_agent, value: s.id })),
      filteredValue: filters.status_id || null,
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      sorter: true,
      render: (priority) => <Tag color={priorityColors[priority]}>{priority?.toUpperCase()}</Tag>,
      filters: [
        { text: 'Low', value: 'low' },
        { text: 'Medium', value: 'medium' },
        { text: 'High', value: 'high' },
        { text: 'Urgent', value: 'urgent' },
      ],
      filteredValue: filters.priority || null,
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      sorter: true,
      render: (date) => moment(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" icon={<DeleteOutlined />} danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}><MailOutlined /> Support Tickets</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          New Ticket
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={tickets}
        rowKey="id"
        pagination={pagination}
        loading={loading || supportDataLoading}
        onChange={handleTableChange}
        scroll={{ x: 'max-content' }}
      />
      <Modal
        title={editingTicket ? `Edit Ticket #${editingTicket.id}` : 'Create New Ticket'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        width={800}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="subject" label="Subject" rules={[{ required: true }]}>
            <Input placeholder="Enter ticket subject" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
                <Select showSearch placeholder="Select a customer" optionFilterProp="children" filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
                  {supportData.customers.map(c => <Option key={c.id} value={c.id}>{c.name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="assign_to" label="Assign To">
                <Select showSearch placeholder="Select an assignee" optionFilterProp="children" filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
                  {supportData.admins.map(a => <Option key={a.id} value={a.id}>{a.user.full_name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="status_id" label="Status" rules={[{ required: true }]}>
                <Select placeholder="Select status">
                  {supportData.statuses.map(s => <Option key={s.id} value={s.id}>{s.title_for_agent}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="group_id" label="Group">
                <Select placeholder="Select group">
                  {supportData.groups.map(g => <Option key={g.id} value={g.id}>{g.title}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="type_id" label="Type">
                <Select placeholder="Select type">
                  {supportData.types.map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="priority" label="Priority" rules={[{ required: true }]}>
            <Select placeholder="Select priority">
              <Option value="low">Low</Option>
              <Option value="medium">Medium</Option>
              <Option value="high">High</Option>
              <Option value="urgent">Urgent</Option>
            </Select>
          </Form.Item>
          {!editingTicket && (
            <Form.Item name="message" label="Initial Message" rules={[{ required: true }]}>
              <TextArea rows={4} placeholder="Describe the issue..." />
            </Form.Item>
          )}
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
              {editingTicket ? 'Save Changes' : 'Create Ticket'}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default TicketsPage;