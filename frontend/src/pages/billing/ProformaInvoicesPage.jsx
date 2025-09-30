import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Typography, Card, Row, Col, Select, DatePicker, Tag } from 'antd';
import apiClient from '../../services/api';
import moment from 'moment';

const { Title } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const ProformaInvoicesPage = () => {
  const [proformaInvoices, setProformaInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 15, total: 0 });
  const [filters, setFilters] = useState({
    customer_id: null,
    date_range: [],
    status: null,
  });

  const fetchProformaInvoices = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const queryParams = {
        skip: (params.pagination.current - 1) * params.pagination.pageSize,
        limit: params.pagination.pageSize,
        customer_id: filters.customer_id,
        status: filters.status,
      };

      if (filters.date_range && filters.date_range.length === 2) {
        queryParams.start_date = filters.date_range[0].format('YYYY-MM-DD');
        queryParams.end_date = filters.date_range[1].format('YYYY-MM-DD');
      }

      const response = await apiClient.get('/v1/proforma-invoices/', { params: queryParams });
      setProformaInvoices(response.data.items);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        current: params.pagination.current,
      }));
    } catch (error) {
      message.error('Failed to fetch proforma invoices.');
      console.error('Error fetching proforma invoices:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.pageSize]);

  useEffect(() => {
    fetchProformaInvoices({ pagination });
  }, [fetchProformaInvoices, pagination.current, pagination.pageSize, filters]);

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const response = await apiClient.get('/v1/customers/', { params: { limit: 1000 } });
        setCustomers(response.data.items);
      } catch (error) {
        message.error('Failed to fetch customers.');
      }
    };
    fetchCustomers();
  }, []);

  const handleTableChange = (newPagination) => {
    fetchProformaInvoices({ pagination: newPagination });
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const columns = [
    { title: 'Number', dataIndex: 'number', key: 'number' },
    { title: 'Customer', dataIndex: ['customer', 'name'], key: 'customer' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        let color;
        if (status === 'paid') color = 'green';
        else if (status === 'not_paid') color = 'orange';
        else color = 'blue';
        return <Tag color={color}>{status.replace('_', ' ').toUpperCase()}</Tag>;
      },
    },
    { title: 'Total', dataIndex: 'total', key: 'total', render: (text) => `$${Number(text).toFixed(2)}` },
    { title: 'Date Created', dataIndex: 'date_created', key: 'date_created', render: (text) => moment(text).format('YYYY-MM-DD') },
  ];

  return (
    <div>
      <Title level={2}>Proforma Invoices</Title>
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Select
              showSearch
              allowClear
              placeholder="Filter by customer"
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('customer_id', value)}
              filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}
            >
              {customers.map(c => <Option key={c.id} value={c.id}>{c.name}</Option>)}
            </Select>
          </Col>
          <Col span={8}>
            <RangePicker style={{ width: '100%' }} onChange={(dates) => handleFilterChange('date_range', dates)} />
          </Col>
          <Col span={8}>
            <Select
              allowClear
              placeholder="Filter by status"
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('status', value)}
            >
              <Option value="not_paid">Not Paid</Option>
              <Option value="paid">Paid</Option>
              <Option value="pending">Pending</Option>
            </Select>
          </Col>
        </Row>
      </Card>
      <Table
        dataSource={proformaInvoices}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
    </div>
  );
};

export default ProformaInvoicesPage;