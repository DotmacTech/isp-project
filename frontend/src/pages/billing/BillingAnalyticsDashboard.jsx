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
    <div className="p-6">
      <Title level={2}>Billing Analytics Dashboard</Title>
      
      {/* Controls and Filters */}
      <Card className="mb-6">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <RangePicker 
                value={dateRange}
                onChange={handleDateRangeChange}
                allowClear={false}
              />
              <Select value={selectedPeriod} onChange={handlePeriodChange} className="w-30">
                <Option value="7days">Last 7 Days</Option>
                <Option value="30days">Last 30 Days</Option>
                <Option value="90days">Last 90 Days</Option>
                <Option value="year">Last Year</Option>
              </Select>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button onClick={runManualBilling} loading={loading}>Run Billing</Button>
              <Button onClick={runDunningProcess} loading={loading}>Run Dunning</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* System Health */}
      {systemHealth && (
        <Card className="mb-6">
          <Title level={4}>System Health</Title>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={8}>
              <Statistic
                title="Billing Engine"
                value={systemHealth.billing_engine_status}
                valueStyle={{ color: systemHealth.billing_engine_status === 'healthy' ? '#52c41a' : '#ff4d4f' }}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title="Payment Processing"
                value={systemHealth.payment_processing_status}
                valueStyle={{ color: systemHealth.payment_processing_status === 'healthy' ? '#52c41a' : '#ff4d4f' }}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title="Dunning Process"
                value={systemHealth.dunning_status}
                valueStyle={{ color: systemHealth.dunning_status === 'healthy' ? '#52c41a' : '#ff4d4f' }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Quick Stats */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Revenue"
              value={revenueData?.total_revenue || 0}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Outstanding Balance"
              value={agingData?.total_outstanding || 0}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Payment Success Rate"
              value={Math.round((paymentData?.payment_success_rate || 0) * 100)}
              suffix="%"
              valueStyle={{ color: paymentData?.payment_success_rate > 0.8 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Active Customers"
              value={revenueData?.active_customers || 0}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts and Detailed Analytics */}
      <Tabs defaultActiveKey="overview" type="card"
        items={[
          {
            key: 'overview',
            label: 'Overview',
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Revenue Trend" className="h-100">
                    {revenueChartData.length > 0 ? (
                      <Line {...revenueConfig} />
                    ) : (
                      <div className="text-center pt-25">
                        <Spin />
                        <p>Loading revenue data...</p>
                      </div>
                    )}
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="Accounts Receivable Aging" className="h-100">
                    {agingChartData.length > 0 ? (
                      <Column {...agingConfig} />
                    ) : (
                      <div className="text-center pt-25">
                        <Spin />
                        <p>Loading aging data...</p>
                      </div>
                    )}
                  </Card>
                </Col>
              </Row>
            )
          },
          {
            key: 'payments',
            label: 'Payment Analysis',
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Payment Methods Distribution" className="h-100">
                    {paymentMethodData.length > 0 ? (
                      <Pie {...paymentMethodConfig} />
                    ) : (
                      <div className="text-center pt-25">
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
            )
          },
          {
            key: 'revenue',
            label: 'Revenue Breakdown',
            children: (
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
                          <Row key={service} justify="space-between" className="py-2">
                            <Col>{service.charAt(0).toUpperCase() + service.slice(1)}</Col>
                            <Col>${parseFloat(amount).toFixed(2)}</Col>
                          </Row>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center p-12">
                        <Spin />
                        <p>Loading service breakdown...</p>
                      </div>
                    )}
                  </Card>
                </Col>
              </Row>
            )
          }
        ]}
      />
    </div>
  );
}

export default BillingAnalyticsDashboard;
