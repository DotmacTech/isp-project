import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  InputNumber,
  DatePicker,
  message,
  Space,
  Popconfirm,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Alert,
  Drawer,
  Divider,
  Checkbox,
  Badge,
  Progress,
  notification,
  Steps,
  Radio,
  Tabs,
  Upload,
  Empty,
  Descriptions,
  Typography
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  DollarOutlined,
  CalendarOutlined,
  CopyOutlined,
  FileTextOutlined,
  AppstoreOutlined,
  FilterOutlined,
  ExportOutlined,
  ImportOutlined,
  SaveOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined,
  UploadOutlined
} from '@ant-design/icons';
import { customerBillingConfigAPI, billingCyclesAPI, customersAPI } from '../../services/billingAPI';
import moment from 'moment';
import EnhancedTable from '../common/EnhancedTable';

const { Option } = Select;
const { Step } = Steps;
const { TabPane } = Tabs;
const { Text, Title } = Typography;
const { Dragger } = Upload;

const CustomerBillingConfigPage = () => {
  const [loading, setLoading] = useState(false);
  const [configs, setConfigs] = useState([]);
  const [filteredConfigs, setFilteredConfigs] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [billingCycles, setBillingCycles] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [form] = Form.useForm();
  const [templateForm] = Form.useForm();
  const [bulkForm] = Form.useForm();
  const [statistics, setStatistics] = useState({
    totalConfigs: 0,
    activeConfigs: 0,
    customCycles: 0,
    avgProrationEnabled: 0
  });

  // New state for enhanced features
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [bulkModalVisible, setBulkModalVisible] = useState(false);
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [templatesDrawerVisible, setTemplatesDrawerVisible] = useState(false);
  const [validationResults, setValidationResults] = useState({});
  const [searchText, setSearchText] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [bulkUpdateStep, setBulkUpdateStep] = useState(0);
  const [bulkUpdateProgress, setBulkUpdateProgress] = useState(0);
  const [configTemplates, setConfigTemplates] = useState([
    {
      id: 'standard_monthly',
      name: 'Standard Monthly',
      description: 'Standard monthly billing configuration for regular customers',
      config: {
        billing_due_day: 1,
        payment_terms_days: 30,
        grace_period_days: 5,
        credit_limit: 1000,
        late_fee_percentage: 5,
        late_fee_fixed_amount: 25,
        is_active: true,
        enable_proration: true,
        auto_pay: false,
        late_fee_enabled: true
      }
    },
    {
      id: 'premium_customer',
      name: 'Premium Customer',
      description: 'Premium billing configuration with extended credit and terms',
      config: {
        billing_due_day: 15,
        payment_terms_days: 45,
        grace_period_days: 10,
        credit_limit: 5000,
        late_fee_percentage: 3,
        late_fee_fixed_amount: 0,
        is_active: true,
        enable_proration: true,
        auto_pay: true,
        late_fee_enabled: true
      }
    },
    {
      id: 'small_business',
      name: 'Small Business',
      description: 'Small business billing configuration with flexible terms',
      config: {
        billing_due_day: 30,
        payment_terms_days: 60,
        grace_period_days: 15,
        credit_limit: 2500,
        late_fee_percentage: 4,
        late_fee_fixed_amount: 50,
        is_active: true,
        enable_proration: true,
        auto_pay: false,
        late_fee_enabled: true
      }
    }
  ]);

  // Enhanced data filtering and search
  const filteredData = useMemo(() => {
    let filtered = configs;
    
    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(config => {
        switch (filterStatus) {
          case 'active':
            return config.is_active;
          case 'inactive':
            return !config.is_active;
          case 'auto_pay':
            return config.auto_pay;
          case 'overdue_protection':
            return config.late_fee_enabled;
          default:
            return true;
        }
      });
    }
    
    // Apply search filter
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(config => 
        config.customer?.name?.toLowerCase().includes(searchLower) ||
        config.customer?.email?.toLowerCase().includes(searchLower) ||
        config.billing_cycle?.name?.toLowerCase().includes(searchLower)
      );
    }
    
    return filtered;
  }, [configs, filterStatus, searchText]);

  // Enhanced validation logic
  const validateConfiguration = useCallback((config) => {
    const errors = [];
    const warnings = [];
    
    // Required field validation
    if (!config.customer_id) errors.push('Customer is required');
    if (!config.billing_cycle_id) errors.push('Billing cycle is required');
    if (!config.billing_due_day || config.billing_due_day < 1 || config.billing_due_day > 31) {
      errors.push('Billing due day must be between 1 and 31');
    }
    
    // Business logic validation
    if (config.payment_terms_days < config.grace_period_days) {
      warnings.push('Grace period should not exceed payment terms');
    }
    
    if (config.late_fee_enabled && !config.late_fee_percentage && !config.late_fee_fixed_amount) {
      warnings.push('Late fees enabled but no fee amount specified');
    }
    
    if (config.credit_limit > 10000) {
      warnings.push('High credit limit - consider approval workflow');
    }
    
    if (config.payment_terms_days > 90) {
      warnings.push('Extended payment terms may impact cash flow');
    }
    
    return { errors, warnings, isValid: errors.length === 0 };
  }, []);

  // Bulk operations logic
  const handleBulkUpdate = useCallback(async (updateData) => {
    setBulkUpdateProgress(0);
    const totalConfigs = selectedRowKeys.length;
    let successCount = 0;
    let errorCount = 0;
    
    for (let i = 0; i < selectedRowKeys.length; i++) {
      try {
        await customerBillingConfigAPI.update(selectedRowKeys[i], updateData);
        successCount++;
      } catch (error) {
        errorCount++;
        console.error(`Failed to update config ${selectedRowKeys[i]}:`, error);
      }
      
      setBulkUpdateProgress(Math.round(((i + 1) / totalConfigs) * 100));
    }
    
    notification.success({
      message: 'Bulk Update Complete',
      description: `Successfully updated ${successCount} configurations. ${errorCount} failed.`,
      duration: 5
    });
    
    setBulkModalVisible(false);
    setSelectedRowKeys([]);
    setBulkUpdateStep(0);
    setBulkUpdateProgress(0);
    fetchAllData();
  }, [selectedRowKeys]);

  // Template application logic
  const applyTemplate = useCallback((template) => {
    form.setFieldsValue(template.config);
    setTemplatesDrawerVisible(false);
    message.success(`Applied template: ${template.name}`);
  }, [form]);

  // Export/Import logic
  const handleExportConfigs = useCallback(() => {
    const exportData = selectedRowKeys.length > 0 
      ? configs.filter(config => selectedRowKeys.includes(config.customer_id))
      : configs;
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `billing-configs-${moment().format('YYYY-MM-DD')}.json`;
    link.click();
    URL.revokeObjectURL(url);
    
    message.success(`Exported ${exportData.length} configurations`);
  }, [configs, selectedRowKeys]);

  // Enhanced data fetching with validation
  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [configsRes, customersRes, cyclesRes] = await Promise.all([
        customerBillingConfigAPI.getAll(),
        customersAPI.getAll(),
        billingCyclesAPI.getAll()
      ]);
      
      const configsData = configsRes.data;
      setConfigs(configsData);
      setCustomers(customersRes.data);
      setBillingCycles(cyclesRes.data);
      
      // Enhanced statistics calculation
      const stats = {
        totalConfigs: configsData.length,
        activeConfigs: configsData.filter(c => c.is_active).length,
        customCycles: configsData.filter(c => c.billing_cycle?.cycle_type === 'custom').length,
        avgProrationEnabled: configsData.filter(c => c.enable_proration).length
      };
      setStatistics(stats);
      
      // Validate all configurations
      const validationResults = {};
      configsData.forEach(config => {
        validationResults[config.customer_id] = validateConfiguration(config);
      });
      setValidationResults(validationResults);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      message.error('Failed to load billing configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingConfig(null);
    form.resetFields();
    // Set default values
    form.setFieldsValue({
      is_active: true,
      enable_proration: true,
      auto_pay: false,
      late_fee_enabled: true,
      late_fee_percentage: 5,
      grace_period_days: 5,
      payment_terms_days: 30
    });
    setModalVisible(true);
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    form.setFieldsValue({
      ...config,
      billing_due_day: config.billing_due_day,
      late_fee_percentage: config.late_fee_percentage ? parseFloat(config.late_fee_percentage) : 5,
      late_fee_fixed_amount: config.late_fee_fixed_amount ? parseFloat(config.late_fee_fixed_amount) : 0,
      credit_limit: config.credit_limit ? parseFloat(config.credit_limit) : 0,
      payment_terms_days: config.payment_terms_days || 30,
      grace_period_days: config.grace_period_days || 5
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values) => {
    // Enhanced validation before submit
    const validation = validateConfiguration(values);
    if (!validation.isValid) {
      notification.error({
        message: 'Validation Failed',
        description: validation.errors.join(', '),
        duration: 5
      });
      return;
    }
    
    if (validation.warnings.length > 0) {
      Modal.confirm({
        title: 'Configuration Warnings',
        content: (
          <div>
            <p>The following warnings were detected:</p>
            <ul>
              {validation.warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
            <p>Do you want to continue?</p>
          </div>
        ),
        onOk: () => submitConfiguration(values),
        okText: 'Continue',
        cancelText: 'Review'
      });
    } else {
      await submitConfiguration(values);
    }
  };

  const submitConfiguration = async (values) => {
    setLoading(true);
    try {
      if (editingConfig) {
        await customerBillingConfigAPI.update(editingConfig.customer_id, values);
        message.success('Billing configuration updated successfully');
      } else {
        await customerBillingConfigAPI.create(values);
        message.success('Billing configuration created successfully');
      }
      setModalVisible(false);
      fetchAllData();
    } catch (error) {
      console.error('Error saving configuration:', error);
      message.error('Failed to save billing configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (customerId) => {
    setLoading(true);
    try {
      await customerBillingConfigAPI.delete(customerId);
      message.success('Billing configuration deleted successfully');
      fetchAllData();
    } catch (error) {
      console.error('Error deleting configuration:', error);
      message.error('Failed to delete billing configuration');
    } finally {
      setLoading(false);
    }
  };

  // New handlers for enhanced features
  const handleBulkAction = (action) => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select configurations to update');
      return;
    }
    
    setBulkUpdateStep(0);
    setBulkModalVisible(true);
  };

  const handleCreateTemplate = () => {
    templateForm.resetFields();
    setTemplateModalVisible(true);
  };

  const handleSaveTemplate = async (values) => {
    const newTemplate = {
      id: `template_${Date.now()}`,
      name: values.name,
      description: values.description,
      config: form.getFieldsValue()
    };
    
    const updatedTemplates = [...configTemplates, newTemplate];
    setConfigTemplates(updatedTemplates);
    setTemplateModalVisible(false);
    message.success('Template saved successfully');
  };

  const handleDuplicateConfig = (config) => {
    const duplicatedConfig = { ...config };
    delete duplicatedConfig.customer_id;
    delete duplicatedConfig.id;
    
    form.setFieldsValue(duplicatedConfig);
    setEditingConfig(null);
    setModalVisible(true);
    message.info('Configuration duplicated. Select a customer to create.');
  };

  const columns = [
    {
      title: 'Customer',
      dataIndex: 'customer',
      key: 'customer',
      fixed: 'left',
      width: 200,
      render: (customer, record) => {
        const validation = validationResults[record.customer_id] || { errors: [], warnings: [] };
        return (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div>
                <div style={{ fontWeight: 'bold' }}>{customer?.name}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>{customer?.email}</div>
              </div>
              {validation.errors.length > 0 && (
                <Tooltip title={validation.errors.join(', ')}>
                  <Badge status="error" />
                </Tooltip>
              )}
              {validation.warnings.length > 0 && (
                <Tooltip title={validation.warnings.join(', ')}>
                  <Badge status="warning" />
                </Tooltip>
              )}
            </div>
          </div>
        );
      },
    },
    {
      title: 'Billing Cycle',
      dataIndex: 'billing_cycle',
      key: 'billing_cycle',
      width: 150,
      render: (cycle) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{cycle?.name}</div>
          <Tag color={cycle?.cycle_type === 'custom' ? 'purple' : 'blue'}>
            {cycle?.cycle_type?.toUpperCase()}
          </Tag>
        </div>
      ),
    },
    {
      title: 'Due Day',
      dataIndex: 'billing_due_day',
      key: 'billing_due_day',
      width: 100,
      render: (day) => (
        <Tag color="orange" icon={<CalendarOutlined />}>
          Day {day}
        </Tag>
      ),
    },
    {
      title: 'Payment Terms',
      dataIndex: 'payment_terms_days',
      key: 'payment_terms_days',
      width: 120,
      render: (days, record) => (
        <div>
          <div>{days} days</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            Grace: {record.grace_period_days} days
          </div>
        </div>
      ),
    },
    {
      title: 'Credit Limit',
      dataIndex: 'credit_limit',
      key: 'credit_limit',
      width: 120,
      render: (amount) => (
        <span style={{ 
          color: amount > 5000 ? '#f5222d' : amount > 1000 ? '#fa8c16' : '#1890ff', 
          fontWeight: 'bold' 
        }}>
          ${parseFloat(amount || 0).toLocaleString()}
        </span>
      ),
    },
    {
      title: 'Late Fees',
      key: 'late_fees',
      width: 120,
      render: (_, record) => {
        if (!record.late_fee_enabled) {
          return <Tag color="default">Disabled</Tag>;
        }
        return (
          <div>
            {record.late_fee_percentage > 0 && (
              <Tag color="orange">{record.late_fee_percentage}%</Tag>
            )}
            {record.late_fee_fixed_amount > 0 && (
              <Tag color="red">${record.late_fee_fixed_amount}</Tag>
            )}
          </div>
        );
      },
    },
    {
      title: 'Status & Features',
      key: 'features',
      width: 180,
      render: (_, record) => (
        <Space size={[0, 4]} wrap>
          <Tag color={record.is_active ? 'green' : 'red'}>
            {record.is_active ? 'Active' : 'Inactive'}
          </Tag>
          {record.enable_proration && <Tag color="blue">Pro-rating</Tag>}
          {record.auto_pay && (
            <Tag color="purple" icon={<CheckCircleOutlined />}>
              Auto Pay
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space>
          <Tooltip title="Edit Configuration">
            <Button
              type="primary"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="Duplicate Configuration">
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleDuplicateConfig(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete this billing configuration?"
            description="This action cannot be undone."
            onConfirm={() => handleDelete(record.customer_id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete Configuration">
              <Button
                type="primary"
                danger
                size="small"
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Row selection configuration
  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
    getCheckboxProps: (record) => ({
      disabled: !record.is_active,
      name: record.customer?.name,
    }),
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Enhanced Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Configurations"
              value={statistics.totalConfigs}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Configurations"
              value={statistics.activeConfigs}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Custom Cycles"
              value={statistics.customCycles}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Pro-rating Enabled"
              value={statistics.avgProrationEnabled}
              prefix={<InfoCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Enhanced Controls and Filters */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col span={8}>
            <Input.Search
              placeholder="Search customers, emails, or billing cycles..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col span={6}>
            <Select
              placeholder="Filter by status"
              value={filterStatus}
              onChange={setFilterStatus}
              style={{ width: '100%' }}
            >
              <Option value="all">All Configurations</Option>
              <Option value="active">Active Only</Option>
              <Option value="inactive">Inactive Only</Option>
              <Option value="auto_pay">Auto Pay Enabled</Option>
              <Option value="overdue_protection">Late Fees Enabled</Option>
            </Select>
          </Col>
          <Col span={10}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleCreate}
              >
                Add Configuration
              </Button>
              <Button
                icon={<FileTextOutlined />}
                onClick={() => setTemplatesDrawerVisible(true)}
              >
                Templates
              </Button>
              <Button
                icon={<AppstoreOutlined />}
                onClick={handleBulkAction}
                disabled={selectedRowKeys.length === 0}
              >
                Bulk Update ({selectedRowKeys.length})
              </Button>
              <Button
                icon={<ExportOutlined />}
                onClick={handleExportConfigs}
              >
                Export
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchAllData}
                loading={loading}
              >
                Refresh
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Enhanced Table */}
      <Card
        title={(
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Customer Billing Configurations</span>
            <Badge count={filteredData.length} showZero color="blue" />
          </div>
        )}
      >
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey="customer_id"
          loading={loading}
          rowSelection={rowSelection}
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} configurations`,
          }}
        />
      </Card>

      {/* Enhanced Configuration Modal */}
      <Modal
        title={(
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{editingConfig ? 'Edit Billing Configuration' : 'Create Billing Configuration'}</span>
            <Button
              size="small"
              icon={<SaveOutlined />}
              onClick={handleCreateTemplate}
            >
              Save as Template
            </Button>
          </div>
        )}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={900}
      >
        <Tabs defaultActiveKey="basic">
          <TabPane tab="Basic Configuration" key="basic">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="customer_id"
                    label="Customer"
                    rules={[{ required: true, message: 'Please select a customer' }]}
                  >
                    <Select
                      placeholder="Select customer"
                      disabled={!!editingConfig}
                      showSearch
                      filterOption={(input, option) =>
                        option.children.toLowerCase().includes(input.toLowerCase())
                      }
                    >
                      {customers.map(customer => (
                        <Option key={customer.id} value={customer.id}>
                          {customer.name} ({customer.email})
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="billing_cycle_id"
                    label="Billing Cycle"
                    rules={[{ required: true, message: 'Please select a billing cycle' }]}
                  >
                    <Select placeholder="Select billing cycle">
                      {billingCycles.map(cycle => (
                        <Option key={cycle.id} value={cycle.id}>
                          {cycle.name} ({cycle.cycle_type})
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="billing_due_day"
                    label="Billing Due Day"
                    rules={[
                      { required: true, message: 'Please set billing due day' },
                      { type: 'number', min: 1, max: 31, message: 'Must be between 1 and 31' }
                    ]}
                  >
                    <InputNumber
                      min={1}
                      max={31}
                      placeholder="Day of month"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="payment_terms_days"
                    label="Payment Terms (Days)"
                    rules={[
                      { required: true, message: 'Please set payment terms' },
                      { type: 'number', min: 1, max: 365, message: 'Must be between 1 and 365' }
                    ]}
                  >
                    <InputNumber
                      min={1}
                      max={365}
                      placeholder="Days"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="grace_period_days"
                    label="Grace Period (Days)"
                    rules={[
                      { required: true, message: 'Please set grace period' },
                      { type: 'number', min: 0, max: 30, message: 'Must be between 0 and 30' }
                    ]}
                  >
                    <InputNumber
                      min={0}
                      max={30}
                      placeholder="Days"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="credit_limit"
                    label="Credit Limit ($)"
                    rules={[{ type: 'number', min: 0, message: 'Must be non-negative' }]}
                  >
                    <InputNumber
                      min={0}
                      step={100}
                      placeholder="0.00"
                      style={{ width: '100%' }}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="late_fee_percentage"
                    label="Late Fee (%)"
                    rules={[{ type: 'number', min: 0, max: 100, message: 'Must be between 0 and 100' }]}
                  >
                    <InputNumber
                      min={0}
                      max={100}
                      step={0.5}
                      placeholder="5.0"
                      style={{ width: '100%' }}
                      formatter={value => `${value}%`}
                      parser={value => value.replace('%', '')}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="late_fee_fixed_amount"
                    label="Late Fee Fixed ($)"
                    rules={[{ type: 'number', min: 0, message: 'Must be non-negative' }]}
                  >
                    <InputNumber
                      min={0}
                      step={5}
                      placeholder="0.00"
                      style={{ width: '100%' }}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Alert
                message="Configuration Options"
                description="These settings control how billing is processed for this customer."
                type="info"
                style={{ marginBottom: '16px' }}
              />

              <Row gutter={16}>
                <Col span={6}>
                  <Form.Item
                    name="is_active"
                    label="Active"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="enable_proration"
                    label="Enable Pro-rating"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="auto_pay"
                    label="Auto Pay"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    name="late_fee_enabled"
                    label="Late Fees"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="notification_email"
                label="Notification Email"
                rules={[{ type: 'email', message: 'Please enter a valid email' }]}
              >
                <Input placeholder="Override default email for billing notifications" />
              </Form.Item>

              <Form.Item
                name="notes"
                label="Notes"
              >
                <Input.TextArea
                  rows={3}
                  placeholder="Additional notes about this billing configuration"
                />
              </Form.Item>

              <div style={{ textAlign: 'right' }}>
                <Space>
                  <Button onClick={() => setModalVisible(false)}>
                    Cancel
                  </Button>
                  <Button 
                    icon={<FileTextOutlined />}
                    onClick={() => setTemplatesDrawerVisible(true)}
                  >
                    Use Template
                  </Button>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    {editingConfig ? 'Update' : 'Create'} Configuration
                  </Button>
                </Space>
              </div>
            </Form>
          </TabPane>
          
          <TabPane tab="Validation" key="validation">
            <div>
              {editingConfig && validationResults[editingConfig.customer_id] ? (
                <div>
                  <Title level={4}>Configuration Validation</Title>
                  <Descriptions bordered column={1}>
                    <Descriptions.Item label="Validation Status">
                      {validationResults[editingConfig.customer_id].isValid ? (
                        <Badge status="success" text="Valid Configuration" />
                      ) : (
                        <Badge status="error" text="Has Validation Errors" />
                      )}
                    </Descriptions.Item>
                    
                    {validationResults[editingConfig.customer_id].errors.length > 0 && (
                      <Descriptions.Item label="Errors">
                        <ul style={{ color: '#ff4d4f', margin: 0 }}>
                          {validationResults[editingConfig.customer_id].errors.map((error, index) => (
                            <li key={index}>{error}</li>
                          ))}
                        </ul>
                      </Descriptions.Item>
                    )}
                    
                    {validationResults[editingConfig.customer_id].warnings.length > 0 && (
                      <Descriptions.Item label="Warnings">
                        <ul style={{ color: '#fa8c16', margin: 0 }}>
                          {validationResults[editingConfig.customer_id].warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                          ))}
                        </ul>
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </div>
              ) : (
                <Empty 
                  description="Create or edit a configuration to see validation results" 
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              )}
            </div>
          </TabPane>
        </Tabs>
      </Modal>

      {/* Templates Drawer */}
      <Drawer
        title="Configuration Templates"
        placement="right"
        width={500}
        open={templatesDrawerVisible}
        onClose={() => setTemplatesDrawerVisible(false)}
      >
        <div style={{ marginBottom: '16px' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateTemplate}
            style={{ width: '100%' }}
          >
            Create New Template
          </Button>
        </div>
        
        <div>
          {configTemplates.map(template => (
            <Card
              key={template.id}
              size="small"
              title={template.name}
              style={{ marginBottom: '12px' }}
              actions={[
                <Button
                  type="link"
                  icon={<CheckCircleOutlined />}
                  onClick={() => applyTemplate(template)}
                >
                  Apply
                </Button>
              ]}
            >
              <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
                {template.description}
              </p>
              <div style={{ marginTop: '8px' }}>
                <Space size={[0, 4]} wrap>
                  <Tag>Due Day: {template.config.billing_due_day}</Tag>
                  <Tag>Terms: {template.config.payment_terms_days}d</Tag>
                  <Tag color={template.config.auto_pay ? 'green' : 'default'}>
                    {template.config.auto_pay ? 'Auto Pay' : 'Manual'}
                  </Tag>
                </Space>
              </div>
            </Card>
          ))}
        </div>
      </Drawer>

      {/* Template Creation Modal */}
      <Modal
        title="Create Configuration Template"
        open={templateModalVisible}
        onCancel={() => setTemplateModalVisible(false)}
        footer={null}
        width={400}
      >
        <Form
          form={templateForm}
          layout="vertical"
          onFinish={handleSaveTemplate}
        >
          <Form.Item
            name="name"
            label="Template Name"
            rules={[{ required: true, message: 'Please enter template name' }]}
          >
            <Input placeholder="e.g., Enterprise Customer" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="Describe when to use this template..."
            />
          </Form.Item>
          
          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setTemplateModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                Save Template
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>

      {/* Bulk Update Modal */}
      <Modal
        title="Bulk Update Configurations"
        open={bulkModalVisible}
        onCancel={() => setBulkModalVisible(false)}
        footer={null}
        width={600}
      >
        <Steps current={bulkUpdateStep} style={{ marginBottom: '24px' }}>
          <Step title="Select Fields" description="Choose what to update" />
          <Step title="Set Values" description="Configure new values" />
          <Step title="Confirm" description="Review and apply" />
        </Steps>
        
        {bulkUpdateProgress > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <Progress percent={bulkUpdateProgress} status="active" />
          </div>
        )}
        
        <Form
          form={bulkForm}
          layout="vertical"
          onFinish={(values) => {
            if (bulkUpdateStep === 2) {
              handleBulkUpdate(values);
            } else {
              setBulkUpdateStep(bulkUpdateStep + 1);
            }
          }}
        >
          {bulkUpdateStep === 0 && (
            <div>
              <Alert
                message="Select Fields to Update"
                description={`You are updating ${selectedRowKeys.length} configurations. Choose which fields to modify.`}
                type="info"
                style={{ marginBottom: '16px' }}
              />
              
              <Form.Item name="fieldsToUpdate" label="Fields to Update">
                <Checkbox.Group
                  options={[
                    { label: 'Payment Terms', value: 'payment_terms_days' },
                    { label: 'Grace Period', value: 'grace_period_days' },
                    { label: 'Credit Limit', value: 'credit_limit' },
                    { label: 'Late Fee Percentage', value: 'late_fee_percentage' },
                    { label: 'Auto Pay Setting', value: 'auto_pay' },
                    { label: 'Pro-rating Setting', value: 'enable_proration' },
                    { label: 'Active Status', value: 'is_active' }
                  ]}
                />
              </Form.Item>
            </div>
          )}
          
          {bulkUpdateStep === 1 && (
            <div>
              <Alert
                message="Set New Values"
                description="Configure the new values for selected fields."
                type="info"
                style={{ marginBottom: '16px' }}
              />
              
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="payment_terms_days" label="Payment Terms (Days)">
                    <InputNumber min={1} max={365} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="grace_period_days" label="Grace Period (Days)">
                    <InputNumber min={0} max={30} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="credit_limit" label="Credit Limit ($)">
                    <InputNumber 
                      min={0} 
                      step={100} 
                      style={{ width: '100%' }}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="late_fee_percentage" label="Late Fee (%)">
                    <InputNumber 
                      min={0} 
                      max={100} 
                      step={0.5} 
                      style={{ width: '100%' }}
                      formatter={value => `${value}%`}
                      parser={value => value.replace('%', '')}
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="auto_pay" label="Auto Pay" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="enable_proration" label="Pro-rating" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="is_active" label="Active" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
            </div>
          )}
          
          {bulkUpdateStep === 2 && (
            <div>
              <Alert
                message="Confirm Bulk Update"
                description={`This will update ${selectedRowKeys.length} configurations. This action cannot be undone.`}
                type="warning"
                style={{ marginBottom: '16px' }}
              />
              
              <Descriptions title="Update Summary" bordered column={1}>
                <Descriptions.Item label="Configurations to Update">
                  {selectedRowKeys.length}
                </Descriptions.Item>
                <Descriptions.Item label="Selected Customers">
                  {configs
                    .filter(config => selectedRowKeys.includes(config.customer_id))
                    .map(config => config.customer?.name)
                    .join(', ')}
                </Descriptions.Item>
              </Descriptions>
            </div>
          )}
          
          <div style={{ textAlign: 'right', marginTop: '24px' }}>
            <Space>
              {bulkUpdateStep > 0 && (
                <Button onClick={() => setBulkUpdateStep(bulkUpdateStep - 1)}>
                  Previous
                </Button>
              )}
              <Button onClick={() => setBulkModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {bulkUpdateStep === 2 ? 'Apply Updates' : 'Next'}
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default CustomerBillingConfigPage;