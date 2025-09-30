import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  message, Typography, Card, Descriptions, Breadcrumb, Spin
} from 'antd';
import apiClient from '../../services/api';
import IpManagementComponent from '../../components/network/IpManagementComponent';

const { Title } = Typography;

const IPv4NetworkDetailPage = () => {
  const { networkId } = useParams();
  const [network, setNetwork] = useState(null);
  const [ips, setIps] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [networkRes, customersRes] = await Promise.all([
        apiClient.get(`/v1/network/ipam/ipv4/${networkId}`),
        apiClient.get('/v1/customers/', { params: { limit: 1000 } })
      ]);
      setNetwork(networkRes.data);
      // IP data is now fetched by IpManagementComponent
      setCustomers(customersRes.data.items || []);
    } catch (error) {
      message.error('Failed to fetch network data.');
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, [networkId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return <Spin tip="Loading..." style={{ display: 'block', marginTop: '50px' }} />;
  }

  if (!network) {
    return <Title level={3}>Network not found.</Title>;
  }

  return (
    <Card>
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item><Link to="/dashboard/network/ipam/ipv4">IPv4 Networks</Link></Breadcrumb.Item>
        <Breadcrumb.Item>{network.network}/{network.mask}</Breadcrumb.Item>
      </Breadcrumb>
      
      <Descriptions title="Network Details" bordered column={2} size="small" style={{ marginBottom: 24 }}>
        <Descriptions.Item label="Network">{network.network}/{network.mask}</Descriptions.Item>
        <Descriptions.Item label="Title">{network.title}</Descriptions.Item>
        <Descriptions.Item label="Location">{network.location?.name}</Descriptions.Item>
        <Descriptions.Item label="Category">{network.category?.name}</Descriptions.Item>
        <Descriptions.Item label="Usage Type">{network.type_of_usage}</Descriptions.Item>
        <Descriptions.Item label="Network Type">{network.network_type}</Descriptions.Item>
        <Descriptions.Item label="Comment" span={2}>{network.comment}</Descriptions.Item>
      </Descriptions>

      <IpManagementComponent ipVersion="ipv4" networkId={networkId} customers={customers} />
    </Card>
  );
};

export default IPv4NetworkDetailPage;