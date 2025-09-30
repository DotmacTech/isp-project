import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Spin, message, Typography, Select } from 'antd';
import { UserOutlined, WifiOutlined, PoweroffOutlined } from '@ant-design/icons';
import { Line } from '@ant-design/plots';
import { getSessionStats, getSessionHistoryChart } from '../../services/freeRadiusApi';

const { Title } = Typography;
const { Option } = Select;

const SessionDashboard = () => {
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingChart, setLoadingChart] = useState(true);
  const [chartHours, setChartHours] = useState(24);

  useEffect(() => {
    const fetchStats = async () => {
      setLoadingStats(true);
      try {
        const response = await getSessionStats();
        setStats(response.data);
      } catch (error) {
        message.error('Failed to load session statistics.');
      } finally {
        setLoadingStats(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh stats every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchChartData = async () => {
      setLoadingChart(true);
      try {
        const response = await getSessionHistoryChart({ hours: chartHours, points: chartHours });
        setChartData(response.data);
      } catch (error) {
        message.error('Failed to load session history chart.');
      } finally {
        setLoadingChart(false);
      }
    };

    fetchChartData();
  }, [chartHours]);

  const chartConfig = {
    data: chartData,
    xField: 'time',
    yField: 'value',
    seriesField: 'type',
    smooth: true,
    height: 350,
    xAxis: {
      type: 'time',
      mask: 'YYYY-MM-DD HH:mm',
    },
    yAxis: {
      label: {
        formatter: (v) => `${v}`,
      },
      title: {
        text: 'Online Users'
      }
    },
    tooltip: {
      formatter: (datum) => ({ name: 'Online Users', value: datum.value }),
    },
  };

  return (
    <div>
      <Title level={2}>Session Dashboard</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Spin spinning={loadingStats}>
              <Statistic
                title="Online Users"
                value={stats?.online_count}
                prefix={<WifiOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Spin>
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Spin spinning={loadingStats}>
              <Statistic
                title="Offline Users"
                value={stats?.offline_count}
                prefix={<PoweroffOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Spin>
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Spin spinning={loadingStats}>
              <Statistic
                title="Total Active Services"
                value={stats?.total_services}
                prefix={<UserOutlined />}
              />
            </Spin>
          </Card>
        </Col>
      </Row>

      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col><Title level={4}>Online Users History</Title></Col>
          <Col><Select value={chartHours} onChange={setChartHours}><Option value={12}>Last 12 Hours</Option><Option value={24}>Last 24 Hours</Option><Option value={48}>Last 48 Hours</Option><Option value={168}>Last 7 Days</Option></Select></Col>
        </Row>
        <Spin spinning={loadingChart}><Line {...chartConfig} /></Spin>
      </Card>
    </div>
  );
};

export default SessionDashboard;