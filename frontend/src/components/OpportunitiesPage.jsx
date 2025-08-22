import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Popconfirm, Tag, InputNumber, Typography, Row, Col, Space } from 'antd';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;
const { Search } = Input;

function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingOpportunity, setEditingOpportunity] = useState(null);
  const [isConvertModalVisible, setIsConvertModalVisible] = useState(false);
  const [convertingOpportunity, setConvertingOpportunity] = useState(null);
  const [filters, setFilters] = useState({ search: '', stage: null });
  const [leads, setLeads] = useState([]);
  const [partners, setPartners] = useState([]);
  const [locations, setLocations] = useState([]);
  const [form] = Form.useForm();
  const [convertForm] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      message.error('Authentication token not found. Please log in.');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get('/api/v1/crm/opportunities/', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
          search: params.filters.search,
          stage: params.filters.stage,
        },
      });
      setOpportunities(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current, pageSize: params.pagination.pageSize }));
    } catch (error) {
      message.error('Failed to fetch opportunities.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination, filters });
    const fetchDropdownData = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      try {
        const [leadsRes, partnersRes, locationsRes] = await Promise.all([
          axios.get('/api/v1/crm/leads/', { headers: { Authorization: `Bearer ${token}` }, params: { limit: 1000 } }),
          axios.get('/api/v1/partners/', { headers: { Authorization: `Bearer ${token}` } }),
          axios.get('/api/v1/locations/', { headers: { Authorization: `Bearer ${token}` } })
        ]);
        setLeads(leadsRes.data.items);
        setPartners(partnersRes.data);
        setLocations(locationsRes.data);
      } catch (error) {
        message.error('Failed to fetch auxiliary data for forms.');
      }
    };
    fetchDropdownData();
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
    setEditingOpportunity(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (opportunity) => {
    setEditingOpportunity(opportunity);
    form.setFieldsValue(opportunity);
    setIsModalVisible(true);
  };

  const handleConvert = (opportunity) => {
    setConvertingOpportunity(opportunity);
    convertForm.resetFields();
    setIsConvertModalVisible(true);
  };

  const handleDelete = async (opportunityId) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.delete(`/api/v1/crm/opportunities/${opportunityId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success('Opportunity deleted successfully');
      fetchData({ pagination, filters });
    } catch (error) {
      message.error('Failed to delete opportunity.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingOpportunity(null);
  };

  const handleConvertModalCancel = () => {
    setIsConvertModalVisible(false);
    setConvertingOpportunity(null);
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');
    const url = editingOpportunity ? `/api/v1/crm/opportunities/${editingOpportunity.id}` : '/api/v1/crm/opportunities/';
    const method = editingOpportunity ? 'put' : 'post';

    try {
      await axios[method](url, values, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success(`Opportunity ${editingOpportunity ? 'updated' : 'added'} successfully`);
      setIsModalVisible(false);
      fetchData({ pagination, filters });
    } catch (error) {
      const errorDetail = error.response?.data?.detail || `Failed to ${editingOpportunity ? 'update' : 'add'} opportunity.`;
      message.error(errorDetail);
    }
  };

  const handleConvertFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');
    if (!convertingOpportunity) return;

    try {
      await axios.post(`/api/v1/crm/opportunities/${convertingOpportunity.id}/convert`, values, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success('Opportunity converted to customer successfully!');
      setIsConvertModalVisible(false);
      fetchData({ pagination, filters });
    } catch (error) {
      const errorDetail = error.response?.data?.detail || 'Failed to convert opportunity.';
      message.error(errorDetail);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Lead', dataIndex: ['lead', 'name'], key: 'lead' },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', render: (amount) => `$${Number(amount).toFixed(2)}` },
    {
      title: 'Stage',
      dataIndex: 'stage',
      key: 'stage',
      render: (stage) => <Tag color={stage === 'Closed Won' ? 'success' : stage === 'Closed Lost' ? 'error' : 'default'}>{stage?.toUpperCase()}</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)} disabled={!!record.customer_id}>Edit</Button>
          {record.stage === 'Closed Won' && !record.customer_id && (
            <Button size="small" type="primary" onClick={() => handleConvert(record)}>
              Convert
            </Button>
          )}
          {record.customer_id && (
            <Tag color="success">CONVERTED</Tag>
          )}
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)} disabled={!!record.customer_id}>
            <Button size="small" danger disabled={!!record.customer_id}>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Opportunities Management</Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Button type="primary" onClick={handleAdd}>
            Add Opportunity
          </Button>
        </Col>
        <Col>
          <Search placeholder="Search by name..." onSearch={(value) => handleFilterChange({ search: value })} style={{ width: 300 }} allowClear />
        </Col>
        <Col>
          <Select placeholder="Filter by stage" onChange={(value) => handleFilterChange({ stage: value })} style={{ width: 200 }} allowClear>
            <Option value="Prospecting">Prospecting</Option>
            <Option value="Qualification">Qualification</Option>
            <Option value="Proposal">Proposal</Option>
            <Option value="Negotiation">Negotiation</Option>
            <Option value="Closed Won">Closed Won</Option>
            <Option value="Closed Lost">Closed Lost</Option>
          </Select>
        </Col>
      </Row>
      <Table
        dataSource={opportunities}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
      <Modal
        title={editingOpportunity ? 'Edit Opportunity' : 'Add Opportunity'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish} initialValues={{ stage: 'Prospecting' }}>
          <Form.Item name="name" label="Opportunity Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="lead_id" label="Lead" rules={[{ required: true }]}>
            <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())} placeholder="Select a lead">
              {leads.map(lead => <Option key={lead.id} value={lead.id}>{lead.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="amount" label="Amount">
            <InputNumber style={{ width: '100%' }} min={0} step="0.01" formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => value.replace(/\$\s?|(,*)/g, '')} />
          </Form.Item>
          <Form.Item name="stage" label="Stage" rules={[{ required: true }]}>
            <Select>
              <Option value="Prospecting">Prospecting</Option>
              <Option value="Qualification">Qualification</Option>
              <Option value="Proposal">Proposal</Option>
              <Option value="Negotiation">Negotiation</Option>
              <Option value="Closed Won">Closed Won</Option>
              <Option value="Closed Lost">Closed Lost</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Opportunity</Button>
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title={`Convert Opportunity: ${convertingOpportunity?.name}`}
        open={isConvertModalVisible}
        onCancel={handleConvertModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={convertForm} layout="vertical" onFinish={handleConvertFormFinish}>
          <p>
            This will create a new customer based on the lead information associated with this opportunity.
            Please provide the required details below.
          </p>
          <Form.Item name="login" label="Customer Login" rules={[{ required: true, message: 'Please input a login for the new customer!' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="partner_id" label="Partner" rules={[{ required: true }]}>
            <Select placeholder="Select a partner">
              {partners.map(partner => <Option key={partner.id} value={partner.id}>{partner.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="location_id" label="Location" rules={[{ required: true }]}>
            <Select placeholder="Select a location">
              {locations.map(location => <Option key={location.id} value={location.id}>{location.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Convert to Customer</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default OpportunitiesPage;