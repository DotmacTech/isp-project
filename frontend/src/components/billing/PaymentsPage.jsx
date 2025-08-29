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
import apiClient from '../../api';
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
        apiClient.get('/v1/billing/payments/stats/', {
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
      message.error('Failed to fetch payments.');
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.pageSize]);
  
  // Fetch dropdown data
  const fetchDropdownData = useCallback(async () => {
    try {
      const [customersRes, methodsRes] = await Promise.all([
        apiClient.get('/v1/customers/', { 
          params: { limit: 1000 } 
        }),
        apiClient.get('/v1/billing/payment-methods/')
      ]);
      setCustomers(customersRes.data.items || []);
      setPaymentMethods(methodsRes.data || []);
    } catch (error) {
      message.error('Failed to fetch data for dropdowns.');
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });

    const fetchDropdownData = async () => {
      try {
        const [customersRes, methodsRes] = await Promise.all([
          apiClient.get('/v1/customers/', { params: { limit: 1000 } }),
          apiClient.get('/v1/billing/payment-methods/')
        ]);
        setCustomers(customersRes.data.items);
        setPaymentMethods(methodsRes.data);
      } catch (error) {
        message.error('Failed to fetch data for dropdowns.');
      }
    };
    fetchDropdownData();
  }, [fetchData, pagination.current, pagination.pageSize]);

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, ...newPagination }));
  };

  const handleAdd = () => {
    form.resetFields();
    form.setFieldsValue({ date: moment() });
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormFinish = async (values) => {
    const payload = {
      ...values,
      date: values.date.format('YYYY-MM-DD'),
    };
    try {
      await apiClient.post('/v1/billing/payments/', payload);
      message.success('Payment recorded successfully.');
      setIsModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to record payment.');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Customer ID', dataIndex: 'customer_id', key: 'customer_id' },
    { title: 'Invoice ID', dataIndex: 'invoice_id', key: 'invoice_id', render: (id) => id || 'N/A' },
    { title: 'Receipt #', dataIndex: 'receipt_number', key: 'receipt_number' },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', render: (amount) => `$${Number(amount).toFixed(2)}` },
    { title: 'Date', dataIndex: 'date', key: 'date', render: (text) => new Date(text).toLocaleDateString() },
  ];

  return (
    <div>
      <Title level={2}>Payments</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Add Payment</Button>
      <Table dataSource={payments} columns={columns} rowKey="id" loading={loading} pagination={pagination} onChange={handleTableChange} />
      <Modal title="Add New Payment" open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}><Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>{customers.map(c => <Option key={c.id} value={c.id}>{c.name}</Option>)}</Select></Form.Item>
          <Form.Item name="payment_type_id" label="Payment Method" rules={[{ required: true }]}><Select>{paymentMethods.map(m => <Option key={m.id} value={m.id}>{m.name}</Option>)}</Select></Form.Item>
          <Form.Item name="amount" label="Amount" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={0.01} step="0.01" /></Form.Item>
          <Form.Item name="receipt_number" label="Receipt / Transaction ID" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="date" label="Payment Date" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="invoice_id" label="Invoice ID (Optional)"><InputNumber style={{ width: '100%' }} min={1} /></Form.Item>
          <Form.Item name="comment" label="Comment"><Input.TextArea /></Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Record Payment</Button>
        </Form>
      </Modal>
    </div>
  );
}

export default PaymentsPage;