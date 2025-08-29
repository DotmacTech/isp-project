import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Popconfirm, Tag, Typography, Row, Col, Space } from 'antd';
import apiClient from '../api';

const { Title } = Typography;
const { Option } = Select;
const { Search } = Input;

const leadStatuses = ['New', 'Contacted', 'Qualified', 'Lost', 'Converted'];

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

    try {
      const response = await apiClient.get('/v1/leads/', {
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
      message.error('Failed to fetch leads.');
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
    try {
      await apiClient.delete(`/v1/leads/${leadId}`);
      message.success('Lead deleted successfully');
      fetchData({ pagination, filters });
    } catch (error) {
      message.error('Failed to delete lead.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingLead(null);
  };

  const handleFormFinish = async (values) => {
    const url = editingLead ? `/v1/leads/${editingLead.id}` : '/v1/leads/';
    const method = editingLead ? 'put' : 'post';

    try {
      await apiClient[method](url, values);
      message.success(`Lead ${editingLead ? 'updated' : 'added'} successfully`);
      setIsModalVisible(false);
      fetchData({ pagination, filters });
    } catch (error) {
      const errorDetail = error.response?.data?.detail || `Failed to ${editingLead ? 'update' : 'add'} lead.`;
      message.error(errorDetail);
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
      render: (status) => {
        let color = 'default';
        if (status === 'Qualified' || status === 'Converted') color = 'success';
        if (status === 'Lost') color = 'error';
        return <Tag color={color}>{status?.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)} disabled={record.status === 'Converted'}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)} disabled={record.status === 'Converted'}>
            <Button size="small" danger disabled={record.status === 'Converted'}>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Leads Management</Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Button type="primary" onClick={handleAdd}>Add Lead</Button>
        </Col>
        <Col>
          <Search placeholder="Search by name, email, or phone..." onSearch={(value) => handleFilterChange({ search: value })} style={{ width: 300 }} allowClear />
        </Col>
        <Col>
          <Select placeholder="Filter by status" onChange={(value) => handleFilterChange({ status: value })} style={{ width: 200 }} allowClear>
            {leadStatuses.map(status => <Option key={status} value={status}>{status}</Option>)}
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
        <Form form={form} layout="vertical" onFinish={handleFormFinish} initialValues={{ status: 'New' }}>
          <Form.Item name="name" label="Lead Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="Email" rules={[{ type: 'email' }]}><Input /></Form.Item>
          <Form.Item name="phone" label="Phone"><Input /></Form.Item>
          <Form.Item name="status" label="Status" rules={[{ required: true }]}>
            <Select>
              {leadStatuses.filter(s => s !== 'Converted').map(status => <Option key={status} value={status}>{status}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Lead</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default LeadsPage;