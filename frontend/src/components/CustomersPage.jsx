import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Spin, Typography, Button, Modal, Form, Input, Select, Popconfirm, Tag, Row, Col } from 'antd';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

function CustomersPage() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [filters, setFilters] = useState({ search: '', status: null });
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [partners, setPartners] = useState([]);
  const [locations, setLocations] = useState([]);
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
      const response = await axios.get('/api/v1/customers/', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
          search: params.filters.search || undefined,
          status: params.filters.status || undefined,
        },
      });
      setCustomers(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to view customers.');
      } else {
        message.error('Failed to fetch customers.');
      }
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []); // useCallback with empty dependency array is fine as it gets all params

  // Debounce search term
  useEffect(() => {
    const handler = setTimeout(() => {
      setFilters(prev => ({ ...prev, search: searchTerm }));
      setPagination(p => ({ ...p, current: 1 })); // Reset to page 1 on new search
    }, 500); // 500ms delay
    return () => clearTimeout(handler);
  }, [searchTerm]);

  useEffect(() => {
    fetchData({ pagination, filters });
  }, [fetchData, pagination.current, pagination.pageSize, filters]);

  useEffect(() => {
    const fetchDropdownData = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      try {
        const [partnersRes, locationsRes] = await Promise.all([
          axios.get('/api/v1/partners/', { headers: { Authorization: `Bearer ${token}` } }),
          axios.get('/api/v1/locations/', { headers: { Authorization: `Bearer ${token}` } })
        ]);
        setPartners(partnersRes.data);
        setLocations(locationsRes.data);
      } catch (error) {
        message.error('Failed to fetch partners or locations for dropdowns.');
        console.error('Error fetching dropdown data:', error);
      }
    };
    fetchDropdownData();
  }, []);

  const handleStatusChange = (value) => {
    setFilters(prev => ({ ...prev, status: value }));
    setPagination(p => ({ ...p, current: 1 })); // Reset to page 1
  };

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const handleAdd = () => {
    setEditingCustomer(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (customer) => {
    setEditingCustomer(customer);
    form.setFieldsValue(customer);
    setIsModalVisible(true);
  };

  const handleDelete = async (customerId) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.delete(`/api/v1/customers/${customerId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success('Customer deleted successfully');
      setCustomers(currentCustomers => currentCustomers.filter(customer => customer.id !== customerId));
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to delete customers.');
      } else {
        message.error('Failed to delete customer.');
      }
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingCustomer(null);
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');
    const url = editingCustomer ? `/api/v1/customers/${editingCustomer.id}` : '/api/v1/customers/';
    const method = editingCustomer ? 'put' : 'post';

    try {
      await axios[method](url, values, {
        headers: { Authorization: `Bearer ${token}` },
      });
      message.success(`Customer ${editingCustomer ? 'updated' : 'added'} successfully`);
      setIsModalVisible(false);
      fetchData({ pagination, filters }); // Use current filters to refresh data
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error(`You do not have permission to ${editingCustomer ? 'edit' : 'create'} customers.`);
      } else {
        const errorDetail = error.response?.data?.detail;
        const errorMessage = Array.isArray(errorDetail) 
          ? errorDetail.map(e => `${e.loc[1]}: ${e.msg}`).join('; ')
          : errorDetail || `Failed to ${editingCustomer ? 'update' : 'add'} customer`;
        message.error(errorMessage);
      }
      console.error('Form submission error:', error);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Login', dataIndex: 'login', key: 'login' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Phone', dataIndex: 'phone', key: 'phone' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const color = status === 'active' ? 'green' : status === 'blocked' ? 'red' : 'orange';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    { title: 'Category', dataIndex: 'category', key: 'category' },
    {
      title: 'Location',
      dataIndex: 'location_id',
      key: 'location_id',
      render: (locationId) => {
        const location = locations.find(loc => loc.id === locationId);
        return location ? location.name : 'N/A';
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <span>
          <Button size="small" onClick={() => handleEdit(record)} style={{ marginRight: 8 }}>Edit</Button>
          <Popconfirm title="Are you sure you want to delete this customer?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Customer Management</Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Button type="primary" onClick={handleAdd}>
            Add Customer
          </Button>
        </Col>
        <Col xs={24} sm={12} md={10} lg={8}>
          <Input.Search
            placeholder="Search by Name, Login, Email..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            allowClear
          />
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Select
            placeholder="Filter by Status"
            onChange={handleStatusChange}
            style={{ width: '100%' }}
            allowClear
          >
            <Option value="active">Active</Option>
            <Option value="blocked">Blocked</Option>
            <Option value="new">New</Option>
          </Select>
        </Col>
      </Row>
      <Table
        dataSource={customers}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
      <Modal
        title={editingCustomer ? 'Edit Customer' : 'Add Customer'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish} initialValues={{ status: 'active', category: 'person' }}>
          <Form.Item name="name" label="Full Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="login" label="Login" rules={[{ required: !editingCustomer }]}>
            <Input disabled={!!editingCustomer} />
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
          <Form.Item name="email" label="Email" rules={[{ type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="Phone Number"><Input /></Form.Item>
          <Form.Item name="status" label="Status" rules={[{ required: true }]}>
            <Select><Option value="active">Active</Option><Option value="blocked">Blocked</Option><Option value="new">New</Option></Select>
          </Form.Item>
          <Form.Item name="category" label="Category" rules={[{ required: true }]}>
            <Select><Option value="person">Person</Option><Option value="company">Company</Option></Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Customer</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default CustomersPage;