import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  message,
  Space,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Alert,
  Tabs,
  Timeline,
  Badge,
  Descriptions,
  Switch,
  Progress,
  Drawer,
  notification,
  Divider,
  Empty,
  Typography,
  List,
  Avatar,
  Slider,
  Radio,
  Steps,
  Spin
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  ExportOutlined,
  InfoCircleOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DatabaseOutlined,
  BellOutlined,
  LineChartOutlined,
  BarChartOutlined,
  DashboardOutlined,
  SettingOutlined,
  FilterOutlined,
  DownloadOutlined,
  EyeOutlined,
  ThunderboltOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  WarningOutlined,
  RadarChartOutlined,
  StockOutlined,
  MonitorOutlined
} from '@ant-design/icons';
import { Line, Column, Pie, Area, Gauge } from '@ant-design/plots';
import { usageTrackingAPI, billingEventsAPI, customersAPI } from '../../services/billingAPI';
import moment from 'moment';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;
const { Title, Text } = Typography;
const { Step } = Steps;

const UsageTrackingPage = () => {
  const [loading, setLoading] = useState(false);
  const [usageRecords, setUsageRecords] = useState([]);
  const [billingEvents, setBillingEvents] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [alertForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [filters, setFilters] = useState({
    customer_id: null,
    start_date: moment().subtract(30, 'days'),
    end_date: moment(),
    event_type: null
  });
  const [statistics, setStatistics] = useState({
    totalUsage: 0,
    totalEvents: 0,
    activeCustomers: 0,
    avgUsagePerCustomer: 0,
    peakUsageHour: 0,
    usageGrowth: 0,
    alertsTriggered: 0
  });

  // Real-time monitoring state
  const [realTimeEnabled, setRealTimeEnabled] = useState(true);
  const [liveData, setLiveData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [alertRules, setAlertRules] = useState([
    {
      id: 'high_usage',
      name: 'High Usage Alert',
      description: 'Triggered when usage exceeds threshold',
      threshold: 10000,
      condition: 'greater_than',
      enabled: true,
      type: 'usage_threshold'
    },
    {
      id: 'unusual_pattern',
      name: 'Unusual Usage Pattern',
      description: 'Triggered when usage pattern is anomalous',
      threshold: 50,
      condition: 'percentage_change',
      enabled: true,
      type: 'pattern_anomaly'
    }
  ]);
  const [trendData, setTrendData] = useState([]);
  const [analyticsDrawerVisible, setAnalyticsDrawerVisible] = useState(false);
  const [alertsDrawerVisible, setAlertsDrawerVisible] = useState(false);
  const [selectedCustomerAnalytics, setSelectedCustomerAnalytics] = useState(null);
  const refreshInterval = useRef(null);

  // Real-time monitoring and analytics functions
  const generateTrendData = useCallback((records) => {
    const groupedData = records.reduce((acc, record) => {
      const date = moment(record.usage_date).format('YYYY-MM-DD');
      const hour = moment(record.usage_date).hour();
      
      if (!acc[date]) {
        acc[date] = { date, total: 0, data: 0, voice: 0, sms: 0, hours: {} };
      }
      
      acc[date].total += parseFloat(record.usage_amount || 0);
      acc[date][record.usage_type] += parseFloat(record.usage_amount || 0);
      
      if (!acc[date].hours[hour]) {
        acc[date].hours[hour] = 0;
      }
      acc[date].hours[hour] += parseFloat(record.usage_amount || 0);
      
      return acc;
    }, {});
    
    return Object.values(groupedData).sort((a, b) => moment(a.date).diff(moment(b.date)));
  }, []);

  const checkAlertRules = useCallback((currentUsage, historicalData) => {
    const newAlerts = [];
    
    alertRules.forEach(rule => {
      if (!rule.enabled) return;
      
      if (rule.type === 'usage_threshold') {
        if (currentUsage > rule.threshold) {
          newAlerts.push({
            id: `alert_${Date.now()}_${rule.id}`,
            ruleId: rule.id,
            title: rule.name,
            message: `Usage ${currentUsage.toFixed(2)} exceeds threshold ${rule.threshold}`,
            severity: 'warning',
            timestamp: moment(),
            type: 'threshold'
          });
        }
      } else if (rule.type === 'pattern_anomaly' && historicalData.length > 1) {
        const recent = historicalData[historicalData.length - 1]?.total || 0;
        const previous = historicalData[historicalData.length - 2]?.total || 0;
        
        if (previous > 0) {
          const percentageChange = Math.abs((recent - previous) / previous) * 100;
          if (percentageChange > rule.threshold) {
            newAlerts.push({
              id: `alert_${Date.now()}_${rule.id}`,
              ruleId: rule.id,
              title: rule.name,
              message: `Usage pattern changed by ${percentageChange.toFixed(1)}% (${recent.toFixed(2)} vs ${previous.toFixed(2)})`,
              severity: 'info',
              timestamp: moment(),
              type: 'anomaly'
            });
          }
        }
      }
    });
    
    if (newAlerts.length > 0) {
      setAlerts(prev => [...newAlerts, ...prev.slice(0, 49)]); // Keep last 50 alerts
      newAlerts.forEach(alert => {
        notification.open({
          message: alert.title,
          description: alert.message,
          icon: alert.severity === 'warning' ? <WarningOutlined style={{ color: '#fa8c16' }} /> : <InfoCircleOutlined style={{ color: '#1890ff' }} />,
          duration: 6
        });
      });
    }
  }, [alertRules]);

  const simulateRealTimeData = useCallback(() => {
    if (!realTimeEnabled) return;
    
    const newDataPoint = {
      id: `live_${Date.now()}`,
      timestamp: moment(),
      usage_amount: Math.random() * 1000 + 100,
      usage_type: ['data', 'voice', 'sms'][Math.floor(Math.random() * 3)],
      customer_id: customers[Math.floor(Math.random() * customers.length)]?.id
    };
    
    setLiveData(prev => [newDataPoint, ...prev.slice(0, 99)]); // Keep last 100 points
    
    // Check alerts for real-time data
    const recentUsage = liveData.slice(0, 10).reduce((sum, point) => sum + point.usage_amount, 0);
    checkAlertRules(recentUsage, trendData);
  }, [realTimeEnabled, customers, liveData, trendData, checkAlertRules]);

  const calculateAdvancedStatistics = useCallback((records) => {
    if (records.length === 0) return statistics;
    
    const hourlyUsage = records.reduce((acc, record) => {
      const hour = moment(record.usage_date).hour();
      acc[hour] = (acc[hour] || 0) + parseFloat(record.usage_amount || 0);
      return acc;
    }, {});
    
    const peakHour = Object.entries(hourlyUsage)
      .reduce((max, [hour, usage]) => usage > max.usage ? { hour: parseInt(hour), usage } : max, { hour: 0, usage: 0 });
    
    const dailyTotals = records.reduce((acc, record) => {
      const date = moment(record.usage_date).format('YYYY-MM-DD');
      acc[date] = (acc[date] || 0) + parseFloat(record.usage_amount || 0);
      return acc;
    }, {});
    
    const sortedDates = Object.keys(dailyTotals).sort();
    const growthRate = sortedDates.length > 1 ? 
      ((dailyTotals[sortedDates[sortedDates.length - 1]] - dailyTotals[sortedDates[0]]) / dailyTotals[sortedDates[0]] * 100) : 0;
    
    return {
      totalUsage: records.reduce((sum, record) => sum + parseFloat(record.usage_amount || 0), 0),
      totalEvents: records.length,
      activeCustomers: new Set(records.map(r => r.customer_id)).size,
      avgUsagePerCustomer: records.length > 0 ? records.reduce((sum, record) => sum + parseFloat(record.usage_amount || 0), 0) / new Set(records.map(r => r.customer_id)).size : 0,
      peakUsageHour: peakHour.hour,
      usageGrowth: growthRate,
      alertsTriggered: alerts.filter(alert => moment().diff(alert.timestamp, 'hours') < 24).length
    };
  }, [alerts, statistics]);

  // Enhanced useEffect hooks
  useEffect(() => {
    fetchCustomers();
    fetchData();
  }, []);

  useEffect(() => {
    fetchData();
  }, [filters]);

  // Real-time monitoring setup
  useEffect(() => {
    if (realTimeEnabled && customers.length > 0) {
      refreshInterval.current = setInterval(simulateRealTimeData, 5000); // Update every 5 seconds
    } else {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    }
    
    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, [realTimeEnabled, customers, simulateRealTimeData]);

  // Update trend data when usage records change
  useEffect(() => {
    if (usageRecords.length > 0) {
      const trends = generateTrendData(usageRecords);
      setTrendData(trends);
      
      const enhancedStats = calculateAdvancedStatistics(usageRecords);
      setStatistics(enhancedStats);
    }
  }, [usageRecords, generateTrendData, calculateAdvancedStatistics]);

  const fetchCustomers = async () => {
    try {
      const response = await customersAPI.getAll();
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
      message.error('Failed to load customers');
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        ...filters,
        start_date: filters.start_date?.format('YYYY-MM-DD'),
        end_date: filters.end_date?.format('YYYY-MM-DD')
      };

      if (activeTab === 'usage' || activeTab === 'dashboard') {
        const response = await usageTrackingAPI.getAll(params);
        setUsageRecords(response.data);
      }
      
      if (activeTab === 'events' || activeTab === 'dashboard') {
        const eventsResponse = await billingEventsAPI.getAll(params);
        setBillingEvents(eventsResponse.data);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      message.error(`Failed to load ${activeTab} data`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUsage = () => {
    form.resetFields();
    form.setFieldsValue({
      usage_date: moment(),
      usage_type: 'data'
    });
    setModalVisible(true);
  };

  const handleSubmitUsage = async (values) => {
    setLoading(true);
    try {
      const payload = {
        ...values,
        usage_date: values.usage_date.format('YYYY-MM-DD'),
        usage_amount: parseFloat(values.usage_amount)
      };
      
      await usageTrackingAPI.create(payload);
      message.success('Usage record created successfully');
      setModalVisible(false);
      fetchData();
    } catch (error) {
      console.error('Error creating usage record:', error);
      message.error('Failed to create usage record');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // New handlers for enhanced features
  const handleRealTimeToggle = (enabled) => {
    setRealTimeEnabled(enabled);
    if (enabled) {
      message.success('Real-time monitoring enabled');
    } else {
      message.info('Real-time monitoring disabled');
    }
  };

  const handleViewCustomerAnalytics = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    if (customer) {
      setSelectedCustomerAnalytics(customer);
      setAnalyticsDrawerVisible(true);
    }
  };

  const handleCreateAlert = (values) => {
    const newAlert = {
      id: `alert_rule_${Date.now()}`,
      ...values,
      enabled: true
    };
    setAlertRules(prev => [...prev, newAlert]);
    message.success('Alert rule created successfully');
    alertForm.resetFields();
  };

  const handleToggleAlertRule = (ruleId, enabled) => {
    setAlertRules(prev => prev.map(rule => 
      rule.id === ruleId ? { ...rule, enabled } : rule
    ));
    message.success(`Alert rule ${enabled ? 'enabled' : 'disabled'}`);
  };

  const handleExportData = () => {
    const dataToExport = {
      usage_records: usageRecords,
      billing_events: billingEvents,
      statistics,
      trend_data: trendData,
      alerts: alerts.slice(0, 10), // Export recent alerts
      export_date: moment().format('YYYY-MM-DD HH:mm:ss')
    };
    
    const dataStr = JSON.stringify(dataToExport, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `usage-analytics-${moment().format('YYYY-MM-DD')}.json`;
    link.click();
    URL.revokeObjectURL(url);
    
    message.success('Analytics data exported successfully');
  };

  const showEventDetails = (event) => {
    Modal.info({
      title: 'Billing Event Details',
      width: 600,
      content: (
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="Customer">{event.customer?.name}</Descriptions.Item>
          <Descriptions.Item label="Event Type">{event.event_type}</Descriptions.Item>
          <Descriptions.Item label="Amount">{event.amount ? `$${parseFloat(event.amount).toFixed(2)}` : 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Date">{moment(event.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
          <Descriptions.Item label="Description">{event.description}</Descriptions.Item>
          {event.event_metadata && (
            <Descriptions.Item label="Metadata">
              <pre style={{ fontSize: '12px', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {JSON.stringify(JSON.parse(event.event_metadata), null, 2)}
              </pre>
            </Descriptions.Item>
          )}
        </Descriptions>
      ),
    });
  };

  // Enhanced event columns
  const eventColumns = [
    {
      title: 'Customer',
      dataIndex: 'customer',
      key: 'customer',
      render: (customer) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{customer?.name}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{customer?.email}</div>
        </div>
      ),
    },
    {
      title: 'Event Type',
      dataIndex: 'event_type',
      key: 'event_type',
      render: (type) => {
        const colors = {
          invoice_generated: 'blue',
          payment_received: 'green',
          service_suspended: 'red',
          service_reactivated: 'cyan',
          dunning_notice: 'orange',
          credit_applied: 'purple'
        };
        return <Tag color={colors[type] || 'default'}>{type?.replace('_', ' ').toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount) => amount ? `$${parseFloat(amount).toFixed(2)}` : '-',
    },
    {
      title: 'Date',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => moment(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: {
        showTitle: false,
      },
      render: (description) => (
        <Tooltip placement="topLeft" title={description}>
          {description}
        </Tooltip>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Tooltip title="View Details">
          <Button
            type="link"
            size="small"
            icon={<InfoCircleOutlined />}
            onClick={() => showEventDetails(record)}
          />
        </Tooltip>
      ),
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Enhanced Statistics Cards with Real-time Indicators */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Usage"
              value={statistics.totalUsage.toFixed(2)}
              prefix={<DatabaseOutlined />}
              suffix="units"
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Growth: {statistics.usageGrowth > 0 ? '+' : ''}{statistics.usageGrowth.toFixed(1)}%
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Customers"
              value={statistics.activeCustomers}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Avg: {statistics.avgUsagePerCustomer.toFixed(2)} units
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Peak Usage Hour"
              value={`${statistics.peakUsageHour}:00`}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Real-time: {realTimeEnabled ? 'ON' : 'OFF'}
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Alerts (24h)"
              value={statistics.alertsTriggered}
              prefix={<BellOutlined />}
              valueStyle={{ color: statistics.alertsTriggered > 0 ? '#f5222d' : '#52c41a' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Live data points: {liveData.length}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Real-time Controls and Filters */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col span={4}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Text strong>Real-time:</Text>
              <Switch 
                checked={realTimeEnabled}
                onChange={handleRealTimeToggle}
                checkedChildren={<MonitorOutlined />}
                unCheckedChildren="OFF"
              />
            </div>
          </Col>
          <Col span={5}>
            <Select
              placeholder="Select customer"
              allowClear
              style={{ width: '100%' }}
              value={filters.customer_id}
              onChange={(value) => handleFilterChange('customer_id', value)}
            >
              {customers.map(customer => (
                <Option key={customer.id} value={customer.id}>
                  {customer.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={6}>
            <RangePicker
              value={[filters.start_date, filters.end_date]}
              onChange={([start, end]) => {
                handleFilterChange('start_date', start);
                handleFilterChange('end_date', end);
              }}
              style={{ width: '100%' }}
            />
          </Col>
          <Col span={9}>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchData}
                loading={loading}
              >
                Refresh
              </Button>
              <Button
                icon={<BellOutlined />}
                onClick={() => setAlertsDrawerVisible(true)}
                type={alerts.length > 0 ? 'primary' : 'default'}
              >
                Alerts ({alerts.length})
              </Button>
              <Button
                icon={<BarChartOutlined />}
                onClick={() => setAnalyticsDrawerVisible(true)}
              >
                Analytics
              </Button>
              <Button
                icon={<ExportOutlined />}
                onClick={handleExportData}
              >
                Export
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Main Content Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        tabBarExtraContent={
          activeTab === 'usage' && (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateUsage}
            >
              Add Usage Record
            </Button>
          )
        }
      >
        {/* Enhanced Dashboard Tab */}
        <TabPane 
          tab={<span><DashboardOutlined />Dashboard</span>} 
          key="dashboard"
        >
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={12}>
              <Card title="Usage Trends" size="small">
                {trendData.length > 0 ? (
                  <Line {...trendChartConfig} />
                ) : (
                  <Empty description="No trend data available" />
                )}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Usage by Type" size="small">
                {trendData.length > 0 ? (
                  <Line {...usageTypeChartConfig} />
                ) : (
                  <Empty description="No usage type data available" />
                )}
              </Card>
            </Col>
          </Row>
          
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={8}>
              <Card title="Hourly Usage Pattern" size="small">
                <Column {...hourlyChartConfig} />
              </Card>
            </Col>
            <Col span={8}>
              <Card 
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span>Live Data Stream</span>
                    {realTimeEnabled && <Badge status="processing" />}
                  </div>
                }
                size="small"
              >
                {realTimeEnabled && liveData.length > 0 ? (
                  <Line {...liveDataConfig} />
                ) : (
                  <Empty description="Enable real-time monitoring to see live data" />
                )}
              </Card>
            </Col>
            <Col span={8}>
              <Card title="Recent Alerts" size="small">
                {alerts.length > 0 ? (
                  <List
                    size="small"
                    dataSource={alerts.slice(0, 5)}
                    renderItem={(alert) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={
                            <Avatar 
                              icon={alert.severity === 'warning' ? <WarningOutlined /> : <InfoCircleOutlined />}
                              style={{ backgroundColor: alert.severity === 'warning' ? '#fa8c16' : '#1890ff' }}
                            />
                          }
                          title={alert.title}
                          description={
                            <div>
                              <div style={{ fontSize: '12px' }}>{alert.message}</div>
                              <div style={{ fontSize: '10px', color: '#999' }}>
                                {alert.timestamp.fromNow()}
                              </div>
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="No recent alerts" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Enhanced Usage Tracking Tab */}
        <TabPane 
          tab={<span><LineChartOutlined />Usage Tracking</span>} 
          key="usage"
        >
          <Table
            columns={usageColumns}
            dataSource={[...usageRecords, ...liveData.filter(live => !usageRecords.some(record => record.id === live.id))]}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1200 }}
            pagination={{
              pageSize: 15,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `${range[0]}-${range[1]} of ${total} usage records`,
            }}
          />
        </TabPane>

        {/* Enhanced Billing Events Tab */}
        <TabPane 
          tab={<span><CheckCircleOutlined />Billing Events</span>} 
          key="events"
        >
          <Alert
            message="Billing Events Audit Trail"
            description="This section shows all billing-related events for audit and tracking purposes."
            type="info"
            style={{ marginBottom: '16px' }}
          />
          <Table
            columns={eventColumns}
            dataSource={billingEvents}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 15,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `${range[0]}-${range[1]} of ${total} billing events`,
            }}
          />
        </TabPane>
      </Tabs>

      {/* Alerts Drawer */}
      <Drawer
        title="Alert Management"
        placement="right"
        width={500}
        open={alertsDrawerVisible}
        onClose={() => setAlertsDrawerVisible(false)}
      >
        <div style={{ marginBottom: '16px' }}>
          <Title level={4}>Alert Rules</Title>
          {alertRules.map(rule => (
            <Card key={rule.id} size="small" style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Text strong>{rule.name}</Text>
                  <div style={{ fontSize: '12px', color: '#666' }}>{rule.description}</div>
                </div>
                <Switch 
                  checked={rule.enabled}
                  onChange={(enabled) => handleToggleAlertRule(rule.id, enabled)}
                  size="small"
                />
              </div>
            </Card>
          ))}
        </div>
        
        <Divider />
        
        <div>
          <Title level={4}>Recent Alerts</Title>
          <Timeline>
            {alerts.slice(0, 10).map(alert => (
              <Timeline.Item
                key={alert.id}
                color={alert.severity === 'warning' ? 'orange' : 'blue'}
              >
                <div>
                  <Text strong>{alert.title}</Text>
                  <div style={{ fontSize: '12px' }}>{alert.message}</div>
                  <div style={{ fontSize: '10px', color: '#999' }}>
                    {alert.timestamp.format('YYYY-MM-DD HH:mm:ss')}
                  </div>
                </div>
              </Timeline.Item>
            ))}
          </Timeline>
        </div>
      </Drawer>

      {/* Analytics Drawer */}
      <Drawer
        title="Advanced Analytics"
        placement="right"
        width={700}
        open={analyticsDrawerVisible}
        onClose={() => setAnalyticsDrawerVisible(false)}
      >
        <div style={{ marginBottom: '24px' }}>
          <Title level={4}>Customer Analytics</Title>
          {selectedCustomerAnalytics ? (
            <div>
              <Descriptions bordered size="small">
                <Descriptions.Item label="Customer">{selectedCustomerAnalytics.name}</Descriptions.Item>
                <Descriptions.Item label="Total Usage">
                  {usageRecords
                    .filter(r => r.customer_id === selectedCustomerAnalytics.id)
                    .reduce((sum, r) => sum + parseFloat(r.usage_amount || 0), 0)
                    .toFixed(2)} units
                </Descriptions.Item>
              </Descriptions>
            </div>
          ) : (
            <Empty description="Select a customer from the usage table to view detailed analytics" />
          )}
        </div>
        
        <div>
          <Title level={4}>System Performance</Title>
          <Row gutter={16}>
            <Col span={12}>
              <Statistic title="Real-time Updates" value={liveData.length} prefix={<ThunderboltOutlined />} />
            </Col>
            <Col span={12}>
              <Statistic title="Data Points" value={usageRecords.length} prefix={<DatabaseOutlined />} />
            </Col>
          </Row>
        </div>
      </Drawer>

      {/* Usage Record Creation Modal */}
      <Modal
        title="Add Usage Record"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitUsage}
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
                name="usage_type"
                label="Usage Type"
                rules={[{ required: true, message: 'Please select usage type' }]}
              >
                <Select placeholder="Select usage type">
                  <Option value="data">Data</Option>
                  <Option value="voice">Voice</Option>
                  <Option value="sms">SMS</Option>
                  <Option value="other">Other</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="usage_amount"
                label="Usage Amount"
                rules={[{ required: true, message: 'Please enter usage amount' }]}
              >
                <InputNumber
                  min={0}
                  step={0.01}
                  style={{ width: '100%' }}
                  placeholder="Enter amount"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="usage_date"
                label="Usage Date"
                rules={[{ required: true, message: 'Please select usage date' }]}
              >
                <DatePicker
                  showTime
                  style={{ width: '100%' }}
                  format="YYYY-MM-DD HH:mm"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="billing_period"
            label="Billing Period"
          >
            <Input placeholder="e.g., 2024-01" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
          >
            <Input.TextArea
              rows={3}
              placeholder="Additional notes about this usage record"
            />
          </Form.Item>

          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                Create Usage Record
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default UsageTrackingPage;