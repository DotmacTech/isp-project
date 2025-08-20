import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Spin, Typography, Tag, Button, Modal, Form, Input, Select, InputNumber, Space } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;

function InvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [customers, setCustomers] = useState([]);
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
      const response = await axios.get('/api/v1/billing/invoices/', {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          skip: (params.pagination.current - 1) * params.pagination.pageSize,
          limit: params.pagination.pageSize,
        },
      });
      setInvoices(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, current: params.pagination.current }));
    } catch (error) {
      message.error('Failed to fetch invoices.');
      console.error('Error fetching invoices:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ pagination });

    const fetchCustomers = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      try {
        const res = await axios.get('/api/v1/customers/', { headers: { Authorization: `Bearer ${token}` }, params: { limit: 1000 } });
        setCustomers(res.data.items);
      } catch (error) {
        message.error('Failed to fetch customers.');
      }
    };
    fetchCustomers();
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
    const payload = {
      customer_id: values.customer_id,
      items: values.items || [],
    };

    try {
      await axios.post('/api/v1/billing/invoices/', payload, { headers: { Authorization: `Bearer ${token}` } });
      message.success('Invoice created successfully.');
      setIsModalVisible(false);
      fetchData({ pagination });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to create invoice.');
    }
  };

  const calculateTotal = () => {
    const items = form.getFieldValue('items') || [];
    const total = items.reduce((sum, item) => {
      const price = item?.price || 0;
      const quantity = item?.quantity || 0;
      return sum + (price * quantity);
    }, 0);
    form.setFieldsValue({ total: total.toFixed(2) });
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Number', dataIndex: 'number', key: 'number' },
    { title: 'Customer ID', dataIndex: 'customer_id', key: 'customer_id' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const color = status === 'paid' ? 'green' : status === 'overdue' ? 'red' : 'orange';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      render: (amount) => `$${Number(amount).toFixed(2)}`,
    },
    {
      title: 'Due',
      dataIndex: 'due',
      key: 'due',
      render: (amount) => `$${Number(amount).toFixed(2)}`,
    },
    {
      title: 'Date Created',
      dataIndex: 'date_created',
      key: 'date_created',
      render: (text) => new Date(text).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: () => <Button size="small">View Details</Button>, // Placeholder
    },
  ];

  return (
    <div>
      <Title level={2}>Invoices</Title>
      <Button type="primary" onClick={handleAdd} style={{ marginBottom: 16 }}>Create Invoice</Button>
      <Table
        dataSource={invoices}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
      <Modal
        title="Create New Invoice"
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        width={800}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish} onValuesChange={calculateTotal}>
          <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
            <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())} placeholder="Select a customer">
              {customers.map(c => <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>)}
            </Select>
          </Form.Item>

          <Title level={4}>Invoice Items</Title>
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                    <Form.Item {...restField} name={[name, 'description']} rules={[{ required: true, message: 'Missing description' }]}>
                      <Input placeholder="Description" style={{width: '350px'}} />
                    </Form.Item>
                    <Form.Item {...restField} name={[name, 'quantity']} initialValue={1} rules={[{ required: true, message: 'Missing quantity' }]}>
                      <InputNumber placeholder="Qty" min={1} />
                    </Form.Item>
                    <Form.Item {...restField} name={[name, 'price']} rules={[{ required: true, message: 'Missing price' }]}>
                      <InputNumber placeholder="Price" min={0} step="0.01" />
                    </Form.Item>
                    <MinusCircleOutlined onClick={() => remove(name)} />
                  </Space>
                ))}
                <Form.Item>
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    Add Item
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Form.Item name="total" label="Total">
            <InputNumber style={{ width: '100%' }} disabled />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
              Create Invoice
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default InvoicesPage;