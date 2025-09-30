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
  Badge,
  Tabs
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
  UploadOutlined,
  SendOutlined,
  PrinterOutlined
} from '@ant-design/icons';
import apiClient from '../../services/api';
import moment from 'moment';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TextArea } = Input;
// TabPane is not used in this component

function InvoicesPage() {
  // Enhanced state management
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState(null);
  const [form] = Form.useForm();
  const [customers, setCustomers] = useState([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [bulkActionVisible, setBulkActionVisible] = useState(false);
  const [filterDrawerVisible, setFilterDrawerVisible] = useState(false);
  const [previewDrawerVisible, setPreviewDrawerVisible] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [quickStats, setQuickStats] = useState({
    total: 0,
    paid: 0,
    pending: 0,
    overdue: 0,
    totalAmount: 0
  });
  
  // Advanced filtering state
  const [filters, setFilters] = useState({
    status: [],
    customer_id: null,
    date_range: [],
    amount_range: [null, null],
    search: '',
    due_date_range: [],
    payment_status: []
  });
  
  // Bulk operations state
  const [bulkOperation, setBulkOperation] = useState('');
  const [bulkProgress, setBulkProgress] = useState(0);
  const [bulkProcessing, setBulkProcessing] = useState(false);
  
  // Export state
  const [exportLoading, setExportLoading] = useState(false);
  const [exportFormat, setExportFormat] = useState('excel');
  
  const tableRef = useRef();

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
      
      if (filters.due_date_range && filters.due_date_range.length === 2) {
        queryParams.due_date_start = filters.due_date_range[0].format('YYYY-MM-DD');
        queryParams.due_date_end = filters.due_date_range[1].format('YYYY-MM-DD');
        delete queryParams.due_date_range;
      }
      
      // Convert amount range
      if (filters.amount_range[0]) queryParams.min_amount = filters.amount_range[0];
      if (filters.amount_range[1]) queryParams.max_amount = filters.amount_range[1];
      delete queryParams.amount_range;
      
      // Convert arrays to comma-separated strings
      if (filters.status && filters.status.length > 0) {
        queryParams.status = filters.status.join(',');
      }
      if (filters.payment_status && filters.payment_status.length > 0) {
        queryParams.payment_status = filters.payment_status.join(',');
      }
      
      const [invoicesResponse, statsResponse] = await Promise.all([
        apiClient.get('/v1/billing/invoices', {
          params: queryParams
        }),
        apiClient.get('/v1/billing/invoices/stats/', {
          params: { ...queryParams, skip: 0, limit: undefined }
        })
      ]);
      
      setInvoices(invoicesResponse.data.items || []);
      setPagination(prev => ({ 
        ...prev, 
        total: invoicesResponse.data.total || 0, 
        current: params.pagination?.current || prev.current 
      }));
      
      // Update quick stats
      setQuickStats(statsResponse.data || {
        total: 0,
        paid: 0,
        pending: 0,
        overdue: 0,
        totalAmount: 0
      });
      
    } catch (error) {
      console.error('Fetch error:', error);
      // Check if it's an authorization error
      if (error.response && error.response.status === 401) {
        message.error('You do not have permission to view invoices. Please contact your system administrator.');
      } else if (error.response && error.response.status === 403) {
        message.error('Access denied. You do not have permission to view invoices.');
      } else {
        message.error('Failed to fetch invoices. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.pageSize]);
  
  // Fetch customers and initial data
  const fetchInitialData = useCallback(async () => {
    try {
      const customersRes = await apiClient.get('/v1/customers/', { 
        params: { limit: 1000 } 
      });
      setCustomers(customersRes.data.items || []);
    } catch (error) {
      if (error.response && error.response.status === 401) {
        message.error('You do not have permission to view customers. Please contact your system administrator.');
      } else if (error.response && error.response.status === 403) {
        message.error('Access denied. You do not have permission to view customers.');
      } else {
        message.error('Failed to fetch customers.');
      }
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);
  
  useEffect(() => {
    fetchData({ pagination });
  }, [fetchData, pagination.current, pagination.pageSize]);
  
  // Enhanced action handlers
  const handleTableChange = (newPagination, tableFilters, sorter) => {
    setPagination(prev => ({ ...prev, ...newPagination }));
  };
  
  const handleFilterApply = (newFilters) => {
    setFilters(newFilters);
    setFilterDrawerVisible(false);
    setPagination(prev => ({ ...prev, current: 1 })); // Reset to first page
  };
  
  const handleFilterReset = () => {
    setFilters({
      status: [],
      customer_id: null,
      date_range: [],
      amount_range: [null, null],
      search: '',
      due_date_range: [],
      payment_status: []
    });
    setPagination(prev => ({ ...prev, current: 1 }));
  };
  
  const handleBulkAction = async (action) => {
    if (!selectedRowKeys.length) {
      message.warning('Please select invoices first.');
      return;
    }
    
    setBulkOperation(action);
    setBulkProcessing(true);
    setBulkProgress(0);
    
    try {
      const total = selectedRowKeys.length;
      
      for (let i = 0; i < selectedRowKeys.length; i++) {
        const invoiceId = selectedRowKeys[i];
        
        switch (action) {
          case 'send':
            await apiClient.post(`/v1/billing/invoices/${invoiceId}/send/`);
            break;
          case 'mark_paid':
            await apiClient.patch(`/v1/billing/invoices/${invoiceId}/`, 
              { status: 'paid' }
            );
            break;
          case 'delete':
            await apiClient.delete(`/v1/billing/invoices/${invoiceId}/`);
            break;
          default:
            break;
        }
        
        setBulkProgress(Math.round(((i + 1) / total) * 100));
      }
      
      notification.success({
        message: 'Bulk Operation Completed',
        description: `Successfully processed ${selectedRowKeys.length} invoices.`,
        duration: 4
      });
      
      setSelectedRowKeys([]);
      fetchData({ pagination });
      
    } catch (error) {
      notification.error({
        message: 'Bulk Operation Failed',
        description: error.response?.data?.detail || 'Some operations may have failed.',
        duration: 6
      });
    } finally {
      setBulkProcessing(false);
      setBulkProgress(0);
      setBulkActionVisible(false);
    }
  };
  
  const handleExport = async (format = 'excel', includeAll = false) => {
    setExportLoading(true);
    try {
      const params = includeAll ? {} : { ids: selectedRowKeys.join(',') };
      
      if (!includeAll && !selectedRowKeys.length) {
        message.warning('Please select invoices to export or choose "Export All".');
        return;
      }
      
      const response = await apiClient.get('/v1/billing/invoices/export/', {
        params: { ...params, format, ...filters },
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const extension = format === 'excel' ? 'xlsx' : 'pdf';
      link.download = `invoices-${moment().format('YYYY-MM-DD')}.${extension}`;
      link.click();
      window.URL.revokeObjectURL(url);
      
      notification.success({
        message: 'Export Completed',
        description: `Invoices exported successfully to ${format.toUpperCase()}.`,
        duration: 3
      });
      
    } catch (error) {
      notification.error({
        message: 'Export Failed',
        description: 'Failed to export invoices. Please try again.',
        duration: 4
      });
    } finally {
      setExportLoading(false);
    }
  };
  
  const handleInvoiceAction = async (invoice, action) => {
    try {
      switch (action) {
        case 'send':
          await apiClient.post(`/v1/billing/invoices/${invoice.id}/send/`);
          message.success('Invoice sent successfully');
          break;
        case 'mark_paid':
          await apiClient.patch(`/v1/billing/invoices/${invoice.id}/`, { status: 'paid' });
          message.success('Invoice marked as paid');
          break;
        case 'download_pdf':
          const response = await apiClient.get(`/v1/billing/invoices/${invoice.id}/pdf/`, { responseType: 'blob' });
          const blob = new Blob([response.data], { type: 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `invoice-${invoice.id}.pdf`;
          link.click();
          window.URL.revokeObjectURL(url);
          message.success('PDF downloaded');
          return; // Skip fetch after download
        case 'delete':
          await apiClient.delete(`/v1/billing/invoices/${invoice.id}/`);
          message.success('Invoice deleted successfully');
          break;
        default:
          return;
      }
      
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Operation failed');
    }
  };
  
  const handlePreview = (invoice) => {
    setSelectedInvoice(invoice);
    setPreviewDrawerVisible(true);
  };

  const handleAdd = () => {
    setEditingInvoice(null);
    form.resetFields();
    form.setFieldsValue({ items: [{ description: '', quantity: 1, price: 0 }] });
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingInvoice(null);
  };

  const handleFormFinish = async (values) => {
    // For now, we only support creating manual invoices. Editing is more complex.
    const url = '/v1/billing/invoices/';
    const method = 'post';

    try {
      await apiClient[method](url, values);
      message.success(`Invoice created successfully.`);
      setIsModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to save invoice.`);
    }
  };

  // Enhanced columns with more information and actions
  const columns = [
    {
      title: 'Invoice #',
      dataIndex: 'number',
      key: 'number',
      width: 120,
      render: (text, record) => (
        <Button type="link" onClick={() => handlePreview(record)}>
          {text}
        </Button>
      ),
      sorter: true,
    },
    {
      title: 'Customer',
      dataIndex: ['customer', 'name'],
      key: 'customer',
      width: 200,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            ID: {record.customer?.id}
          </Text>
        </div>
      ),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Select
            style={{ width: 200, marginBottom: 8, display: 'block' }}
            placeholder="Select customer"
            value={selectedKeys[0]}
            onChange={value => setSelectedKeys(value ? [value] : [])}
            showSearch
            filterOption={(input, option) => 
              option.children.toLowerCase().includes(input.toLowerCase())
            }
          >
            {customers.map(customer => (
              <Option key={customer.id} value={customer.id}>
                {customer.name}
              </Option>
            ))}
          </Select>
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              size="small"
              style={{ width: 90 }}
            >
              Filter
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              Reset
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
    },
    {
      title: 'Date Created',
      dataIndex: 'date_created',
      key: 'date_created',
      width: 120,
      render: (text) => moment(text).format('MMM DD, YYYY'),
      sorter: true,
    },
    {
      title: 'Due Date',
      dataIndex: 'due_date',
      key: 'due_date',
      width: 120,
      render: (text, record) => {
        const dueDate = moment(text);
        const isOverdue = dueDate.isBefore(moment()) && record.status !== 'paid';
        return (
          <span style={{ color: isOverdue ? '#ff4d4f' : undefined }}>
            {dueDate.format('MMM DD, YYYY')}
            {isOverdue && <ExclamationCircleOutlined style={{ marginLeft: 4, color: '#ff4d4f' }} />}
          </span>
        );
      },
      sorter: true,
    },
    {
      title: 'Amount',
      dataIndex: 'total',
      key: 'total',
      width: 100,
      render: (text) => (
        <span style={{ fontWeight: 'bold' }}>
          ${Number(text || 0).toFixed(2)}
        </span>
      ),
      sorter: true,
    },
    {
      title: 'Due Amount',
      dataIndex: 'due',
      key: 'due',
      width: 100,
      render: (text, record) => {
        const amount = Number(text || 0);
        return (
          <span style={{ 
            fontWeight: 'bold',
            color: amount > 0 ? '#ff4d4f' : '#52c41a'
          }}>
            ${amount.toFixed(2)}
          </span>
        );
      },
      sorter: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => {
        const statusColors = {
          'draft': 'default',
          'sent': 'processing',
          'paid': 'success',
          'overdue': 'error',
          'void': 'warning',
          'partial': 'orange'
        };
        return (
          <Tag color={statusColors[status] || 'default'}>
            {status?.toUpperCase()}
          </Tag>
        );
      },
      filters: [
        { text: 'Draft', value: 'draft' },
        { text: 'Sent', value: 'sent' },
        { text: 'Paid', value: 'paid' },
        { text: 'Overdue', value: 'overdue' },
        { text: 'Void', value: 'void' },
        { text: 'Partial', value: 'partial' },
      ],
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => {
        const actionMenu = (
          <Menu onClick={({ key }) => handleInvoiceAction(record, key)}>
            <Menu.Item key="send" icon={<SendOutlined />}>
              Send Invoice
            </Menu.Item>
            <Menu.Item key="mark_paid" icon={<CheckCircleOutlined />}>
              Mark as Paid
            </Menu.Item>
            <Menu.Item key="download_pdf" icon={<FilePdfOutlined />}>
              Download PDF
            </Menu.Item>
            <Menu.Divider />
            <Menu.Item key="delete" icon={<DeleteOutlined />} danger>
              Delete Invoice
            </Menu.Item>
          </Menu>
        );
        
        return (
          <Space>
            <Tooltip title="Preview">
              <Button 
                type="text" 
                icon={<EyeOutlined />} 
                onClick={() => handlePreview(record)}
                size="small"
              />
            </Tooltip>
            <Dropdown overlay={actionMenu} trigger={['click']}>
              <Button type="text" icon={<MoreOutlined />} size="small" />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header with Title and Actions */}
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ margin: 0 }}>Invoices Management</Title>
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
              icon={<DownloadOutlined />} 
              onClick={() => handleExport('excel', false)}
              disabled={!selectedRowKeys.length}
              loading={exportLoading}
            >
              Export Selected
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleAdd}
            >
              Create Invoice
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats Cards */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Invoices"
              value={quickStats.total}
              prefix={<FileExcelOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Paid"
              value={quickStats.paid}
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
              title="Overdue"
              value={quickStats.overdue}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Search and Quick Filters */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col span={8}>
            <Input.Search
              placeholder="Search invoices..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              onSearch={() => fetchData({ pagination: { ...pagination, current: 1 } })}
              style={{ width: '100%' }}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Status"
              style={{ width: '100%' }}
              value={filters.status}
              onChange={(value) => setFilters(prev => ({ ...prev, status: value || [] }))}
              mode="multiple"
              allowClear
            >
              <Option value="draft">Draft</Option>
              <Option value="sent">Sent</Option>
              <Option value="paid">Paid</Option>
              <Option value="overdue">Overdue</Option>
              <Option value="void">Void</Option>
            </Select>
          </Col>
          <Col span={6}>
            <RangePicker
              style={{ width: '100%' }}
              value={filters.date_range}
              onChange={(dates) => setFilters(prev => ({ ...prev, date_range: dates || [] }))}
              placeholder={['Start Date', 'End Date']}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Customer"
              style={{ width: '100%' }}
              value={filters.customer_id}
              onChange={(value) => setFilters(prev => ({ ...prev, customer_id: value }))}
              showSearch
              allowClear
              filterOption={(input, option) => 
                option.children.toLowerCase().includes(input.toLowerCase())
              }
            >
              {customers.map(customer => (
                <Option key={customer.id} value={customer.id}>
                  {customer.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={2}>
            <Button 
              type="default" 
              onClick={handleFilterReset}
              block
            >
              Reset
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Bulk Actions Bar */}
      {selectedRowKeys.length > 0 && (
        <Alert
          message={
            <Row justify="space-between" align="middle">
              <Col>
                <Space>
                  <Text strong>{selectedRowKeys.length} invoice(s) selected</Text>
                  <Button size="small" onClick={() => setSelectedRowKeys([])}>
                    Clear Selection
                  </Button>
                </Space>
              </Col>
              <Col>
                <Space>
                  <Button 
                    size="small" 
                    icon={<SendOutlined />}
                    onClick={() => handleBulkAction('send')}
                    loading={bulkProcessing && bulkOperation === 'send'}
                  >
                    Send All
                  </Button>
                  <Button 
                    size="small" 
                    icon={<CheckCircleOutlined />}
                    onClick={() => handleBulkAction('mark_paid')}
                    loading={bulkProcessing && bulkOperation === 'mark_paid'}
                  >
                    Mark as Paid
                  </Button>
                  <Button 
                    size="small" 
                    icon={<DownloadOutlined />}
                    onClick={() => handleExport('excel', false)}
                    loading={exportLoading}
                  >
                    Export
                  </Button>
                  <Popconfirm
                    title="Are you sure you want to delete selected invoices?"
                    onConfirm={() => handleBulkAction('delete')}
                    okText="Yes"
                    cancelText="No"
                  >
                    <Button 
                      size="small" 
                      danger 
                      icon={<DeleteOutlined />}
                      loading={bulkProcessing && bulkOperation === 'delete'}
                    >
                      Delete
                    </Button>
                  </Popconfirm>
                </Space>
              </Col>
            </Row>
          }
          type="info"
          style={{ marginBottom: '16px' }}
        />
      )}

      {/* Bulk Progress */}
      {bulkProcessing && (
        <Card style={{ marginBottom: '16px' }}>
          <div>
            <Text strong>Processing {bulkOperation}...</Text>
            <Progress percent={bulkProgress} status="active" style={{ marginTop: '8px' }} />
          </div>
        </Card>
      )}
      {/* Enhanced Table */}
      <Card>
        <Table
          dataSource={invoices}
          columns={columns}
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
            selections: [
              Table.SELECTION_ALL,
              Table.SELECTION_INVERT,
              Table.SELECTION_NONE,
            ],
          }}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* Create/Edit Invoice Modal */}
      <Modal
        title={editingInvoice ? 'Edit Invoice' : 'Create Manual Invoice'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnHidden
        width={900}
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
                <Select 
                  showSearch 
                  placeholder="Select a customer" 
                  filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}
                >
                  {customers.map(c => <Option key={c.id} value={c.id}>{c.name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="due_date" label="Due Date" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Invoice Items</Divider>
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={16} style={{ marginBottom: 16 }}>
                    <Col span={10}>
                      <Form.Item 
                        {...restField} 
                        name={[name, 'description']} 
                        rules={[{ required: true, message: 'Missing description' }]}
                        label="Description"
                      >
                        <Input placeholder="Service or product description" />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item 
                        {...restField} 
                        name={[name, 'quantity']} 
                        rules={[{ required: true, message: 'Missing quantity' }]}
                        label="Qty"
                      >
                        <InputNumber placeholder="1" min={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={5}>
                      <Form.Item 
                        {...restField} 
                        name={[name, 'price']} 
                        rules={[{ required: true, message: 'Missing price' }]}
                        label="Unit Price"
                      >
                        <InputNumber 
                          placeholder="0.00" 
                          min={0} 
                          step="0.01" 
                          style={{ width: '100%' }}
                          formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                          parser={value => value.replace(/\$\s?|(,*)/g, '')}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item label="Total">
                        <Text strong>
                          ${((form.getFieldValue(['items', name, 'quantity']) || 0) * 
                             (form.getFieldValue(['items', name, 'price']) || 0)).toFixed(2)}
                        </Text>
                      </Form.Item>
                    </Col>
                    <Col span={1}>
                      <Form.Item label=" ">
                        <Button 
                          type="text" 
                          danger 
                          icon={<DeleteOutlined />} 
                          onClick={() => remove(name)}
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                ))}
                <Form.Item>
                  <Button 
                    type="dashed" 
                    onClick={() => add({ description: '', quantity: 1, price: 0 })} 
                    block 
                    icon={<PlusOutlined />}
                    style={{ marginTop: 16 }}
                  >
                    Add Invoice Item
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="note" label="Notes (visible to customer)">
                <TextArea rows={3} placeholder="Additional notes or terms..." />
              </Form.Item>
            </Col>
          </Row>

          <Row justify="end">
            <Col>
              <Space>
                <Button onClick={handleModalCancel}>Cancel</Button>
                <Button type="primary" htmlType="submit">
                  {editingInvoice ? 'Update Invoice' : 'Create Invoice'}
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Advanced Filters Drawer */}
      <Drawer
        title="Advanced Filters"
        placement="right"
        onClose={() => setFilterDrawerVisible(false)}
        visible={filterDrawerVisible}
        width={400}
      >
        <Form layout="vertical">
          <Form.Item label="Amount Range">
            <Row gutter={8}>
              <Col span={12}>
                <InputNumber
                  placeholder="Min"
                  style={{ width: '100%' }}
                  value={filters.amount_range[0]}
                  onChange={(value) => setFilters(prev => ({
                    ...prev,
                    amount_range: [value, prev.amount_range[1]]
                  }))}
                />
              </Col>
              <Col span={12}>
                <InputNumber
                  placeholder="Max"
                  style={{ width: '100%' }}
                  value={filters.amount_range[1]}
                  onChange={(value) => setFilters(prev => ({
                    ...prev,
                    amount_range: [prev.amount_range[0], value]
                  }))}
                />
              </Col>
            </Row>
          </Form.Item>
          
          <Form.Item label="Due Date Range">
            <RangePicker
              style={{ width: '100%' }}
              value={filters.due_date_range}
              onChange={(dates) => setFilters(prev => ({ ...prev, due_date_range: dates || [] }))}
            />
          </Form.Item>
          
          <Form.Item label="Payment Status">
            <Checkbox.Group
              value={filters.payment_status}
              onChange={(values) => setFilters(prev => ({ ...prev, payment_status: values }))}
            >
              <Row>
                <Col span={24}><Checkbox value="fully_paid">Fully Paid</Checkbox></Col>
                <Col span={24}><Checkbox value="partially_paid">Partially Paid</Checkbox></Col>
                <Col span={24}><Checkbox value="unpaid">Unpaid</Checkbox></Col>
                <Col span={24}><Checkbox value="refunded">Refunded</Checkbox></Col>
              </Row>
            </Checkbox.Group>
          </Form.Item>
        </Form>
        
        <div style={{ position: 'absolute', bottom: 0, width: '100%', borderTop: '1px solid #e9e9e9', padding: '10px 16px', background: '#fff', textAlign: 'right' }}>
          <Space>
            <Button onClick={() => setFilterDrawerVisible(false)}>Cancel</Button>
            <Button onClick={handleFilterReset}>Reset</Button>
            <Button type="primary" onClick={() => handleFilterApply(filters)}>Apply Filters</Button>
          </Space>
        </div>
      </Drawer>

      {/* Invoice Preview Drawer */}
      <Drawer
        title={`Invoice ${selectedInvoice?.number || ''}`}
        placement="right"
        onClose={() => setPreviewDrawerVisible(false)}
        visible={previewDrawerVisible}
        width={600}
      >
        {selectedInvoice && (
          <div>
            <Card title="Invoice Details" style={{ marginBottom: 16 }}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Text strong>Customer:</Text>
                  <div>{selectedInvoice.customer?.name}</div>
                </Col>
                <Col span={12}>
                  <Text strong>Status:</Text>
                  <div>
                    <Tag color={selectedInvoice.status === 'paid' ? 'success' : 'warning'}>
                      {selectedInvoice.status?.toUpperCase()}
                    </Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <Text strong>Date Created:</Text>
                  <div>{moment(selectedInvoice.date_created).format('MMMM DD, YYYY')}</div>
                </Col>
                <Col span={12}>
                  <Text strong>Due Date:</Text>
                  <div>{moment(selectedInvoice.due_date).format('MMMM DD, YYYY')}</div>
                </Col>
                <Col span={12}>
                  <Text strong>Total Amount:</Text>
                  <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                    ${Number(selectedInvoice.total || 0).toFixed(2)}
                  </div>
                </Col>
                <Col span={12}>
                  <Text strong>Amount Due:</Text>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#ff4d4f' }}>
                    ${Number(selectedInvoice.due || 0).toFixed(2)}
                  </div>
                </Col>
              </Row>
            </Card>
            
            <Card title="Quick Actions">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button 
                  type="primary" 
                  icon={<SendOutlined />} 
                  block
                  onClick={() => handleInvoiceAction(selectedInvoice, 'send')}
                >
                  Send Invoice
                </Button>
                <Button 
                  icon={<DownloadOutlined />} 
                  block
                  onClick={() => handleExport('pdf', false)}
                >
                  Download PDF
                </Button>
                <Button 
                  icon={<PrinterOutlined />} 
                  block
                  onClick={() => window.print()}
                >
                  Print Invoice
                </Button>
              </Space>
            </Card>
          </div>
        )}
      </Drawer>
    </div>
  );
}

export default InvoicesPage;