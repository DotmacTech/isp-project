import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Typography, 
  Button, 
  message, 
  Tabs, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  InputNumber, 
  Select 
} from 'antd';
import { 
  ShoppingOutlined, 
  WifiOutlined, 
  PhoneOutlined, 
  GiftOutlined, 
  CheckCircleOutlined 
} from '@ant-design/icons';
import apiClient from '../../../services/api';
import { jwtDecode } from 'jwt-decode';

const { Title } = Typography;
const { Option } = Select;

const TariffsPage = () => {
  const [tariffs, setTariffs] = useState({
    internet: [],
    voice: [],
    recurring: [],
    bundle: []
  });
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedTariff, setSelectedTariff] = useState(null);
  const [subscriptionForm] = Form.useForm();

  useEffect(() => {
    fetchTariffs();
  }, []);

  const fetchTariffs = async () => {
    setLoading(true);
    try {
      // Fetch tariffs that are visible on customer portal
      const [internetRes, voiceRes, recurringRes, bundleRes] = await Promise.all([
        apiClient.get('/v1/customer/tariffs/internet'),
        apiClient.get('/v1/customer/tariffs/voice'),
        apiClient.get('/v1/customer/tariffs/recurring'),
        apiClient.get('/v1/customer/tariffs/bundle')
      ]);

      setTariffs({
        internet: internetRes.data.items || [],
        voice: voiceRes.data.items || [],
        recurring: recurringRes.data.items || [],
        bundle: bundleRes.data.items || []
      });
    } catch (error) {
      message.error('Failed to fetch tariffs');
      console.error('Error fetching tariffs:', error);
    } finally {
      setLoading(false);
    }
  };

  const showSubscriptionModal = (tariff, type) => {
    setSelectedTariff({ ...tariff, type });
    setIsModalVisible(true);
  };

  const handleSubscription = async (values) => {
    try {
      // Get customer ID from token
      const token = localStorage.getItem('customer_access_token');
      if (!token) {
        message.error('You must be logged in to subscribe to services');
        return;
      }
      
      const decodedToken = jwtDecode(token);
      const customerId = decodedToken.sub;
      
      let response;
      switch (selectedTariff.type) {
        case 'internet':
          response = await apiClient.post('/v1/customer/services/subscribe/internet', {
            customer_id: parseInt(customerId),
            tariff_id: selectedTariff.id,
            description: values.description,
            quantity: values.quantity
          });
          break;
        case 'voice':
          response = await apiClient.post('/v1/customer/services/subscribe/voice', {
            customer_id: parseInt(customerId),
            tariff_id: selectedTariff.id,
            description: values.description,
            quantity: values.quantity
          });
          break;
        case 'recurring':
          response = await apiClient.post('/v1/customer/services/subscribe/recurring', {
            customer_id: parseInt(customerId),
            tariff_id: selectedTariff.id,
            description: values.description,
            quantity: values.quantity
          });
          break;
        case 'bundle':
          response = await apiClient.post('/v1/customer/services/subscribe/bundle', {
            customer_id: parseInt(customerId),
            bundle_id: selectedTariff.id,
            description: values.description,
            quantity: values.quantity
          });
          break;
        default:
          throw new Error('Invalid tariff type');
      }
      
      message.success(`Successfully subscribed to ${selectedTariff.title}!`);
      setIsModalVisible(false);
      subscriptionForm.resetFields();
    } catch (error) {
      message.error('Failed to create subscription: ' + (error.response?.data?.detail || error.message));
      console.error('Error creating subscription:', error);
    }
  };

  const internetColumns = [
    {
      title: 'Plan Name',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Download Speed',
      dataIndex: 'speed_download',
      key: 'speed_download',
      render: (speed) => `${speed} kbps`
    },
    {
      title: 'Upload Speed',
      dataIndex: 'speed_upload',
      key: 'speed_upload',
      render: (speed) => `${speed} kbps`
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price) => `$${price}`
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="primary" 
          icon={<CheckCircleOutlined />}
          onClick={() => showSubscriptionModal(record, 'internet')}
        >
          Subscribe
        </Button>
      ),
    },
  ];

  const voiceColumns = [
    {
      title: 'Plan Name',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price) => `$${price}`
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="primary" 
          icon={<CheckCircleOutlined />}
          onClick={() => showSubscriptionModal(record, 'voice')}
        >
          Subscribe
        </Button>
      ),
    },
  ];

  const recurringColumns = [
    {
      title: 'Plan Name',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Service Name',
      dataIndex: 'service_name',
      key: 'service_name',
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price) => `$${price}`
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="primary" 
          icon={<CheckCircleOutlined />}
          onClick={() => showSubscriptionModal(record, 'recurring')}
        >
          Subscribe
        </Button>
      ),
    },
  ];

  const bundleColumns = [
    {
      title: 'Plan Name',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Description',
      dataIndex: 'service_description',
      key: 'service_description',
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price) => `$${price}`
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="primary" 
          icon={<CheckCircleOutlined />}
          onClick={() => showSubscriptionModal(record, 'bundle')}
        >
          Subscribe
        </Button>
      ),
    },
  ];

  const items = [
    {
      key: '1',
      label: (
        <span>
          <WifiOutlined />
          Internet Tariffs
        </span>
      ),
      children: (
        <Table 
          dataSource={tariffs.internet} 
          columns={internetColumns} 
          loading={loading}
          rowKey="id"
        />
      ),
    },
    {
      key: '2',
      label: (
        <span>
          <PhoneOutlined />
          Voice Tariffs
        </span>
      ),
      children: (
        <Table 
          dataSource={tariffs.voice} 
          columns={voiceColumns} 
          loading={loading}
          rowKey="id"
        />
      ),
    },
    {
      key: '3',
      label: (
        <span>
          <GiftOutlined />
          Recurring Tariffs
        </span>
      ),
      children: (
        <Table 
          dataSource={tariffs.recurring} 
          columns={recurringColumns} 
          loading={loading}
          rowKey="id"
        />
      ),
    },
    {
      key: '4',
      label: (
        <span>
          <ShoppingOutlined />
          Bundle Tariffs
        </span>
      ),
      children: (
        <Table 
          dataSource={tariffs.bundle} 
          columns={bundleColumns} 
          loading={loading}
          rowKey="id"
        />
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Available Tariffs</Title>
      <p>Browse our available service plans and subscribe to the ones that meet your needs.</p>
      
      <Card>
        <Tabs defaultActiveKey="1" items={items} />
      </Card>

      <Modal
        title={`Subscribe to ${selectedTariff?.title}`}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          subscriptionForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={subscriptionForm}
          layout="vertical"
          onFinish={handleSubscription}
        >
          <Form.Item
            name="description"
            label="Service Description"
            rules={[{ required: true, message: 'Please enter a service description' }]}
          >
            <Input placeholder="e.g., Home Internet Service" />
          </Form.Item>
          
          <Form.Item
            name="quantity"
            label="Quantity"
            initialValue={1}
          >
            <InputNumber min={1} />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
              Confirm Subscription
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TariffsPage;