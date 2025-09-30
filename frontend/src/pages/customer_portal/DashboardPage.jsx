import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, message } from 'antd';
import { UserOutlined, ShoppingOutlined } from '@ant-design/icons';
import apiClient from '../../../services/api';
import { jwtDecode } from 'jwt-decode';  // ✅ FIXED

const { Title } = Typography;

const CustomerDashboardPage = () => {
  const [customerData, setCustomerData] = useState(null);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCustomerData = async () => {
      try {
        // Get customer ID from token
        const token = localStorage.getItem('customer_access_token');
        if (!token) {
          message.error('You must be logged in to view this page');
          return;
        }
        
        const decodedToken = jwtDecode(token); // ✅ FIXED
        const customerId = decodedToken.sub;
        
        // Fetch customer data
        const customerRes = await apiClient.get(`/v1/customers/${customerId}`);
        setCustomerData(customerRes.data);
        
        // Fetch customer services
        const servicesRes = await apiClient.get('/v1/internet-services/', { 
          params: { customer_id: customerId } 
        });
        setServices(servicesRes.data.items);
      } catch (error) {
        message.error('Failed to fetch customer data');
        console.error('Error fetching customer data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCustomerData();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <Title level={2}>Customer Dashboard</Title>
      
      {customerData && (
        <Card title="Customer Information" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="Name" value={customerData.name} prefix={<UserOutlined />} />
            </Col>
            <Col span={8}>
              <Statistic title="Email" value={customerData.email || 'N/A'} />
            </Col>
            <Col span={8}>
              <Statistic title="Phone" value={customerData.phone || 'N/A'} />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={8}>
              <Statistic title="Status" value={customerData.status} />
            </Col>
            <Col span={8}>
              <Statistic title="Login" value={customerData.login} />
            </Col>
            <Col span={8}>
              <Statistic title="Services" value={services.length} prefix={<ShoppingOutlined />} />
            </Col>
          </Row>
        </Card>
      )}

      <Card title="My Services">
        {services.length > 0 ? (
          <Row gutter={16}>
            {services.map(service => (
              <Col span={8} key={service.id}>
                <Card 
                  title={service.tariff?.title || 'Service'} 
                  bordered={true} 
                  style={{ marginBottom: 16 }}
                >
                  <p><strong>Status:</strong> {service.status}</p>
                  <p><strong>Description:</strong> {service.description}</p>
                  <p><strong>Price:</strong> ${service.unit_price || 0}</p>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <p>You don't have any services yet. <a href="/customer/tariffs">Browse tariffs</a> to subscribe.</p>
        )}
      </Card>
    </div>
  );
};

export default CustomerDashboardPage;
