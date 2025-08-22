import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Popconfirm, Tag, Typography, Row, Col } from 'antd';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;
const { Search } = Input;

function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  const [filters, setFilters] = useState({ search: '', status: null });
  const [form] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      message.error('Authentication token not found. Please log in.');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get('/api/v1/crm/leads/', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
          search: params.filters.search,
          status: params.filters.status,
        },
      });
      setLeads(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current, pageSize: params.pagination.pageSize }));
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to view leads.');
      } else {
        message.error('Failed to fetch leads.');
      }
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination, filters });
  }, [fetchData, pagination.current, pagination.pageSize, filters]);

  const handleTableChange = (newPagination) => {
    setPagination(newPagination);
  };

  const handleFilterChange = (value) => {
    // Reset to first page when filters change
    setPagination(prev => ({ ...prev, current: 1 }));
    setFilters(prev => ({ ...prev, ...value }));
  }

  const handleAdd = () => {
    setEditingLead(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (lead) => {
    setEditingLead(lead);
    form.setFieldsValue(lead);
    setIsModalVisible(true);
  };

  const handleDelete = async (leadId) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.delete(`/api/v1/crm/leads/${leadId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success('Lead deleted successfully');
      fetchData({ pagination, filters });
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to delete leads.');
      } else {
        message.error('Failed to delete lead.');
      }
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingLead(null);
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');
    const url = editingLead ? `/api/v1/crm/leads/${editingLead.id}` : '/api/v1/crm/leads/';
    const method = editingLead ? 'put' : 'post';

    try {
      await axios[method](url, values, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success(`Lead ${editingLead ? 'updated' : 'added'} successfully`);
      setIsModalVisible(false);
      fetchData({ pagination, filters });
    } catch (error) {
      const errorDetail = error.response?.data?.detail || `Failed to ${editingLead ? 'update' : 'add'} lead.`;
      message.error(errorDetail);
      console.error('Form submission error:', error);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Phone', dataIndex: 'phone', key: 'phone' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag>{status?.toUpperCase()}</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <span>
          <Button size="small" onClick={() => handleEdit(record)} style={{ marginRight: 8 }}>Edit</Button>
          <Popconfirm title="Are you sure you want to delete this lead?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Leads Management</Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Button type="primary" onClick={handleAdd}>
            Add Lead
          </Button>
        </Col>
        <Col>
          <Search placeholder="Search by name, email, phone..." onSearch={(value) => handleFilterChange({ search: value })} style={{ width: 300 }} allowClear />
        </Col>
        <Col>
          <Select placeholder="Filter by status" onChange={(value) => handleFilterChange({ status: value })} style={{ width: 200 }} allowClear>
            <Option value="new">New</Option>
            <Option value="contacted">Contacted</Option>
            <Option value="qualified">Qualified</Option>
            <Option value="unqualified">Unqualified</Option>
            <Option value="converted">Converted</Option>
          </Select>
        </Col>
      </Row>
      <Table
        dataSource={leads}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
      <Modal
        title={editingLead ? 'Edit Lead' : 'Add Lead'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish} initialValues={{ status: 'new' }}>
          <Form.Item name="name" label="Full Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="Phone Number"><Input /></Form.Item>
          <Form.Item name="status" label="Status" rules={[{ required: true }]}>
            <Select>
              <Option value="new">New</Option>
              <Option value="contacted">Contacted</Option>
              <Option value="qualified">Qualified</Option>
              <Option value="unqualified">Unqualified</Option>
              <Option value="converted">Converted</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Lead</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default LeadsPage;