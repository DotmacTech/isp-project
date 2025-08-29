import React, { useState, useEffect, useCallback } from 'react';
import { 
  Table, 
  message, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Typography, 
  Tag, 
  Row, 
  Col,
  Space,
  Popconfirm,
  DatePicker,
  InputNumber,
  Tabs,
  Card,
  List,
  Avatar,
  Divider,
  Spin
} from 'antd';
import { 
  PlusOutlined, 
  SearchOutlined, 
  EditOutlined, 
  DeleteOutlined,
  UserOutlined,
  PhoneOutlined,
  MailOutlined,
  HomeOutlined
} from '@ant-design/icons';
import apiClient from '../api';
import moment from 'moment';

const { Title } = Typography;
const { Option } = Select;
const { Search } = Input;
const { TabPane } = Tabs;

const customerStatuses = ['active', 'new', 'blocked', 'disabled'];
const customerCategories = ['person', 'company'];
const billingTypes = ['recurring', 'prepaid_daily', 'prepaid_monthly'];

function CustomersPage() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [filters, setFilters] = useState({ search: '', status: null });
  const [form] = Form.useForm();

  // Data for form dropdowns
  const [partners, setPartners] = useState([]);
  const [locations, setLocations] = useState([]);
  const [allCustomers, setAllCustomers] = useState([]); // For parent customer dropdown
  const [tariffs, setTariffs] = useState([]);

  // State for services tab
  const [customerServices, setCustomerServices] = useState([]);
  const [servicesLoading, setServicesLoading] = useState(false);
  const [isServiceModalVisible, setIsServiceModalVisible] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [serviceForm] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);

    try {
      const response = await apiClient.get('/v1/customers/', {
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
          search: params.filters.search,
          status: params.filters.status,
        },
      });
      setCustomers(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current, pageSize: params.pagination.pageSize }));
    } catch (error) {
      message.error('Failed to fetch customers.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDropdownData = useCallback(async () => {
    try {
      const [partnersRes, locationsRes, customersRes, tariffsRes] = await Promise.all([
        apiClient.get('/v1/partners/'),
        apiClient.get('/v1/locations/'),
        apiClient.get('/v1/customers/', { params: { limit: 1000 } }), // Fetch customers for parent dropdown
        apiClient.get('/v1/internet-tariffs/', { params: { limit: 1000 } })
      ]);
      setPartners(partnersRes.data.items);
      setLocations(locationsRes.data);
      setAllCustomers(customersRes.data.items);
      setTariffs(tariffsRes.data.items);
    } catch (error) {
      message.error('Failed to fetch data for form dropdowns.');
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination, filters });
  }, [fetchData, pagination.current, pagination.pageSize, filters]);

  useEffect(() => {
    fetchDropdownData();
  }, [fetchDropdownData]);

  const handleTableChange = (newPagination) => {
    setPagination(newPagination);
  };

  const handleFilterChange = (value) => {
    setPagination(prev => ({ ...prev, current: 1 }));
    setFilters(prev => ({ ...prev, ...value }));
  }

  const handleAdd = () => {
    setEditingCustomer(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const fetchCustomerServices = useCallback(async (customerId) => {
    if (!customerId) return;
    setServicesLoading(true);
    try {
      const response = await apiClient.get('/v1/internet-services', {
        params: { customer_id: customerId, limit: 100 }
      });
      setCustomerServices(response.data.items);
    } catch (error) {
      message.error('Failed to fetch services for this customer.');
    } finally {
      setServicesLoading(false);
    }
  }, []);

  const handleEdit = (customer) => {
    setEditingCustomer(customer);
    form.setFieldsValue({
      ...customer,
      partner_id: customer.partner?.id,
      location_id: customer.location?.id,
    });
    fetchCustomerServices(customer.id);
    setIsModalVisible(true);
  };

  const handleDelete = async (customerId) => {
    try {
      await apiClient.delete(`/v1/customers/${customerId}`);
      message.success('Customer deleted successfully');
      fetchData({ pagination, filters });
    } catch (error) {
      message.error('Failed to delete customer.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingCustomer(null);
  };

  const handleFormFinish = async (values) => {
    const url = editingCustomer ? `/v1/customers/${editingCustomer.id}` : '/v1/customers/';
    const method = editingCustomer ? 'put' : 'post';

    try {
      await apiClient[method](url, values);
      message.success(`Customer ${editingCustomer ? 'updated' : 'added'} successfully`);
      setIsModalVisible(false);
      fetchData({ pagination, filters });
    } catch (error) {
      const errorDetail = error.response?.data?.detail || `Failed to ${editingCustomer ? 'update' : 'add'} customer.`;
      message.error(errorDetail);
    }
  };

  const handleServiceAdd = () => {
    setEditingService(null);
    serviceForm.resetFields();
    serviceForm.setFieldsValue({
      customer_id: editingCustomer.id,
      status: 'active',
      start_date: moment()
    });
    setIsServiceModalVisible(true);
  };

  const handleServiceEdit = (service) => {
    setEditingService(service);
    serviceForm.setFieldsValue({
      ...service,
      customer_id: service.customer.id,
      tariff_id: service.tariff.id,
      start_date: service.start_date ? moment(service.start_date) : null,
      end_date: service.end_date ? moment(service.end_date) : null,
    });
    setIsServiceModalVisible(true);
  };

  const handleServiceDelete = async (serviceId) => {
    try {
      await apiClient.delete(`/v1/internet-services/${serviceId}`);
      message.success('Service deleted successfully');
      fetchCustomerServices(editingCustomer.id);
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete service.');
    }
  };

  const handleServiceModalCancel = () => {
    setIsServiceModalVisible(false);
    setEditingService(null);
  };

  const handleServiceFormFinish = async (values) => {
    const payload = {
      ...values,
      start_date: values.start_date.format('YYYY-MM-DD'),
      end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : null,
    };
    const url = editingService ? `/v1/internet-services/${editingService.id}` : '/v1/internet-services/';
    const method = editingService ? 'put' : 'post';

    try {
      await apiClient[method](url, payload);
      message.success(`Service ${editingService ? 'updated' : 'created'} successfully`);
      setIsServiceModalVisible(false);
      fetchCustomerServices(editingCustomer.id);
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save service.');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Login', dataIndex: 'login', key: 'login' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Phone', dataIndex: 'phone', key: 'phone' },
    { title: 'Partner', dataIndex: ['partner', 'name'], key: 'partner' },
    { title: 'Location', dataIndex: ['location', 'name'], key: 'location' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        let color = 'default';
        if (status === 'active') color = 'success';
        if (status === 'blocked') color = 'error';
        if (status === 'new') color = 'processing';
        return <Tag color={color}>{status?.toUpperCase()}</Tag>;
      },
    },
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

  const serviceColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Description', dataIndex: 'description', key: 'description' },
    { title: 'Tariff', dataIndex: ['tariff', 'title'], key: 'tariff' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (status) => <Tag color={status === 'active' ? 'green' : 'red'}>{status?.toUpperCase()}</Tag> },
    { title: 'Login', dataIndex: 'login', key: 'login' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleServiceEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleServiceDelete(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const ServicesTab = () => (
    <div>
      <Button type="primary" onClick={handleServiceAdd} style={{ marginBottom: 16 }}>
        Add Service
      </Button>
      <Table
        dataSource={customerServices}
        columns={serviceColumns}
        rowKey="id"
        loading={servicesLoading}
        pagination={false}
      />
    </div>
  );

  return (
    <div>
      <Title level={2}>Customers</Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Button type="primary" onClick={handleAdd}>Add Customer</Button>
        </Col>
        <Col>
          <Search placeholder="Search by name, login, or email..." onSearch={(value) => handleFilterChange({ search: value })} style={{ width: 300 }} allowClear />
        </Col>
        <Col>
          <Select placeholder="Filter by status" onChange={(value) => handleFilterChange({ status: value })} style={{ width: 200 }} allowClear>
            {customerStatuses.map(status => <Option key={status} value={status}>{status}</Option>)}
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
        title={editingCustomer ? `Edit Customer: ${editingCustomer.name}` : 'Add Customer'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
        width={1000}
      >
        {!editingCustomer ? (
          <Form form={form} layout="vertical" onFinish={handleFormFinish} initialValues={{ status: 'active', category: 'person', billing_type: 'recurring' }}>
            <Form.Item name="name" label="Full Name" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="login" label="Login" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="email" label="Email" rules={[{ type: 'email' }]}><Input /></Form.Item>
            <Form.Item name="partner_id" label="Partner" rules={[{ required: true }]}>
              <Select placeholder="Select a partner">{partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select>
            </Form.Item>
            <Form.Item name="location_id" label="Location" rules={[{ required: true }]}>
              <Select placeholder="Select a location">{locations.map(l => <Option key={l.id} value={l.id}>{l.name}</Option>)}</Select>
            </Form.Item>
            <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Customer</Button></Form.Item>
          </Form>
        ) : (
          <Tabs defaultActiveKey="1">
            <TabPane tab="Customer Details" key="1">
              <Form form={form} layout="vertical" onFinish={handleFormFinish}>
                <Divider>Personal Information</Divider>
                <Row gutter={16}>
                  <Col span={12}><Form.Item name="name" label="Full Name" rules={[{ required: true }]}><Input /></Form.Item></Col>
                  <Col span={12}><Form.Item name="category" label="Category" rules={[{ required: true }]}><Select>{customerCategories.map(c => <Option key={c} value={c}>{c}</Option>)}</Select></Form.Item></Col>
                </Row>
                <Row gutter={16}>
                  <Col span={12}><Form.Item name="email" label="Contact Email" rules={[{ type: 'email' }]}><Input /></Form.Item></Col>
                  <Col span={12}><Form.Item name="billing_email" label="Billing Email" rules={[{ type: 'email' }]}><Input /></Form.Item></Col>
                </Row>
                <Form.Item name="phone" label="Phone"><Input /></Form.Item>
                <Divider>Login Information</Divider>
                <Row gutter={16}>
                  <Col span={12}><Form.Item name="login" label="Login" rules={[{ required: true }]}><Input disabled={!!editingCustomer} /></Form.Item></Col>
                  <Col span={12}><Form.Item name="password" label="Password" help="Leave blank to keep current password"><Input.Password placeholder="Enter new password" /></Form.Item></Col>
                </Row>
                <Divider>Address Information</Divider>
                <Form.Item name="street_1" label="Street Address"><Input /></Form.Item>
                <Row gutter={16}>
                  <Col span={8}><Form.Item name="city" label="City"><Input /></Form.Item></Col>
                  <Col span={8}><Form.Item name="subdivision_id" label="State/Province ID"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
                  <Col span={8}><Form.Item name="zip_code" label="Zip/Postal Code"><Input /></Form.Item></Col>
                </Row>
                <Form.Item name="gps" label="GPS Coordinates" help="Format: latitude,longitude"><Input /></Form.Item>
                <Divider>System & Billing Information</Divider>
                <Row gutter={16}>
                  <Col span={12}><Form.Item name="partner_id" label="Partner" rules={[{ required: true }]}><Select placeholder="Select a partner">{partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select></Form.Item></Col>
                  <Col span={12}><Form.Item name="location_id" label="Location" rules={[{ required: true }]}><Select placeholder="Select a location">{locations.map(l => <Option key={l.id} value={l.id}>{l.name}</Option>)}</Select></Form.Item></Col>
                </Row>
                <Row gutter={16}>
                  <Col span={12}><Form.Item name="parent_id" label="Parent Customer (for Sub-accounts)"><Select showSearch placeholder="Select a parent customer" allowClear filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>{allCustomers.filter(c => c.id !== editingCustomer?.id).map(c => <Option key={c.id} value={c.id}>{c.name} ({c.login})</Option>)}</Select></Form.Item></Col>
                  <Col span={12}><Form.Item name="status" label="Status" rules={[{ required: true }]}><Select>{customerStatuses.map(s => <Option key={s} value={s}>{s}</Option>)}</Select></Form.Item></Col>
                </Row>
                <Form.Item name="billing_type" label="Billing Type" rules={[{ required: true }]}><Select>{billingTypes.map(bt => <Option key={bt} value={bt}>{bt.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</Option>)}</Select></Form.Item>
                <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Customer</Button></Form.Item>
              </Form>
            </TabPane>
            <TabPane tab="Services" key="2">
              <ServicesTab />
            </TabPane>
          </Tabs>
        )}
      </Modal>
      <Modal title={editingService ? 'Edit Service' : 'Add Service'} open={isServiceModalVisible} onCancel={handleServiceModalCancel} footer={null} destroyOnClose>
        <Form form={serviceForm} layout="vertical" onFinish={handleServiceFormFinish}>
          <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
            <Select disabled><Option value={editingCustomer?.id}>{editingCustomer?.name}</Option></Select>
          </Form.Item>
          <Form.Item name="tariff_id" label="Tariff" rules={[{ required: true }]}>
            <Select placeholder="Select a tariff">{tariffs.map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}</Select>
          </Form.Item>
          <Form.Item name="description" label="Description" rules={[{ required: true }]}><Input.TextArea /></Form.Item>
          <Form.Item name="login" label="Login" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="password" label="Password" help={editingService ? "Leave blank to keep current password" : ""}><Input.Password /></Form.Item>
          <Form.Item name="ipv4" label="Static IP"><Input /></Form.Item>
          <Form.Item name="start_date" label="Start Date" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="End Date"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="status" label="Status" rules={[{ required: true }]}>
            <Select><Option value="active">Active</Option><Option value="stopped">Stopped</Option><Option value="pending">Pending</Option><Option value="terminated">Terminated</Option></Select>
          </Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Service</Button>
        </Form>
      </Modal>
    </div>
  );
}

export default CustomersPage;