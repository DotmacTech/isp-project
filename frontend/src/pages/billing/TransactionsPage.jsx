import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Typography, Card, Row, Col, Select, DatePicker, Tag } from 'antd';
import apiClient from '../../services/api';
import moment from 'moment';

const { Title } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const TransactionsPage = () => {
  const [transactions, setTransactions] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 15, total: 0 });
  const [filters, setFilters] = useState({
    customer_id: null,
    date_range: [],
    type: null,
  });

  const fetchTransactions = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const queryParams = {
        skip: (params.pagination.current - 1) * params.pagination.pageSize,
        limit: params.pagination.pageSize,
        customer_id: filters.customer_id,
        type: filters.type,
      };

      if (filters.date_range && filters.date_range.length === 2) {
        queryParams.start_date = filters.date_range[0].format('YYYY-MM-DD');
        queryParams.end_date = filters.date_range[1].format('YYYY-MM-DD');
      }

      const response = await apiClient.get('/v1/transactions/', { params: queryParams });
      setTransactions(response.data.items);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        current: params.pagination.current,
      }));
    } catch (error) {
      message.error('Failed to fetch transactions.');
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.pageSize]);

  useEffect(() => {
    fetchTransactions({ pagination });
  }, [fetchTransactions, pagination.current, pagination.pageSize, filters]);

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
    fetchTransactions({ pagination: newPagination });
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Customer', dataIndex: ['customer', 'name'], key: 'customer' },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => {
        const color = type === 'debit' ? 'green' : 'volcano';
        return <Tag color={color}>{type.toUpperCase()}</Tag>;
      },
    },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: 'Total', dataIndex: 'total', key: 'total', render: (text) => `$${Number(text).toFixed(2)}` },
    { title: 'Date', dataIndex: 'date', key: 'date', render: (text) => moment(text).format('YYYY-MM-DD') },
    { title: 'Category', dataIndex: ['category', 'name'], key: 'category' },
    { title: 'Invoice ID', dataIndex: 'invoice_id', key: 'invoice_id' },
  ];

  return (
    <div>
      <Title level={2}>Transactions</Title>
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
              placeholder="Filter by type"
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('type', value)}
            >
              <Option value="debit">Debit (Income)</Option>
              <Option value="credit">Credit (Charge)</Option>
            </Select>
          </Col>
        </Row>
      </Card>
      <Table
        dataSource={transactions}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
    </div>
  );
};

export default TransactionsPage;