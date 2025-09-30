import React, { useState, useEffect, useCallback } from 'react';
import { Table, Card, Button, Tag, Spin, notification, Typography, Space } from 'antd';
import { EditOutlined, PlusOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { customerBillingConfigAPI } from '../../services/billingAPI';

const { Title } = Typography;

const CustomerBillingConfigPage = () => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const navigate = useNavigate();

  const fetchData = useCallback(async (pageParams) => {
    setLoading(true);
    try {
      const response = await customerBillingConfigAPI.getAll({
        skip: (pageParams.current - 1) * pageParams.pageSize,
        limit: pageParams.pageSize,
      });
      setConfigs(response.data.items);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        current: pageParams.current,
        pageSize: pageParams.pageSize,
      }));
    } catch (error) {
      console.error("Error fetching customer billing configs:", error);
      notification.error({
        message: 'Fetch Error',
        description: 'Could not fetch customer billing configurations. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ current: 1, pageSize: 10 });
  }, [fetchData]);

  const handleTableChange = (newPagination) => {
    fetchData({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    });
  };

  const handleEdit = (customerId) => {
    navigate(`/dashboard/billing/customer-config/${customerId}/edit`);
  };

  const columns = [
    {
      title: 'Customer',
      dataIndex: ['customer', 'name'],
      key: 'customer',
      render: (text, record) => (
        <Link to={`/dashboard/customers/${record.customer_id}`}>{record.customer?.name || 'N/A'}</Link>
      ),
    },
    {
      title: 'Billing Cycle',
      dataIndex: ['billing_cycle', 'name'],
      key: 'billing_cycle',
      render: (text, record) => record.billing_cycle?.name || 'N/A',
    },
    {
      title: 'Billing Day',
      key: 'billing_day',
      render: (_, record) => {
        const day = record.custom_billing_day || record.billing_cycle?.billing_day;
        return day ? `Day ${day}` : 'N/A';
      },
    },
    {
      title: 'Auto-Payment',
      dataIndex: 'auto_payment_enabled',
      key: 'auto_payment_enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'default'}>
          {enabled ? 'Enabled' : 'Disabled'}
        </Tag>
      ),
    },
    {
      title: 'Dunning',
      dataIndex: 'dunning_enabled',
      key: 'dunning_enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'blue' : 'default'}>
          {enabled ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Invoice Delivery',
      dataIndex: 'invoice_delivery_method',
      key: 'invoice_delivery_method',
    },
    {
      title: 'Actions',
      key: 'actions',
      align: 'center',
      render: (_, record) => (
        <Button
          type="primary"
          icon={<EditOutlined />}
          onClick={() => handleEdit(record.customer_id)}
        >
          Edit
        </Button>
      ),
    },
  ];

  return (
    <Card
      title={<Title level={4}>Customer Billing Configurations</Title>}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/dashboard/billing/customer-config/new')}
        >
          Add Configuration
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={configs}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        scroll={{ x: 'max-content' }}
      />
    </Card>
  );
};

export default CustomerBillingConfigPage;