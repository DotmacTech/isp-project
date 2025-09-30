import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Table, 
  message, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Typography, 
  InputNumber, 
  DatePicker,
  Card,
  Row,
  Col,
  Space,
  Tag,
  Statistic,
  Drawer,
  Checkbox,
  Tooltip,
  Dropdown,
  Menu,
  Alert,
  Progress,
  notification,
  Popconfirm,
  Upload,
  Divider,
  Badge
} from 'antd';
import {
  PlusOutlined,
  DownloadOutlined,
  FilterOutlined,
  SearchOutlined,
  ReloadOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  MoreOutlined,
  DollarOutlined,
  CreditCardOutlined,
  BankOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  UploadOutlined
} from '@ant-design/icons';
import apiClient from '../../services/api';
import moment from 'moment';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

function PaymentsPage() {
  // Enhanced state management
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [paymentGateways, setPaymentGateways] = useState([]);
  const [form] = Form.useForm();
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [filterDrawerVisible, setFilterDrawerVisible] = useState(false);
  const [previewDrawerVisible, setPreviewDrawerVisible] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [quickStats, setQuickStats] = useState({
    total: 0,
    totalAmount: 0,
    successful: 0,
    pending: 0,
    failed: 0
  });
  const [editingPayment, setEditingPayment] = useState(null);
  
  // Advanced filtering state
  const [filters, setFilters] = useState({
    status: [],
    customer_id: null,
    date_range: [],
    amount_range: [null, null],
    search: '',
    payment_method: [],
    transaction_type: []
  });
  
  // Export state
  const [exportLoading, setExportLoading] = useState(false);
  const [bulkProcessing, setBulkProcessing] = useState(false);

  // Enhanced data fetching with filters
  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);

    try {
      // Build query parameters
      const queryParams = {
        skip: (params.pagination?.current - 1 || 0) * (params.pagination?.pageSize || pagination.pageSize),
        limit: params.pagination?.pageSize || pagination.pageSize,
        ...filters
      };
      
      // Convert date ranges
      if (filters.date_range && filters.date_range.length === 2) {
        queryParams.start_date = filters.date_range[0].format('YYYY-MM-DD');
        queryParams.end_date = filters.date_range[1].format('YYYY-MM-DD');
        delete queryParams.date_range;
      }
      
      // Convert amount range
      if (filters.amount_range[0]) queryParams.min_amount = filters.amount_range[0];
      if (filters.amount_range[1]) queryParams.max_amount = filters.amount_range[1];
      delete queryParams.amount_range;
      
      // Convert arrays to comma-separated strings
      if (filters.status && filters.status.length > 0) {
        queryParams.status = filters.status.join(',');
      }
      if (filters.payment_method && filters.payment_method.length > 0) {
        queryParams.payment_method = filters.payment_method.join(',');
      }
      
      const [paymentsResponse, statsResponse] = await Promise.all([
        apiClient.get('/v1/billing/payments/', {
          params: queryParams
        }),
        apiClient.get('/v1/billing/payments/stats', {
          params: { ...queryParams, skip: 0, limit: undefined }
        })
      ]);
      
      setPayments(paymentsResponse.data.items || []);
      setPagination(prev => ({ 
        ...prev, 
        total: paymentsResponse.data.total || 0, 
        current: params.pagination?.current || prev.current 
      }));
      
      // Update quick stats
      setQuickStats(statsResponse.data || {
        total: 0,
        totalAmount: 0,
        successful: 0,
        pending: 0,
        failed: 0
      });
      
    } catch (error) {
      console.error('Fetch error:', error);
      // Check if it's an authorization error
      if (error.response && error.response.status === 401) {
        message.error('You do not have permission to view payments. Please contact your system administrator.');
      } else if (error.response && error.response.status === 403) {
        message.error('Access denied. You do not have permission to view payments.');
      } else {
        message.error('Failed to fetch payments. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.pageSize]);
  
  // Fetch dropdown data
  const fetchDropdownData = useCallback(async () => {
    try {
      const [customersRes, methodsRes, gatewaysRes] = await Promise.all([
        apiClient.get('/v1/customers/', { 
          params: { limit: 1000 } 
        }),
        apiClient.get('/v1/billing/payment-methods/'),
        apiClient.get('/v1/billing/payment-gateways/', { params: { is_active: true } })
      ]);
      setCustomers(customersRes.data.items || []);
      setPaymentMethods(methodsRes.data || []);
      setPaymentGateways(gatewaysRes.data.filter(g => g.is_active) || []);
    } catch (error) {
      if (error.response && error.response.status === 401) {
        message.error('You do not have permission to view customer or payment method data. Please contact your system administrator.');
      } else if (error.response && error.response.status === 403) {
        message.error('Access denied. You do not have permission to view customer or payment method data.');
      } else {
        message.error('Failed to fetch supporting data for the form.');
      }
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });
    fetchDropdownData();
  }, [fetchData, fetchDropdownData]);

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, ...newPagination }));
  };

  const handleAdd = () => {
    form.resetFields();
    setEditingPayment(null);
    form.setFieldsValue({
      date: moment(),
      status: 'pending'
    });
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormFinish = async (values) => {
    setLoading(true);
    try {
      const payload = {
        customer_id: values.customer_id,
        amount: values.amount,
        gateway_id: values.gateway_id,
        payment_method_id: values.payment_method_id,
        description: values.description,
        invoice_id: values.invoice_id
      };
      await apiClient.post('/v1/billing/payments/process', payload);
      message.success('Payment processing initiated successfully.');
      setIsModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to process payment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ margin: 0 }}>Payments Management</Title>
        </Col>
        <Col>
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchData({ pagination })}
              loading={loading}
            >
              Refresh
            </Button>
            <Button 
              icon={<FilterOutlined />} 
              onClick={() => setFilterDrawerVisible(true)}
            >
              Advanced Filters
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleAdd}
            >
              Add Payment
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats Cards */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Payments"
              value={quickStats.total}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Successful"
              value={quickStats.successful}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Pending"
              value={quickStats.pending}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Failed"
              value={quickStats.failed}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Table
          dataSource={payments}
          columns={[
            {
              title: 'ID',
              dataIndex: 'id',
              key: 'id',
            },
            {
              title: 'Customer',
              dataIndex: ['customer', 'name'],
              key: 'customer',
            },
            {
              title: 'Amount',
              dataIndex: 'amount',
              key: 'amount',
              render: (text) => `$${Number(text || 0).toFixed(2)}`,
            },
            {
              title: 'Payment Method',
              dataIndex: 'payment_method',
              key: 'payment_method',
            },
            {
              title: 'Status',
              dataIndex: 'status',
              key: 'status',
              render: (status) => {
                const statusColors = {
                  'completed': 'success',
                  'pending': 'warning',
                  'failed': 'error'
                };
                return (
                  <Tag color={statusColors[status] || 'default'}>
                    {status?.toUpperCase()}
                  </Tag>
                );
              },
            },
            {
              title: 'Date',
              dataIndex: 'created_at',
              key: 'created_at',
              render: (text) => moment(text).format('MMM DD, YYYY'),
            },
          ]}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
            pageSizeOptions: ['10', '20', '50', '100']
          }}
          onChange={handleTableChange}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
        />
      </Card>

      <Modal
        title={editingPayment ? 'Edit Payment' : 'Process New Payment'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnHidden
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
            <Select showSearch placeholder="Select a customer" filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
              {customers.map(c => <Option key={c.id} value={c.id}>{c.name}</Option>)}
            </Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="amount" label="Amount" rules={[{ required: true }]}>
                <InputNumber min={0.01} step="0.01" style={{ width: '100%' }} formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => value.replace(/\$\s?|(,*)/g, '')} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="gateway_id" label="Payment Gateway" rules={[{ required: true }]}>
                <Select placeholder="Select a gateway">
                  {paymentGateways.map(g => <Option key={g.id} value={g.id}>{g.name} ({g.gateway_type})</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="payment_method_id" label="Payment Method" rules={[{ required: true }]}>
            <Select placeholder="Select a payment method">
              {paymentMethods.map(m => <Option key={m.id} value={m.id}>{m.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={3} placeholder="e.g., Payment for Invoice #123" />
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" loading={loading} style={{ width: '100%' }}>Process Payment</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default PaymentsPage;