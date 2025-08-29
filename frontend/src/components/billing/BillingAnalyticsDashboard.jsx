import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  DatePicker,
  Select,
  Table,
  Button,
  Typography,
  Space,
  Alert,
  Spin,
  message,
  Tabs,
  Progress,
  Divider
} from 'antd';
import {
  DollarOutlined,
  FileTextOutlined,
  CreditCardOutlined,
  ExclamationCircleOutlined,
  RiseOutlined,
  DownloadOutlined,
  SyncOutlined
} from '@ant-design/icons';
import { Line, Column, Pie } from '@ant-design/plots';
import moment from 'moment';
import billingAPI from '../../services/billingAPI';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

function BillingAnalyticsDashboard() {
  // State management
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState([
    moment().subtract(30, 'days'),
    moment()
  ]);
  const [selectedPeriod, setSelectedPeriod] = useState('30days');
  
  // Analytics data
  const [revenueData, setRevenueData] = useState(null);
  const [agingData, setAgingData] = useState(null);
  const [paymentData, setPaymentData] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  
  // Charts data
  const [revenueChartData, setRevenueChartData] = useState([]);
  const [agingChartData, setAgingChartData] = useState([]);
  const [paymentMethodData, setPaymentMethodData] = useState([]);

  useEffect(() => {
    loadDashboardData();
    loadSystemHealth();
  }, [dateRange]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [startDate, endDate] = dateRange;
      const start = startDate.format('YYYY-MM-DD');
      const end = endDate.format('YYYY-MM-DD');

      // Load all analytics in parallel
      const [revenueResponse, agingResponse, paymentResponse] = await Promise.all([
        billingAPI.analytics.getRevenueAnalytics({
          start_date: start,
          end_date: end,
          report_type: 'revenue_summary'
        }),
        billingAPI.analytics.getAgingAnalytics({
          start_date: start,
          end_date: end,
          report_type: 'aging_report'
        }),
        billingAPI.analytics.getPaymentAnalytics({
          start_date: start,
          end_date: end,
          report_type: 'payment_analysis'
        })
      ]);

      setRevenueData(revenueResponse.data);
      setAgingData(agingResponse.data);
      setPaymentData(paymentResponse.data);

      // Process data for charts
      processChartData(revenueResponse.data, agingResponse.data, paymentResponse.data);

    } catch (error) {
      message.error('Failed to load analytics data');
      console.error('Analytics loading error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSystemHealth = async () => {
    try {
      const response = await billingAPI.billingEngine.healthCheck();
      setSystemHealth(response.data);
    } catch (error) {
      console.error('System health check failed:', error);
    }
  };

  const processChartData = (revenue, aging, payments) => {
    // Process revenue chart data
    if (revenue?.revenue_by_month) {
      const chartData = Object.entries(revenue.revenue_by_month).map(([month, amount]) => ({
        month,
        revenue: parseFloat(amount)
      }));
      setRevenueChartData(chartData);
    }

    // Process aging chart data
    if (aging?.aging_buckets) {
      const chartData = Object.entries(aging.aging_buckets).map(([bucket, amount]) => ({
        category: bucket.replace('_', '-').replace('days', ' days'),
        amount: parseFloat(amount)
      }));
      setAgingChartData(chartData);
    }

    // Process payment method data
    if (payments?.payments_by_method) {
      const chartData = Object.entries(payments.payments_by_method).map(([method, amount]) => ({
        method,
        amount: parseFloat(amount)
      }));
      setPaymentMethodData(chartData);
    }
  };

  const handleDateRangeChange = (dates) => {
    setDateRange(dates);
    setSelectedPeriod('custom');
  };

  const handlePeriodChange = (period) => {
    setSelectedPeriod(period);
    let newRange;
    switch (period) {
      case '7days':
        newRange = [moment().subtract(7, 'days'), moment()];
        break;
      case '30days':
        newRange = [moment().subtract(30, 'days'), moment()];
        break;
      case '90days':
        newRange = [moment().subtract(90, 'days'), moment()];
        break;
      case 'year':
        newRange = [moment().subtract(1, 'year'), moment()];
        break;
      default:
        return;
    }
    setDateRange(newRange);
  };

  const runManualBilling = async () => {
    try {
      setLoading(true);
      const response = await billingAPI.billingEngine.runBilling();
      message.success('Billing run completed successfully');
      console.log('Billing result:', response.data);
      loadDashboardData(); // Refresh data
    } catch (error) {
      message.error('Billing run failed');
      console.error('Billing run error:', error);
    } finally {
      setLoading(false);
    }
  };

  const runDunningProcess = async () => {
    try {
      setLoading(true);
      const response = await billingAPI.billingEngine.runDunning();
      message.success('Dunning process completed successfully');
      console.log('Dunning result:', response.data);
      loadDashboardData(); // Refresh data
    } catch (error) {
      message.error('Dunning process failed');
      console.error('Dunning process error:', error);
    } finally {
      setLoading(false);
    }
  };

  const revenueConfig = {
    data: revenueChartData,
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

  const agingConfig = {
    data: agingChartData,
    xField: 'category',
    yField: 'amount',
    color: ({ category }) => {
      if (category.includes('current')) return '#52c41a';
      if (category.includes('1-30')) return '#faad14';
      if (category.includes('31-60')) return '#fa8c16';
      if (category.includes('61-90')) return '#f5222d';
      return '#722ed1';
    },
  };

  const paymentMethodConfig = {
    data: paymentMethodData,
    angleField: 'amount',
    colorField: 'method',
    radius: 0.8,
    label: {
      type: 'spider',
      labelHeight: 28,
      content: '{name}\n{percentage}',
    },
    interactions: [
      {
        type: 'element-selected',
      },
      {
        type: 'element-active',
      },
    ],
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2}>Billing Analytics Dashboard</Title>
        </Col>
        <Col>
          <Space>
            <Select
              value={selectedPeriod}
              onChange={handlePeriodChange}
              style={{ width: 120 }}
            >
              <Option value="7days">Last 7 days</Option>
              <Option value="30days">Last 30 days</Option>
              <Option value="90days">Last 90 days</Option>
              <Option value="year">Last year</Option>
              <Option value="custom">Custom</Option>
            </Select>
            <RangePicker
              value={dateRange}
              onChange={handleDateRangeChange}
              format="YYYY-MM-DD"
            />
            <Button
              type="primary"
              icon={<SyncOutlined />}
              onClick={loadDashboardData}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        </Col>
      </Row>

      {/* System Health Alert */}
      {systemHealth && (
        <Alert
          message={`System Status: ${systemHealth.status}`}
          description={`Database: ${systemHealth.database_connection} | Recent billing runs: ${systemHealth.recent_billing_runs} | Total outstanding: $${parseFloat(systemHealth.total_outstanding || 0).toFixed(2)}`}
          type={systemHealth.status === 'healthy' ? 'success' : 'warning'}
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* Key Metrics Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Revenue"
              value={revenueData?.total_revenue || 0}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="USD"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Outstanding Amount"
              value={agingData?.total_outstanding || 0}
              precision={2}
              prefix={<ExclamationCircleOutlined />}
              suffix="USD"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Payments"
              value={paymentData?.total_payments || 0}
              precision={2}
              prefix={<CreditCardOutlined />}
              suffix="USD"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Invoice Count"
              value={revenueData?.invoice_count || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Action Buttons */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col>
          <Button
            type="primary"
            icon={<RiseOutlined />}
            onClick={runManualBilling}
            loading={loading}
          >
            Run Manual Billing
          </Button>
        </Col>
        <Col>
          <Button
            icon={<ExclamationCircleOutlined />}
            onClick={runDunningProcess}
            loading={loading}
          >
            Run Dunning Process
          </Button>
        </Col>
        <Col>
          <Button icon={<DownloadOutlined />}>
            Export Report
          </Button>
        </Col>
      </Row>

      {/* Charts and Detailed Analytics */}
      <Tabs defaultActiveKey="overview" type="card">
        <TabPane tab="Overview" key="overview">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Revenue Trend" style={{ height: '400px' }}>
                {revenueChartData.length > 0 ? (
                  <Line {...revenueConfig} />
                ) : (
                  <div style={{ textAlign: 'center', paddingTop: '100px' }}>
                    <Spin />
                    <p>Loading revenue data...</p>
                  </div>
                )}
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Accounts Receivable Aging" style={{ height: '400px' }}>
                {agingChartData.length > 0 ? (
                  <Column {...agingConfig} />
                ) : (
                  <div style={{ textAlign: 'center', paddingTop: '100px' }}>
                    <Spin />
                    <p>Loading aging data...</p>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Payment Analysis" key="payments">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Payment Methods Distribution" style={{ height: '400px' }}>
                {paymentMethodData.length > 0 ? (
                  <Pie {...paymentMethodConfig} />
                ) : (
                  <div style={{ textAlign: 'center', paddingTop: '100px' }}>
                    <Spin />
                    <p>Loading payment data...</p>
                  </div>
                )}
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Payment Statistics">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Statistic
                      title="Payment Count"
                      value={paymentData?.payment_count || 0}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Average Payment"
                      value={paymentData?.average_payment_amount || 0}
                      precision={2}
                      prefix="$"
                    />
                  </Col>
                  <Col span={24}>
                    <Divider />
                    <Title level={5}>Payment Success Rate</Title>
                    <Progress
                      percent={Math.round((paymentData?.payment_success_rate || 0) * 100)}
                      status="active"
                      strokeColor={{
                        from: '#108ee9',
                        to: '#87d068',
                      }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Revenue Breakdown" key="revenue">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={8}>
              <Card title="Revenue Summary">
                <Statistic
                  title="Gross Revenue"
                  value={revenueData?.total_revenue || 0}
                  precision={2}
                  prefix="$"
                />
                <Divider />
                <Statistic
                  title="Total Tax"
                  value={revenueData?.total_tax || 0}
                  precision={2}
                  prefix="$"
                />
                <Divider />
                <Statistic
                  title="Net Revenue"
                  value={revenueData?.net_revenue || 0}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: '#3f8600', fontWeight: 'bold' }}
                />
              </Card>
            </Col>
            <Col xs={24} lg={16}>
              <Card title="Revenue by Service Type">
                {revenueData?.revenue_by_service_type ? (
                  <div>
                    {Object.entries(revenueData.revenue_by_service_type).map(([service, amount]) => (
                      <Row key={service} justify="space-between" style={{ padding: '8px 0' }}>
                        <Col>{service.charAt(0).toUpperCase() + service.slice(1)}</Col>
                        <Col>${parseFloat(amount).toFixed(2)}</Col>
                      </Row>
                    ))}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '50px' }}>
                    <Spin />
                    <p>Loading service breakdown...</p>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
}

export default BillingAnalyticsDashboard;