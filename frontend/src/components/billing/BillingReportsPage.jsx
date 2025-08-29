import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Form,
  Select,
  DatePicker,
  message,
  Space,
  Row,
  Col,
  Statistic,
  Table,
  Descriptions,
  Modal,
  Tabs,
  Tag,
  Progress,
  Alert,
  Spin
} from 'antd';
import {
  FileExcelOutlined,
  FilePdfOutlined,
  BarChartOutlined,
  DollarOutlined,
  CalendarOutlined,
  UserOutlined,
  DownloadOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { billingReportsAPI, customersAPI } from '../../services/billingAPI';
import { Line, Column, Pie } from '@ant-design/plots';
import moment from 'moment';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

const BillingReportsPage = () => {
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [reports, setReports] = useState({});
  const [activeTab, setActiveTab] = useState('builder');
  const [form] = Form.useForm();
  const [templateForm] = Form.useForm();
  const [scheduleForm] = Form.useForm();
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [currentReport, setCurrentReport] = useState(null);
  const [reportProgress, setReportProgress] = useState(0);

  // Enhanced features state
  const [reportBuilderVisible, setReportBuilderVisible] = useState(false);
  const [templatesDrawerVisible, setTemplatesDrawerVisible] = useState(false);
  const [schedulerDrawerVisible, setSchedulerDrawerVisible] = useState(false);
  const [reportBuilderStep, setReportBuilderStep] = useState(0);
  const [selectedFields, setSelectedFields] = useState([]);
  const [reportConfig, setReportConfig] = useState({
    title: '',
    description: '',
    type: 'revenue',
    format: 'table',
    fields: [],
    filters: {},
    groupBy: [],
    sortBy: [],
    chartType: 'line'
  });
  const [reportTemplates, setReportTemplates] = useState([
    {
      id: 'monthly_revenue',
      name: 'Monthly Revenue Summary',
      description: 'Comprehensive monthly revenue breakdown by service type',
      type: 'revenue',
      config: {
        fields: ['service_type', 'gross_revenue', 'net_revenue', 'tax_amount'],
        groupBy: ['service_type'],
        chartType: 'column',
        filters: { period: 'monthly' }
      },
      isDefault: true
    },
    {
      id: 'aging_analysis',
      name: 'Accounts Receivable Aging',
      description: 'Detailed aging analysis for outstanding receivables',
      type: 'aging',
      config: {
        fields: ['customer_name', 'current', '1_30_days', '31_60_days', 'total'],
        chartType: 'pie',
        filters: { includeZeroBalance: false }
      },
      isDefault: true
    },
    {
      id: 'payment_trends',
      name: 'Payment Trends Analysis',
      description: 'Payment patterns and success rate analysis',
      type: 'payment',
      config: {
        fields: ['payment_method', 'total_amount', 'success_rate', 'transaction_count'],
        groupBy: ['payment_method'],
        chartType: 'area'
      },
      isDefault: true
    }
  ]);
  const [scheduledReports, setScheduledReports] = useState([
    {
      id: 'weekly_revenue',
      name: 'Weekly Revenue Report',
      template: 'monthly_revenue',
      frequency: 'weekly',
      day: 'monday',
      time: '09:00',
      recipients: ['admin@company.com'],
      format: 'excel',
      enabled: true,
      lastRun: moment().subtract(1, 'week'),
      nextRun: moment().add(6, 'days')
    }
  ]);
  const [availableFields, setAvailableFields] = useState({
    revenue: [
      { key: 'service_type', label: 'Service Type', type: 'string' },
      { key: 'customer_name', label: 'Customer Name', type: 'string' },
      { key: 'invoice_count', label: 'Invoice Count', type: 'number' },
      { key: 'gross_revenue', label: 'Gross Revenue', type: 'currency' },
      { key: 'tax_amount', label: 'Tax Amount', type: 'currency' },
      { key: 'net_revenue', label: 'Net Revenue', type: 'currency' },
      { key: 'invoice_date', label: 'Invoice Date', type: 'date' },
      { key: 'payment_status', label: 'Payment Status', type: 'string' }
    ],
    aging: [
      { key: 'customer_name', label: 'Customer Name', type: 'string' },
      { key: 'current', label: 'Current', type: 'currency' },
      { key: '1_30_days', label: '1-30 Days', type: 'currency' },
      { key: '31_60_days', label: '31-60 Days', type: 'currency' },
      { key: '61_90_days', label: '61-90 Days', type: 'currency' },
      { key: 'over_90_days', label: 'Over 90 Days', type: 'currency' },
      { key: 'total', label: 'Total Outstanding', type: 'currency' }
    ],
    payment: [
      { key: 'payment_method', label: 'Payment Method', type: 'string' },
      { key: 'total_amount', label: 'Total Amount', type: 'currency' },
      { key: 'transaction_count', label: 'Transaction Count', type: 'number' },
      { key: 'success_rate', label: 'Success Rate', type: 'percentage' },
      { key: 'avg_amount', label: 'Average Amount', type: 'currency' },
      { key: 'payment_date', label: 'Payment Date', type: 'date' }
    ],
    usage: [
      { key: 'customer_name', label: 'Customer Name', type: 'string' },
      { key: 'usage_type', label: 'Usage Type', type: 'string' },
      { key: 'usage_amount', label: 'Usage Amount', type: 'number' },
      { key: 'billing_period', label: 'Billing Period', type: 'string' },
      { key: 'usage_date', label: 'Usage Date', type: 'date' }
    ]
  });

  // Enhanced functionality methods
  const initializeReportBuilder = useCallback(() => {
    setReportBuilderStep(0);
    setReportConfig({
      title: '',
      description: '',
      type: 'revenue',
      format: 'table',
      fields: [],
      filters: {},
      groupBy: [],
      sortBy: [],
      chartType: 'line'
    });
    setSelectedFields([]);
    setReportBuilderVisible(true);
  }, []);

  const handleReportConfigChange = useCallback((field, value) => {
    setReportConfig(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleFieldSelection = useCallback((selectedKeys) => {
    setSelectedFields(selectedKeys);
    setReportConfig(prev => ({
      ...prev,
      fields: selectedKeys
    }));
  }, []);

  const saveReportTemplate = useCallback(async (values) => {
    const newTemplate = {
      id: `template_${Date.now()}`,
      name: values.name,
      description: values.description,
      type: reportConfig.type,
      config: reportConfig,
      isDefault: false,
      createdAt: moment(),
      createdBy: 'current_user' // Replace with actual user
    };
    
    setReportTemplates(prev => [...prev, newTemplate]);
    message.success('Report template saved successfully');
    templateForm.resetFields();
  }, [reportConfig, templateForm]);

  const applyTemplate = useCallback((template) => {
    setReportConfig({
      ...template.config,
      title: template.name,
      description: template.description,
      type: template.type
    });
    setSelectedFields(template.config.fields || []);
    message.success(`Applied template: ${template.name}`);
    setTemplatesDrawerVisible(false);
  }, []);

  const scheduleReport = useCallback(async (values) => {
    const newSchedule = {
      id: `schedule_${Date.now()}`,
      name: values.name,
      template: values.templateId,
      frequency: values.frequency,
      day: values.day,
      time: values.time?.format('HH:mm'),
      recipients: values.recipients || [],
      format: values.format,
      enabled: true,
      createdAt: moment(),
      lastRun: null,
      nextRun: calculateNextRun(values.frequency, values.day, values.time)
    };
    
    setScheduledReports(prev => [...prev, newSchedule]);
    notification.success({
      message: 'Report Scheduled',
      description: `Report "${values.name}" has been scheduled successfully.`,
      duration: 4
    });
    scheduleForm.resetFields();
    setSchedulerDrawerVisible(false);
  }, [scheduleForm]);

  const calculateNextRun = useCallback((frequency, day, time) => {
    const now = moment();
    let nextRun = moment();
    
    switch (frequency) {
      case 'daily':
        nextRun = now.clone().add(1, 'day').startOf('day');
        break;
      case 'weekly':
        const targetDay = moment().day(day);
        nextRun = targetDay.isAfter(now) ? targetDay : targetDay.add(1, 'week');
        break;
      case 'monthly':
        nextRun = now.clone().add(1, 'month').startOf('month');
        break;
      case 'quarterly':
        nextRun = now.clone().add(1, 'quarter').startOf('quarter');
        break;
      default:
        nextRun = now.clone().add(1, 'day');
    }
    
    if (time) {
      nextRun.hour(time.hour()).minute(time.minute());
    }
    
    return nextRun;
  }, []);

  const generateCustomReport = useCallback(async () => {
    if (selectedFields.length === 0) {
      message.warning('Please select at least one field for the report');
      return;
    }
    
    setLoading(true);
    setReportProgress(10);
    
    try {
      setReportProgress(30);
      
      const reportData = await billingReportsAPI.generateCustomReport({
        type: reportConfig.type,
        fields: selectedFields,
        filters: reportConfig.filters,
        groupBy: reportConfig.groupBy,
        sortBy: reportConfig.sortBy,
        format: reportConfig.format
      });
      
      setReportProgress(70);
      
      setReports(prev => ({
        ...prev,
        custom: {
          ...reportData.data,
          config: reportConfig,
          generatedAt: moment()
        }
      }));
      
      setReportProgress(100);
      setReportBuilderVisible(false);
      setActiveTab('custom');
      
      notification.success({
        message: 'Custom Report Generated',
        description: 'Your custom report has been generated successfully.',
        duration: 4
      });
      
    } catch (error) {
      console.error('Error generating custom report:', error);
      message.error('Failed to generate custom report');
    } finally {
      setLoading(false);
      setTimeout(() => setReportProgress(0), 1000);
    }
  }, [selectedFields, reportConfig]);

  const exportReportAdvanced = useCallback(async (format, reportType = 'custom') => {
    try {
      const reportData = reports[reportType];
      if (!reportData) {
        message.warning('No report data available for export');
        return;
      }
      
      const exportData = {
        reportType,
        config: reportData.config,
        data: reportData,
        generatedAt: moment().format('YYYY-MM-DD HH:mm:ss')
      };
      
      if (format === 'json') {
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${reportType}-report-${moment().format('YYYY-MM-DD')}.json`;
        link.click();
        URL.revokeObjectURL(url);
        
        message.success('Report exported as JSON');
      } else {
        // For Excel/PDF, call backend API
        const response = await billingReportsAPI.exportReport({
          reportType,
          format,
          data: exportData
        });
        
        // Handle file download from response
        message.success(`Report exported as ${format.toUpperCase()}`);
      }
    } catch (error) {
      console.error('Export error:', error);
      message.error('Failed to export report');
    }
  }, [reports]);

  const toggleScheduledReport = useCallback((scheduleId, enabled) => {
    setScheduledReports(prev => prev.map(schedule => 
      schedule.id === scheduleId ? { ...schedule, enabled } : schedule
    ));
    message.success(`Schedule ${enabled ? 'enabled' : 'disabled'}`);
  }, []);

  const deleteScheduledReport = useCallback((scheduleId) => {
    setScheduledReports(prev => prev.filter(schedule => schedule.id !== scheduleId));
    message.success('Scheduled report deleted');
  }, []);

  const fetchCustomers = async () => {
    try {
      const response = await customersAPI.getAll();
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
      message.error('Failed to load customers');
    }
  };

  const generateReport = async (reportType, formData) => {
    setLoading(true);
    setReportProgress(10);
    
    try {
      const [startDate, endDate] = formData.dateRange || [];
      let reportData;
      
      setReportProgress(30);
      
      switch (reportType) {
        case 'revenue':
          reportData = await billingReportsAPI.generateRevenue(
            startDate.format('YYYY-MM-DD'),
            endDate.format('YYYY-MM-DD'),
            formData
          );
          break;
        case 'aging':
          reportData = await billingReportsAPI.generateAging(
            endDate ? endDate.format('YYYY-MM-DD') : null
          );
          break;
        case 'payment':
          reportData = await billingReportsAPI.generatePaymentAnalysis(
            startDate.format('YYYY-MM-DD'),
            endDate.format('YYYY-MM-DD')
          );
          break;
        case 'tax':
          reportData = await billingReportsAPI.generateTaxSummary(
            startDate.format('YYYY-MM-DD'),
            endDate.format('YYYY-MM-DD')
          );
          break;
        case 'usage':
          reportData = await billingReportsAPI.generateUsageReport(
            formData.customerId,
            startDate.format('YYYY-MM-DD'),
            endDate.format('YYYY-MM-DD')
          );
          break;
        default:
          throw new Error('Invalid report type');
      }
      
      setReportProgress(70);
      
      setReports(prev => ({
        ...prev,
        [reportType]: reportData.data
      }));
      
      setReportProgress(100);
      message.success(`${reportType.charAt(0).toUpperCase() + reportType.slice(1)} report generated successfully`);
      
    } catch (error) {
      console.error('Error generating report:', error);
      message.error('Failed to generate report');
    } finally {
      setLoading(false);
      setTimeout(() => setReportProgress(0), 1000);
    }
  };

  const handleFormSubmit = (values) => {
    generateReport(activeTab, values);
  };

  const exportReport = (format) => {
    message.info(`Export to ${format.toUpperCase()} functionality coming soon`);
  };

  const previewReport = (reportType) => {
    setCurrentReport({ type: reportType, data: reports[reportType] });
    setPreviewModalVisible(true);
  };

  const revenueColumns = [
    {
      title: 'Service Type',
      dataIndex: 'service_type',
      key: 'service_type',
      render: (type) => <Tag color="blue">{type?.toUpperCase()}</Tag>
    },
    {
      title: 'Invoice Count',
      dataIndex: 'invoice_count',
      key: 'invoice_count'
    },
    {
      title: 'Gross Revenue',
      dataIndex: 'gross_revenue',
      key: 'gross_revenue',
      render: (amount) => `$${parseFloat(amount || 0).toFixed(2)}`
    },
    {
      title: 'Tax Amount',
      dataIndex: 'tax_amount',
      key: 'tax_amount',
      render: (amount) => `$${parseFloat(amount || 0).toFixed(2)}`
    },
    {
      title: 'Net Revenue',
      dataIndex: 'net_revenue',
      key: 'net_revenue',
      render: (amount) => `$${parseFloat(amount || 0).toFixed(2)}`
    }
  ];

  const agingColumns = [
    {
      title: 'Customer',
      dataIndex: 'customer_name',
      key: 'customer_name'
    },
    {
      title: 'Current',
      dataIndex: 'current',
      key: 'current',
      render: (amount) => `$${parseFloat(amount || 0).toFixed(2)}`
    },
    {
      title: '1-30 Days',
      dataIndex: '1_30_days',
      key: '1_30_days',
      render: (amount) => `$${parseFloat(amount || 0).toFixed(2)}`
    },
    {
      title: '31-60 Days',
      dataIndex: '31_60_days',
      key: '31_60_days',
      render: (amount) => `$${parseFloat(amount || 0).toFixed(2)}`
    },
    {
      title: '61-90 Days',
      dataIndex: '61_90_days',
      key: '61_90_days',
      render: (amount) => `$${parseFloat(amount || 0).toFixed(2)}`
    },
    {
      title: 'Over 90 Days',
      dataIndex: 'over_90_days',
      key: 'over_90_days',
      render: (amount) => `$${parseFloat(amount || 0).toFixed(2)}`
    },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      render: (amount) => <strong>`$${parseFloat(amount || 0).toFixed(2)}`</strong>
    }
  ];

  const renderRevenueChart = (data) => {
    if (!data || !data.revenue_by_month) return null;
    
    const chartData = Object.entries(data.revenue_by_month).map(([month, amount]) => ({
      month,
      revenue: parseFloat(amount)
    }));

    const config = {
      data: chartData,
      xField: 'month',
      yField: 'revenue',
      point: {
        size: 5,
        shape: 'diamond',
      },
      label: {
        style: {
          fill: '#aaa',
        },
      },
    };

    return <Line {...config} />;
  };

  const renderAgingChart = (data) => {
    if (!data || !data.aging_buckets) return null;
    
    const chartData = Object.entries(data.aging_buckets).map(([bucket, amount]) => ({
      bucket: bucket.replace('_', '-'),
      amount: parseFloat(amount)
    }));

    const config = {
      data: chartData,
      xField: 'bucket',
      yField: 'amount',
      color: ({ bucket }) => {
        if (bucket === 'current') return '#52c41a';
        if (bucket === '1-30-days') return '#1890ff';
        if (bucket === '31-60-days') return '#faad14';
        if (bucket === '61-90-days') return '#fa8c16';
        return '#f5222d';
      },
    };

    return <Column {...config} />;
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Enhanced Statistics Dashboard */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Available Reports"
              value={Object.keys(availableFields).length}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Generated Reports"
              value={Object.keys(reports).length}
              prefix={<FileExcelOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Saved Templates"
              value={reportTemplates.length}
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Scheduled Reports"
              value={scheduledReports.filter(s => s.enabled).length}
              prefix={<ScheduleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {scheduledReports.length} total schedules
            </div>
          </Card>
        </Col>
      </Row>

      {/* Report Progress */}
      {reportProgress > 0 && (
        <Card style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Spin size="small" />
            <div style={{ flex: 1 }}>
              <Text strong>Generating Report...</Text>
              <Progress percent={reportProgress} size="small" status="active" />
            </div>
          </div>
        </Card>
      )}

      {/* Main Action Controls */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col span={6}>
            <Button
              type="primary"
              icon={<BuildOutlined />}
              size="large"
              onClick={initializeReportBuilder}
              style={{ width: '100%' }}
            >
              Report Builder
            </Button>
          </Col>
          <Col span={6}>
            <Button
              icon={<FolderOutlined />}
              size="large"
              onClick={() => setTemplatesDrawerVisible(true)}
              style={{ width: '100%' }}
            >
              Templates ({reportTemplates.length})
            </Button>
          </Col>
          <Col span={6}>
            <Button
              icon={<ScheduleOutlined />}
              size="large"
              onClick={() => setSchedulerDrawerVisible(true)}
              style={{ width: '100%' }}
            >
              Scheduler ({scheduledReports.length})
            </Button>
          </Col>
          <Col span={6}>
            <Button
              icon={<ReloadOutlined />}
              size="large"
              onClick={() => window.location.reload()}
              style={{ width: '100%' }}
            >
              Refresh
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Enhanced Reports Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        tabBarExtraContent={
          <Space>
            <Badge count={scheduledReports.filter(s => s.enabled).length} offset={[10, 0]}>
              <Button
                icon={<BellOutlined />}
                onClick={() => setSchedulerDrawerVisible(true)}
              >
                Active Schedules
              </Button>
            </Badge>
          </Space>
        }
      >
        {/* Report Builder Tab */}
        <TabPane
          tab={<span><BuildOutlined />Report Builder</span>}
          key="builder"
        >
          <Card>
            <Empty
              image={<BuildOutlined style={{ fontSize: 64, color: '#1890ff' }} />}
              description={
                <div>
                  <Title level={4}>Advanced Report Builder</Title>
                  <Text type="secondary">
                    Create custom reports with our powerful drag-and-drop report builder.
                    Select data fields, apply filters, choose visualizations, and save as templates.
                  </Text>
                </div>
              }
            >
              <Button type="primary" size="large" onClick={initializeReportBuilder}>
                Open Report Builder
              </Button>
            </Empty>
          </Card>
        </TabPane>

        {/* Custom Reports Tab */}
        {reports.custom && (
          <TabPane
            tab={<span><TableOutlined />Custom Report</span>}
            key="custom"
          >
            <Card
              title={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{reports.custom.config?.title || 'Custom Report'}</span>
                  <Space>
                    <Tag color="blue">{reports.custom.config?.type?.toUpperCase()}</Tag>
                    <Tag color="green">{reports.custom.config?.format?.toUpperCase()}</Tag>
                  </Space>
                </div>
              }
              extra={
                <Space>
                  <Button icon={<EyeOutlined />} onClick={() => previewReport('custom')}>
                    Preview
                  </Button>
                  <Button icon={<ExportOutlined />} onClick={() => exportReportAdvanced('json', 'custom')}>
                    Export JSON
                  </Button>
                  <Button icon={<FileExcelOutlined />} onClick={() => exportReportAdvanced('excel', 'custom')}>
                    Export Excel
                  </Button>
                  <Button icon={<FilePdfOutlined />} onClick={() => exportReportAdvanced('pdf', 'custom')}>
                    Export PDF
                  </Button>
                </Space>
              }
            >
              <Descriptions bordered size="small" style={{ marginBottom: '16px' }}>
                <Descriptions.Item label="Generated">
                  {reports.custom.generatedAt?.format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
                <Descriptions.Item label="Fields">
                  {reports.custom.config?.fields?.length || 0} selected
                </Descriptions.Item>
                <Descriptions.Item label="Format">
                  {reports.custom.config?.format || 'Table'}
                </Descriptions.Item>
              </Descriptions>
              
              {reports.custom.config?.description && (
                <Alert
                  message={reports.custom.config.description}
                  type="info"
                  style={{ marginBottom: '16px' }}
                />
              )}
              
              {/* Render custom report data based on format */}
              {reports.custom.config?.format === 'chart' ? (
                <div style={{ height: 400 }}>
                  {/* Chart rendering would go here based on chartType */}
                  <Empty description="Chart visualization will be implemented based on data structure" />
                </div>
              ) : (
                <div>
                  {/* Table rendering */}
                  <Text type="secondary">Custom report data table will be rendered here</Text>
                </div>
              )}
            </Card>
          </TabPane>
        )}

        {/* Standard Report Tabs */}
        <TabPane tab="Revenue Reports" key="revenue">
          <Form form={form} layout="inline" onFinish={handleFormSubmit} style={{ marginBottom: '16px' }}>
            <Form.Item name="dateRange" label="Date Range" rules={[{ required: true }]}>
              <RangePicker />
            </Form.Item>
            <Form.Item name="serviceType" label="Service Type">
              <Select placeholder="All services" style={{ width: 150 }} allowClear>
                <Option value="internet">Internet</Option>
                <Option value="voice">Voice</Option>
                <Option value="bundle">Bundle</Option>
              </Select>
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Generate Report
                </Button>
                {reports.revenue && (
                  <>
                    <Button icon={<EyeOutlined />} onClick={() => previewReport('revenue')}>
                      Preview
                    </Button>
                    <Button icon={<FileExcelOutlined />} onClick={() => exportReport('excel')}>
                      Excel
                    </Button>
                    <Button icon={<FilePdfOutlined />} onClick={() => exportReport('pdf')}>
                      PDF
                    </Button>
                  </>
                )}
              </Space>
            </Form.Item>
          </Form>

          {reports.revenue && (
            <div>
              <Row gutter={16} style={{ marginBottom: '16px' }}>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="Total Revenue"
                      value={parseFloat(reports.revenue.total_revenue || 0)}
                      precision={2}
                      prefix="$"
                      valueStyle={{ color: '#3f8600' }}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="Total Tax"
                      value={parseFloat(reports.revenue.total_tax || 0)}
                      precision={2}
                      prefix="$"
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="Invoice Count"
                      value={reports.revenue.invoice_count || 0}
                      valueStyle={{ color: '#722ed1' }}
                    />
                  </Card>
                </Col>
              </Row>
              {renderRevenueChart(reports.revenue)}
            </div>
          )}
        </TabPane>

        <TabPane tab="Aging Report" key="aging">
          <Form form={form} layout="inline" onFinish={handleFormSubmit} style={{ marginBottom: '16px' }}>
            <Form.Item name="asOfDate" label="As of Date" initialValue={moment()}>
              <DatePicker />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Generate Report
                </Button>
                {reports.aging && (
                  <>
                    <Button icon={<EyeOutlined />} onClick={() => previewReport('aging')}>
                      Preview
                    </Button>
                    <Button icon={<FileExcelOutlined />} onClick={() => exportReport('excel')}>
                      Excel
                    </Button>
                    <Button icon={<FilePdfOutlined />} onClick={() => exportReport('pdf')}>
                      PDF
                    </Button>
                  </>
                )}
              </Space>
            </Form.Item>
          </Form>

          {reports.aging && (
            <div>
              <Row gutter={16} style={{ marginBottom: '16px' }}>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="Total Outstanding"
                      value={parseFloat(reports.aging.total_outstanding || 0)}
                      precision={2}
                      prefix="$"
                      valueStyle={{ color: '#f5222d' }}
                    />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title="Customers with Balance"
                      value={Object.keys(reports.aging.customer_count_by_bucket || {}).reduce((sum, key) => 
                        sum + (reports.aging.customer_count_by_bucket[key] || 0), 0)}
                      valueStyle={{ color: '#722ed1' }}
                    />
                  </Card>
                </Col>
              </Row>
              {renderAgingChart(reports.aging)}
            </div>
          )}
        </TabPane>

        <TabPane tab="Payment Analysis" key="payment">
          <Form form={form} layout="inline" onFinish={handleFormSubmit} style={{ marginBottom: '16px' }}>
            <Form.Item name="dateRange" label="Date Range" rules={[{ required: true }]}>
              <RangePicker />
            </Form.Item>
            <Form.Item name="paymentMethod" label="Payment Method">
              <Select placeholder="All methods" style={{ width: 150 }} allowClear>
                <Option value="credit_card">Credit Card</Option>
                <Option value="bank_transfer">Bank Transfer</Option>
                <Option value="cash">Cash</Option>
                <Option value="check">Check</Option>
              </Select>
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Generate Report
                </Button>
                {reports.payment && (
                  <>
                    <Button icon={<EyeOutlined />} onClick={() => previewReport('payment')}>
                      Preview
                    </Button>
                    <Button icon={<FileExcelOutlined />} onClick={() => exportReport('excel')}>
                      Excel
                    </Button>
                    <Button icon={<FilePdfOutlined />} onClick={() => exportReport('pdf')}>
                      PDF
                    </Button>
                  </>
                )}
              </Space>
            </Form.Item>
          </Form>

          {reports.payment && (
            <Row gutter={16}>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Total Payments"
                    value={parseFloat(reports.payment.total_payments || 0)}
                    precision={2}
                    prefix="$"
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Payment Count"
                    value={reports.payment.payment_count || 0}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Success Rate"
                    value={parseFloat(reports.payment.payment_success_rate || 0)}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Card>
              </Col>
            </Row>
          )}
        </TabPane>

        <TabPane tab="Usage Reports" key="usage">
          <Form form={form} layout="inline" onFinish={handleFormSubmit} style={{ marginBottom: '16px' }}>
            <Form.Item name="customerId" label="Customer" rules={[{ required: true }]}>
              <Select
                placeholder="Select customer"
                style={{ width: 200 }}
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
            </Form.Item>
            <Form.Item name="dateRange" label="Date Range" rules={[{ required: true }]}>
              <RangePicker />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Generate Report
                </Button>
                {reports.usage && (
                  <>
                    <Button icon={<EyeOutlined />} onClick={() => previewReport('usage')}>
                      Preview
                    </Button>
                    <Button icon={<FileExcelOutlined />} onClick={() => exportReport('excel')}>
                      Excel
                    </Button>
                    <Button icon={<FilePdfOutlined />} onClick={() => exportReport('pdf')}>
                      PDF
                    </Button>
                  </>
                )}
              </Space>
            </Form.Item>
          </Form>

          {reports.usage && (
            <Alert
              message="Usage Report Generated"
              description={`Usage data for selected customer and period. Total records: ${reports.usage.length || 0}`}
              type="success"
              style={{ marginBottom: '16px' }}
            />
          )}
        </TabPane>
      </Tabs>

      {/* Templates Drawer */}
      <Drawer
        title="Report Templates"
        placement="right"
        width={600}
        open={templatesDrawerVisible}
        onClose={() => setTemplatesDrawerVisible(false)}
      >
        <div style={{ marginBottom: '16px' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              templateForm.setFieldsValue({
                name: reportConfig.title || '',
                description: reportConfig.description || ''
              });
            }}
            style={{ width: '100%' }}
          >
            Save Current Config as Template
          </Button>
        </div>

        <Divider />

        <div>
          <Title level={4}>Available Templates</Title>
          {reportTemplates.map(template => (
            <Card
              key={template.id}
              size="small"
              style={{ marginBottom: '12px' }}
              title={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{template.name}</span>
                  <Space>
                    {template.isDefault && <Tag color="gold">Default</Tag>}
                    <Tag color="blue">{template.type?.toUpperCase()}</Tag>
                  </Space>
                </div>
              }
              actions={[
                <Button
                  type="link"
                  icon={<EyeOutlined />}
                  onClick={() => applyTemplate(template)}
                >
                  Apply
                </Button>,
                <Button
                  type="link"
                  icon={<CopyOutlined />}
                  onClick={() => {
                    const newTemplate = {
                      ...template,
                      id: `template_${Date.now()}`,
                      name: `${template.name} (Copy)`,
                      isDefault: false
                    };
                    setReportTemplates(prev => [...prev, newTemplate]);
                    message.success('Template duplicated');
                  }}
                >
                  Duplicate
                </Button>,
                !template.isDefault && (
                  <Popconfirm
                    title="Delete template?"
                    onConfirm={() => {
                      setReportTemplates(prev => prev.filter(t => t.id !== template.id));
                      message.success('Template deleted');
                    }}
                  >
                    <Button type="link" danger icon={<DeleteOutlined />}>
                      Delete
                    </Button>
                  </Popconfirm>
                )
              ]}
            >
              <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
                {template.description}
              </p>
              <div style={{ marginTop: '8px' }}>
                <Space size={[0, 4]} wrap>
                  <Tag>Fields: {template.config?.fields?.length || 0}</Tag>
                  <Tag color={template.config?.chartType ? 'green' : 'default'}>
                    {template.config?.chartType ? template.config.chartType : 'Table'}
                  </Tag>
                </Space>
              </div>
            </Card>
          ))}
        </div>

        <Modal
          title="Save Report Template"
          open={templateForm.getFieldValue('name') !== undefined}
          onCancel={() => templateForm.resetFields()}
          footer={null}
          width={400}
        >
          <Form
            form={templateForm}
            layout="vertical"
            onFinish={saveReportTemplate}
          >
            <Form.Item
              name="name"
              label="Template Name"
              rules={[{ required: true, message: 'Please enter template name' }]}
            >
              <Input placeholder="e.g., Monthly Revenue Analysis" />
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
                <Button onClick={() => templateForm.resetFields()}>
                  Cancel
                </Button>
                <Button type="primary" htmlType="submit">
                  Save Template
                </Button>
              </Space>
            </div>
          </Form>
        </Modal>
      </Drawer>

      {/* Scheduler Drawer */}
      <Drawer
        title="Report Scheduler"
        placement="right"
        width={700}
        open={schedulerDrawerVisible}
        onClose={() => setSchedulerDrawerVisible(false)}
      >
        <div style={{ marginBottom: '16px' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => scheduleForm.resetFields()}
            style={{ width: '100%' }}
          >
            Schedule New Report
          </Button>
        </div>

        <Divider />

        <div style={{ marginBottom: '24px' }}>
          <Title level={4}>Active Schedules</Title>
          {scheduledReports.map(schedule => (
            <Card
              key={schedule.id}
              size="small"
              style={{ marginBottom: '12px' }}
              title={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{schedule.name}</span>
                  <Space>
                    <Switch
                      checked={schedule.enabled}
                      onChange={(enabled) => toggleScheduledReport(schedule.id, enabled)}
                      size="small"
                    />
                    {schedule.enabled && <Badge status="processing" text="Active" />}
                  </Space>
                </div>
              }
              actions={[
                <Button type="link" icon={<EditOutlined />}>
                  Edit
                </Button>,
                <Popconfirm
                  title="Delete schedule?"
                  onConfirm={() => deleteScheduledReport(schedule.id)}
                >
                  <Button type="link" danger icon={<DeleteOutlined />}>
                    Delete
                  </Button>
                </Popconfirm>
              ]}
            >
              <div>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Frequency:</Text> {schedule.frequency}
                    {schedule.day && <Text type="secondary"> on {schedule.day}</Text>}
                    <Text type="secondary"> at {schedule.time}</Text>
                  </div>
                  <div>
                    <Text strong>Template:</Text> {reportTemplates.find(t => t.id === schedule.template)?.name || 'Unknown'}
                  </div>
                  <div>
                    <Text strong>Format:</Text> {schedule.format?.toUpperCase()}
                  </div>
                  <div>
                    <Text strong>Recipients:</Text> {schedule.recipients?.join(', ') || 'None'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    Last run: {schedule.lastRun ? schedule.lastRun.fromNow() : 'Never'} | 
                    Next run: {schedule.nextRun?.fromNow() || 'Not scheduled'}
                  </div>
                </Space>
              </div>
            </Card>
          ))}
        </div>

        <Form
          form={scheduleForm}
          layout="vertical"
          onFinish={scheduleReport}
        >
          <Title level={4}>Create Schedule</Title>
          
          <Form.Item
            name="name"
            label="Schedule Name"
            rules={[{ required: true, message: 'Please enter schedule name' }]}
          >
            <Input placeholder="e.g., Weekly Revenue Report" />
          </Form.Item>
          
          <Form.Item
            name="templateId"
            label="Report Template"
            rules={[{ required: true, message: 'Please select a template' }]}
          >
            <Select placeholder="Select template">
              {reportTemplates.map(template => (
                <Option key={template.id} value={template.id}>
                  {template.name} ({template.type})
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="frequency"
                label="Frequency"
                rules={[{ required: true, message: 'Please select frequency' }]}
              >
                <Select placeholder="Select frequency">
                  <Option value="daily">Daily</Option>
                  <Option value="weekly">Weekly</Option>
                  <Option value="monthly">Monthly</Option>
                  <Option value="quarterly">Quarterly</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="day" label="Day (for weekly/monthly)">
                <Select placeholder="Select day">
                  <Option value="monday">Monday</Option>
                  <Option value="tuesday">Tuesday</Option>
                  <Option value="wednesday">Wednesday</Option>
                  <Option value="thursday">Thursday</Option>
                  <Option value="friday">Friday</Option>
                  <Option value="saturday">Saturday</Option>
                  <Option value="sunday">Sunday</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="time"
                label="Time"
                rules={[{ required: true, message: 'Please select time' }]}
              >
                <TimePicker format="HH:mm" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="format"
                label="Export Format"
                rules={[{ required: true, message: 'Please select format' }]}
              >
                <Select placeholder="Select format">
                  <Option value="excel">Excel</Option>
                  <Option value="pdf">PDF</Option>
                  <Option value="json">JSON</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item name="recipients" label="Email Recipients">
            <Select
              mode="tags"
              placeholder="Enter email addresses"
              style={{ width: '100%' }}
            />
          </Form.Item>
          
          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => scheduleForm.resetFields()}>
                Reset
              </Button>
              <Button type="primary" htmlType="submit">
                Create Schedule
              </Button>
            </Space>
          </div>
        </Form>
      </Drawer>

      {/* Enhanced Preview Modal */}
      <Modal
        title={`${currentReport?.type?.charAt(0).toUpperCase() + currentReport?.type?.slice(1)} Report Preview`}
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        width={1000}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            Close
          </Button>,
          <Button key="download" type="primary" icon={<DownloadOutlined />}>
            Download
          </Button>
        ]}
      >
        {currentReport && (
          <div>
            <Descriptions bordered size="small" style={{ marginBottom: '16px' }}>
              <Descriptions.Item label="Report Type" span={2}>
                {currentReport.type?.charAt(0).toUpperCase() + currentReport.type?.slice(1)}
              </Descriptions.Item>
              <Descriptions.Item label="Generated">
                {moment().format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>
            
            {currentReport.type === 'revenue' && reports.revenue && (
              <Table
                columns={revenueColumns}
                dataSource={reports.revenue.revenue_by_service_type ? 
                  Object.entries(reports.revenue.revenue_by_service_type).map(([type, data]) => ({
                    key: type,
                    service_type: type,
                    ...data
                  })) : []}
                pagination={false}
                size="small"
              />
            )}
            
            {currentReport.type === 'aging' && reports.aging && (
              <Table
                columns={agingColumns}
                dataSource={reports.aging.customer_details || []}
                pagination={false}
                size="small"
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default BillingReportsPage;