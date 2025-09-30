import React, { useState, useEffect, useCallback } from 'react';
import {
  Select,
  Button,
  Spin,
  Alert,
  Row,
  Col,
  Card,
  Typography,
  message,
  Radio,
} from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import LineChart from '../../components/network/LineChart';
import StatCard from '../../components/network/StatCard';

const { Option } = Select;
const { Title } = Typography;

const TIME_RANGES = {
  '1h': { label: 'Last 1 Hour', hours: 1 },
  '6h': { label: 'Last 6 Hours', hours: 6 },
  '24h': { label: 'Last 24 Hours', hours: 24 },
  '7d': { label: 'Last 7 Days', hours: 168 },
};

const PerformanceAnalyticsDashboard = () => {
  const [devices, setDevices] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState('');
  const [selectedMetric, setSelectedMetric] = useState('');
  const [timeRange, setTimeRange] = useState('24h');

  const [chartData, setChartData] = useState({ labels: [], datasets: [] });
  const [summaryStats, setSummaryStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch devices and metrics on component mount
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [devicesData, metricsData] = await Promise.all([
          apiClient.get('/v1/network/monitoring-devices/', { params: { limit: 1000 } }),
          apiClient.get('/v1/network/performance/metrics/', { params: { limit: 1000 } }),
        ]);
        setDevices(devicesData.data.items || []);
        setMetrics(metricsData.data.items || []);
        if (devicesData.data.items && devicesData.data.items.length > 0) {
          setSelectedDevice(devicesData.data.items[0].id.toString());
        }
        if (metricsData.data.items && metricsData.data.items.length > 0) {
          setSelectedMetric(metricsData.data.items[0].id.toString());
        }
      } catch (err) {
        message.error('Failed to load initial device and metric data.');
        setError('Failed to load initial device and metric data.');
      }
    };
    fetchInitialData();
  }, []);

  // Fetch chart data when selections change
  const fetchPerformanceData = useCallback(async () => {
    if (!selectedDevice || !selectedMetric) return;

    setLoading(true);
    setError(null);
    setChartData({ labels: [], datasets: [] }); // Clear previous data
    setSummaryStats(null);

    try {
      const { hours } = TIME_RANGES[timeRange];
      const endDate = new Date();
      const startDate = new Date(endDate.getTime() - hours * 60 * 60 * 1000);

      const params = {
        device_id: selectedDevice,
        metric_id: selectedMetric,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        limit: 1000, // Fetch up to 1000 data points for the chart
      };

      const response = await apiClient.get('/v1/network/performance/data/', { params });
      const data = response.data;

      const currentMetric = metrics.find(m => m.id.toString() === selectedMetric);
      const currentDevice = devices.find(d => d.id.toString() === selectedDevice);

      if (data && data.items && data.items.length > 0) {
        const sortedData = data.items.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        const labels = sortedData.map(d => new Date(d.timestamp).toLocaleString());
        const values = sortedData.map(d => d.value);

        setChartData({
          labels,
          datasets: [
            {
              label: `${currentMetric?.metric_name} for ${currentDevice?.title} (${currentMetric?.unit})`,
              data: values,
              borderColor: 'rgb(75, 192, 192)',
              backgroundColor: 'rgba(75, 192, 192, 0.5)',
              tension: 0.1,
            },
          ],
        });

        // Calculate summary stats
        const numericValues = values.map(v => parseFloat(v));
        setSummaryStats({
          average: (numericValues.reduce((a, b) => a + b, 0) / numericValues.length).toFixed(2),
          max: Math.max(...numericValues).toFixed(2),
          min: Math.min(...numericValues).toFixed(2),
          unit: currentMetric?.unit,
        });

      } else {
        setError('No data available for the selected criteria.');
        setChartData({ labels: [], datasets: [] });
        setSummaryStats(null);
      }
    } catch (err) {
      message.error(`Failed to fetch performance data: ${err.message}`);
      setError(`Failed to fetch performance data: ${err.message}`);
      setChartData({ labels: [], datasets: [] });
      setSummaryStats(null);
    } finally {
      setLoading(false);
    }
  }, [selectedDevice, selectedMetric, timeRange, devices, metrics]);

  useEffect(() => {
    fetchPerformanceData();
  }, [fetchPerformanceData]);

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>Performance Analytics</Title>

      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="bottom">
          <Col>
            <Typography.Text strong>Device:</Typography.Text>
            <Select
              value={selectedDevice}
              style={{ width: 200 }}
              onChange={value => setSelectedDevice(value)}
              loading={devices.length === 0}
            >
              {devices.map(d => (
                <Option key={d.id} value={d.id.toString()}>
                  {d.title} ({d.ip})
                </Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Typography.Text strong>Metric:</Typography.Text>
            <Select
              value={selectedMetric}
              style={{ width: 200 }}
              onChange={value => setSelectedMetric(value)}
              loading={metrics.length === 0}
            >
              {metrics.map(m => (
                <Option key={m.id} value={m.id.toString()}>
                  {m.metric_name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Typography.Text strong>Time Range:</Typography.Text>
            <Radio.Group value={timeRange} onChange={e => setTimeRange(e.target.value)} buttonStyle="solid">
              {Object.entries(TIME_RANGES).map(([key, { label }]) => (
                <Radio.Button key={key} value={key}>
                  {label}
                </Radio.Button>
              ))}
            </Radio.Group>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={fetchPerformanceData}
              loading={loading}
            >
              Refresh Data
            </Button>
          </Col>
        </Row>
      </Card>

      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 24 }} />}

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <StatCard title="Average" value={summaryStats?.average ?? 'N/A'} unit={summaryStats?.unit} />
        </Col>
        <Col xs={24} sm={8}>
          <StatCard title="Maximum" value={summaryStats?.max ?? 'N/A'} unit={summaryStats?.unit} />
        </Col>
        <Col xs={24} sm={8}>
          <StatCard title="Minimum" value={summaryStats?.min ?? 'N/A'} unit={summaryStats?.unit} />
        </Col>
      </Row>

      <Card>
        <Spin spinning={loading} tip="Loading chart data...">
          <div style={{ height: 400 }}>
            {chartData.labels.length > 0 ? (
              <LineChart chartData={chartData} titleText="Metric Trend" />
            ) : (
              !error && <Alert message="Select a device and metric to view data." type="info" showIcon />
            )}
          </div>
        </Spin>
      </Card>
    </div>
  );
};

export default PerformanceAnalyticsDashboard;