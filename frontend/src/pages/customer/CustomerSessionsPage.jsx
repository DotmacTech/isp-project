import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Typography, Table, DatePicker, Spin, Alert, Row, Col, Statistic } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format, parseISO, startOfDay } from 'date-fns';
import apiClient from '../../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const formatBytes = (bytes, decimals = 2) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

const CustomerSessionsPage = () => {
    const { customerId } = useParams();
    const [customer, setCustomer] = useState(null);
    const [sessions, setSessions] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [summary, setSummary] = useState({ totalDownload: 0, totalUpload: 0, sessionCount: 0 });
    const [loading, setLoading] = useState(false);
    const [loadingAggregates, setLoadingAggregates] = useState(false);
    const [error, setError] = useState(null);
    const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    const [dateRange, setDateRange] = useState([dayjs().subtract(7, 'day'), dayjs()]);

    const fetchCustomer = useCallback(async () => {
        if (!customerId) return;
        setLoading(true);
        try {
            const response = await apiClient.get(`/v1/customers/${customerId}/`);
            setCustomer(response.data);
        } catch (err) {
            setError('Failed to fetch customer details.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [customerId]);

    const fetchAggregateData = useCallback(async (dates) => {
        if (!customer || !customer.login || !dates || dates.length !== 2) return;
        setLoadingAggregates(true);
        setError(null);
        try {
            const params = {
                username: customer.login,
                start_date: dates[0].startOf('day').toISOString(),
                end_date: dates[1].endOf('day').toISOString(),
                skip: 0,
                limit: 10000, // A large limit to get all sessions for the range
            };
            const response = await apiClient.get('/v1/freeradius/logs/accounting/', { params });
            const allItems = response.data.items;

            // Process for chart
            const dailyData = allItems.reduce((acc, session) => {
                const day = format(startOfDay(parseISO(session.acctstarttime)), 'yyyy-MM-dd');
                if (!acc[day]) {
                    acc[day] = { date: day, download: 0, upload: 0 };
                }
                acc[day].download += session.acctinputoctets || 0;
                acc[day].upload += session.acctoutputoctets || 0;
                return acc;
            }, {});
            setChartData(Object.values(dailyData).sort((a, b) => new Date(a.date) - new Date(b.date)));

            // Process for summary
            const totalDownload = allItems.reduce((sum, s) => sum + (s.acctinputoctets || 0), 0);
            const totalUpload = allItems.reduce((sum, s) => sum + (s.acctoutputoctets || 0), 0);
            setSummary({ totalDownload, totalUpload, sessionCount: response.data.total });

        } catch (err) {
            setError('Failed to fetch summary and chart data.');
            console.error(err);
        } finally {
            setLoadingAggregates(false);
        }
    }, [customer]);

    const fetchPageData = useCallback(async (currentPagination, dates) => {
        if (!customer || !customer.login || !dates || dates.length !== 2) return;
        setLoading(true);
        setError(null);
        try {
            const params = {
                username: customer.login,
                start_date: dates[0].startOf('day').toISOString(),
                end_date: dates[1].endOf('day').toISOString(),
                skip: (currentPagination.current - 1) * currentPagination.pageSize,
                limit: currentPagination.pageSize,
            };
            const response = await apiClient.get('/v1/freeradius/logs/accounting/', { params });
            setSessions(response.data.items);
            setPagination(pg => ({ ...pg, total: response.data.total, current: currentPagination.current }));
        } catch (err) {
            setError('Failed to fetch session page data.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [customer]);

    useEffect(() => {
        fetchCustomer();
    }, [fetchCustomer]);

    useEffect(() => {
        if (customer && dateRange && dateRange.length === 2) {
            const firstPage = { ...pagination, current: 1 };
            fetchAggregateData(dateRange);
            fetchPageData(firstPage, dateRange);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [customer, dateRange]);

    const handleTableChange = (newPagination) => {
        fetchPageData(newPagination, dateRange);
    };

    const handleDateChange = (dates) => {
        if (dates) {
            setDateRange(dates);
        } else {
            setDateRange([]);
        }
    };

    const columns = [
        { title: 'Session ID', dataIndex: 'acctsessionid', key: 'acctsessionid', width: 200, ellipsis: true },
        {
            title: 'Start Time',
            dataIndex: 'acctstarttime',
            key: 'acctstarttime',
            render: (text) => text ? new Date(text).toLocaleString() : 'N/A',
        },
        {
            title: 'Stop Time',
            dataIndex: 'acctstoptime',
            key: 'acctstoptime',
            render: (text) => text ? new Date(text).toLocaleString() : <Text strong color="green">ONLINE</Text>,
        },
        {
            title: 'Duration (s)',
            dataIndex: 'acctsessiontime',
            key: 'acctsessiontime',
            align: 'right',
        },
        {
            title: 'Download',
            dataIndex: 'acctinputoctets',
            key: 'acctinputoctets',
            align: 'right',
            render: (bytes) => formatBytes(bytes),
        },
        {
            title: 'Upload',
            dataIndex: 'acctoutputoctets',
            key: 'acctoutputoctets',
            align: 'right',
            render: (bytes) => formatBytes(bytes),
        },
        { title: 'IP Address', dataIndex: 'framedipaddress', key: 'framedipaddress' },
        { title: 'NAS IP', dataIndex: 'nasipaddress', key: 'nasipaddress' },
        { title: 'Terminate Cause', dataIndex: 'acctterminatecause', key: 'acctterminatecause' },
    ];

    if (!customer && loading) {
        return <Spin tip="Loading customer..."><div style={{ height: '200px' }} /></Spin>;
    }

    return (
        <Card>
            <Title level={2}>Session History for {customer?.name || `ID: ${customerId}`}</Title>
            {customer?.login && <Text type="secondary">RADIUS Username: {customer.login}</Text>}

            <Row gutter={16} style={{ marginTop: 24, marginBottom: 24 }}>
                <Col>
                    <Text strong>Date Range:</Text>{' '}
                    <RangePicker value={dateRange} onChange={handleDateChange} />
                </Col>
            </Row>

            {error && <Alert message="Error" description={error} type="error" showIcon style={{ marginBottom: 16 }} />}

            <Spin spinning={loadingAggregates}>
                <Row gutter={16} style={{ marginBottom: 24 }}>
                    <Col span={8}>
                        <Card bordered={false}><Statistic title="Total Download" value={formatBytes(summary.totalDownload)} /></Card>
                    </Col>
                    <Col span={8}>
                        <Card bordered={false}><Statistic title="Total Upload" value={formatBytes(summary.totalUpload)} /></Card>
                    </Col>
                    <Col span={8}>
                        <Card bordered={false}><Statistic title="Total Sessions" value={summary.sessionCount} /></Card>
                    </Col>
                </Row>

                <Title level={4}>Daily Usage</Title>
                <Card style={{ marginBottom: 24 }}>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" />
                            <YAxis tickFormatter={(value) => formatBytes(value)} />
                            <Tooltip formatter={(value, name) => [formatBytes(value), name]} />
                            <Legend />
                            <Line type="monotone" dataKey="download" stroke="#8884d8" name="Download" dot={false} />
                            <Line type="monotone" dataKey="upload" stroke="#82ca9d" name="Upload" dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </Card>
            </Spin>

            <Title level={4}>Session Details</Title>
            <Table
                loading={loading}
                columns={columns}
                dataSource={sessions}
                rowKey="radacctid"
                pagination={pagination}
                onChange={handleTableChange}
                scroll={{ x: 1300 }}
            />
        </Card>
    );
};

export default CustomerSessionsPage;