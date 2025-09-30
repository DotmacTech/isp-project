import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Card,
  Button,
  Tag,
  Spin,
  notification,
  Typography,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Popconfirm
} from 'antd';
import { EditOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { paymentGatewaysAPI } from '../../services/billingAPI';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const PaymentGatewaysPage = () => {
  const [gateways, setGateways] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingGateway, setEditingGateway] = useState(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async (pageParams) => {
    setLoading(true);
    try {
      const response = await paymentGatewaysAPI.getAll({
        skip: (pageParams.current - 1) * pageParams.pageSize,
        limit: pageParams.pageSize,
      });
      setGateways(response.data.items);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        current: pageParams.current,
        pageSize: pageParams.pageSize,
      }));
    } catch (error) {
      console.error("Error fetching payment gateways:", error);
      notification.error({
        message: 'Fetch Error',
        description: 'Could not fetch payment gateways. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ current: 1, pageSize: 10 });
  }, [fetchData]);

  const handleTableChange = (newPagination) => {
    fetchData(newPagination);
  };

  const handleAdd = () => {
    setEditingGateway(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true });
    setIsModalVisible(true);
  };

  const handleEdit = (gateway) => {
    setEditingGateway(gateway);
    form.setFieldsValue({
      ...gateway,
      config: gateway.config ? JSON.stringify(gateway.config, null, 2) : ''
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await paymentGatewaysAPI.delete(id);
      notification.success({ message: 'Payment gateway deleted successfully.' });
      fetchData(pagination);
    } catch (error) {
      notification.error({
        message: 'Delete Failed',
        description: error.response?.data?.detail || 'Could not delete payment gateway.',
      });
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingGateway(null);
  };

  const handleFormFinish = async (values) => {
    setLoading(true);
    try {
      let payload = { ...values };
      if (payload.config) {
        try {
          payload.config = JSON.parse(payload.config);
        } catch (e) {
          notification.error({ message: 'Invalid JSON in config field.' });
          setLoading(false);
          return;
        }
      } else {
        payload.config = {};
      }

      if (editingGateway) {
        await paymentGatewaysAPI.update(editingGateway.id, payload);
        notification.success({ message: 'Payment gateway updated successfully.' });
      } else {
        await paymentGatewaysAPI.create(payload);
        notification.success({ message: 'Payment gateway created successfully.' });
      }
      setIsModalVisible(false);
      fetchData(pagination);
    } catch (error) {
      notification.error({
        message: 'Save Failed',
        description: error.response?.data?.detail || 'Could not save payment gateway.',
      });
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name', sorter: (a, b) => a.name.localeCompare(b.name) },
    { title: 'Type', dataIndex: 'gateway_type', key: 'gateway_type' },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      align: 'center',
      render: (_, record) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm
            title="Are you sure you want to delete this gateway?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button icon={<DeleteOutlined />} danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title={<Title level={4}>Payment Gateway Management</Title>}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          Add Gateway
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={gateways}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        scroll={{ x: 'max-content' }}
      />
      <Modal
        title={editingGateway ? 'Edit Payment Gateway' : 'Add Payment Gateway'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnHidden
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="name" label="Gateway Name" rules={[{ required: true }]}>
            <Input placeholder="e.g., Stripe, PayPal" />
          </Form.Item>
          <Form.Item name="gateway_type" label="Gateway Type" rules={[{ required: true }]}>
            <Select placeholder="Select a type">
              <Option value="stripe">Stripe</Option>
              <Option value="paypal">PayPal</Option>
              <Option value="authorize_net">Authorize.Net</Option>
              <Option value="manual">Manual</Option>
              <Option value="other">Other</Option>
            </Select>
          </Form.Item>
          <Form.Item name="config" label="Configuration (JSON)">
            <TextArea rows={6} placeholder='e.g., { "api_key": "...", "secret_key": "..." }' />
          </Form.Item>
          <Form.Item name="is_active" label="Active" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} style={{ width: '100%' }}>
              {editingGateway ? 'Save Changes' : 'Create Gateway'}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default PaymentGatewaysPage;