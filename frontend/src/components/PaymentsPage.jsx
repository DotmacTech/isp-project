import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Spin, Typography, Tag, Button, Modal, Form, Input, Select, InputNumber } from 'antd';
import axios from 'axios';

const { Title } = Typography;

function PaymentsPage() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [form] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      message.error('Authentication required.');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get('/api/v1/billing/payments/', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setPayments(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch payments.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });

    const fetchDropdownData = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      try {
        const [customersRes, methodsRes] = await Promise.all([
          axios.get('/api/v1/customers/', { headers: { Authorization: `Bearer ${token}` }, params: { limit: 1000 } }),
          axios.get('/api/v1/billing/payment-methods/', { headers: { Authorization: `Bearer ${token}` } })
        ]);
        setCustomers(customersRes.data.items);
        setPaymentMethods(methodsRes.data);
      } catch (error) {
        message.error('Failed to fetch data for dropdowns.');
      }
    };
    fetchDropdownData();
  }, [fetchData, pagination.current, pagination.pageSize]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, current: newPagination.current, pageSize: newPagination.pageSize }));
  };

  const handleAdd = () => {
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormFinish = async (values) => {
    const token = localStorage.getItem('access_token');
    try {
      await axios.post('/api/v1/billing/payments/', values, { headers: { Authorization: `Bearer ${token}` } });
      message.success('Payment recorded successfully.');
      setIsModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to record payment.');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Customer ID', dataIndex: 'customer_id', key: 'customer_id' },
    { title: 'Invoice ID', dataIndex: 'invoice_id', key: 'invoice_id' },
    { title: 'Receipt #', dataIndex: 'receipt_number', key: 'receipt_number' },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', render: (amount) => `$${Number(amount).toFixed(2)}` },
    { title: 'Date', dataIndex: 'date', key: 'date', render: (text) => new Date(text).toLocaleDateString() },
  ];

  return (
    <div>
      <Title level={2}>Payments</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Add Payment</Button>
      <Table dataSource={payments} columns={columns} rowKey="id" loading={loading} pagination={pagination} onChange={handleTableChange} />
      <Modal title="Add New Payment" open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
            <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
              {customers.map(c => <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="payment_type_id" label="Payment Method" rules={[{ required: true }]}>
            <Select>
              {paymentMethods.map(m => <Select.Option key={m.id} value={m.id}>{m.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="amount" label="Amount" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} step="0.01" />
          </Form.Item>
          <Form.Item name="receipt_number" label="Receipt / Transaction ID" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="invoice_id" label="Invoice ID (Optional)">
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>
          <Form.Item name="comment" label="Comment"><Input.TextArea /></Form.Item>
          <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Record Payment</Button>
        </Form>
      </Modal>
    </div>
  );
}

export default PaymentsPage;