import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Table, message, Button, Modal, Form, Input, Typography, Space, Popconfirm, Select, Tag, InputNumber
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, DatabaseOutlined, ToolOutlined, SearchOutlined } from '@ant-design/icons';
import { Address4, Address6 } from 'ip-address';
import apiClient from '../../api';

const { Title } = Typography;
const { Option } = Select;

const IpManagementComponent = ({ ipVersion, networkId, customers }) => {
  const [ips, setIps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingIp, setEditingIp] = useState(null);
  const [form] = Form.useForm();
  const [isGenerateModalVisible, setIsGenerateModalVisible] = useState(false);
  const [findIpLoading, setFindIpLoading] = useState(false);
  const [generateForm] = Form.useForm();

  const ipListUrl = `/v1/network/ipam/${ipVersion}/${networkId}/ips`;
  const ipDetailBaseUrl = `/v1/network/ipam/${ipVersion}/ips/`;

  const fetchIps = useCallback(async () => {
    setLoading(true);
    try {
      const ipsRes = await apiClient.get(ipListUrl);
      setIps(ipsRes.data || []);
    } catch (error) {
      message.error(`Failed to fetch ${ipVersion.toUpperCase()} addresses.`);
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, [ipListUrl, ipVersion]);

  useEffect(() => {
    if (networkId) {
      fetchIps();
    }
  }, [fetchIps, networkId]);

  const handleAdd = () => {
    setEditingIp(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (ip) => {
    setEditingIp(ip);
    form.setFieldsValue({
      ...ip,
      customer_id: ip.customer?.id,
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (ipId) => {
    try {
      await apiClient.delete(`${ipDetailBaseUrl}${ipId}`);
      message.success(`${ipVersion.toUpperCase()} Address deleted successfully`);
      fetchIps();
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to delete ${ipVersion.toUpperCase()} Address.`);
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormFinish = async (values) => {
    const url = editingIp ? `${ipDetailBaseUrl}${editingIp.id}` : ipListUrl;
    const method = editingIp ? 'put' : 'post';

    try {
      await apiClient({ method, url, data: values });
      message.success(`${ipVersion.toUpperCase()} Address ${editingIp ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      fetchIps();
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to save ${ipVersion.toUpperCase()} Address.`);
    }
  };

  const handleFindNextIp = async () => {
    setFindIpLoading(true);
    try {
      const res = await apiClient.get(`/v1/network/ipam/${ipVersion}/${networkId}/next-available-ip`);
      if (res.data && res.data.ip) {
        form.setFieldsValue({ ip: res.data.ip });
        message.success(`Found next available IP: ${res.data.ip}`);
      } else {
        message.warning('Could not find an available IP.');
      }
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to find next available IP.');
    } finally {
      setFindIpLoading(false);
    }
  };

  const handleOpenGenerateModal = () => {
    generateForm.resetFields();
    setIsGenerateModalVisible(true);
  };

  const handleGenerateModalCancel = () => {
    setIsGenerateModalVisible(false);
  };

  const handleGenerateFormFinish = async (values) => {
    const { start_ip, end_ip } = values;
    const MAX_RANGE_SIZE = 256;

    try {
      let start, end;
      if (ipVersion === 'ipv4') {
        start = new Address4(start_ip);
        end = new Address4(end_ip);
      } else {
        start = new Address6(start_ip);
        end = new Address6(end_ip);
      }

      if (end.bigInteger() < start.bigInteger()) {
        message.error('End IP address must be greater than or equal to Start IP address.');
        return;
      }

      const rangeSize = end.bigInteger() - start.bigInteger() + 1n;

      if (rangeSize > BigInt(MAX_RANGE_SIZE)) {
        message.error(`The IP range is too large. Please select a range with no more than ${MAX_RANGE_SIZE} addresses.`);
        return;
      }

      const response = await apiClient.post(`/v1/network/ipam/${ipVersion}/${networkId}/ips/generate`, values);
      message.success(response.data.message || `Successfully generated IP addresses.`);
      setIsGenerateModalVisible(false);
      fetchIps(); // Refresh the list
    } catch (error) {
      // Handle invalid IP format from the library or API errors
      if (error.message && error.message.includes('Invalid IP address')) {
        message.error('Invalid IP address format. Please check your input.');
      } else {
        message.error(error.response?.data?.detail || `Failed to generate ${ipVersion.toUpperCase()} addresses.`);
      }
    }
  };

  const columns = [
    { title: 'IP Address', dataIndex: 'ip', key: 'ip', render: (text, record) => (ipVersion === 'ipv6' ? `${record.ip}/${record.prefix}` : record.ip) },
    ...(ipVersion === 'ipv4' ? [{ title: 'Hostname', dataIndex: 'hostname', key: 'hostname' }] : []),
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Used', dataIndex: 'is_used', key: 'is_used', render: used => <Tag color={used ? 'red' : 'green'}>{used ? 'Yes' : 'No'}</Tag> },
    { title: 'Customer', dataIndex: ['customer', 'name'], key: 'customer', render: (name, record) => name && record.customer ? <Link to={`/dashboard/customers/view/${record.customer.id}`}>{name}</Link> : 'N/A' },
    { title: 'Comment', dataIndex: 'comment', key: 'comment' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)}><Button icon={<DeleteOutlined />} danger>Delete</Button></Popconfirm>
        </Space>
      ),
    },
  ];

  const modalTitle = `${editingIp ? 'Edit' : 'Add'} ${ipVersion.toUpperCase()} Address`;
  const ipPlaceholder = ipVersion === 'ipv4' ? 'e.g., 192.168.1.10' : 'e.g., 2001:db8::10';

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, marginTop: 24 }}>
        <Title level={3} style={{ margin: 0 }}><DatabaseOutlined /> IP Addresses</Title>
        <Space>
          <Button icon={<ToolOutlined />} onClick={handleOpenGenerateModal}>Generate IPs</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>Add {ipVersion.toUpperCase()} Address</Button>
        </Space>
      </div>
      <Table dataSource={ips} columns={columns} rowKey="id" loading={loading} />

      <Modal title={modalTitle} open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item label="IP Address" required>
            <Input.Group compact>
              <Form.Item
                name="ip"
                noStyle
                rules={[{ required: true, message: 'Please input an IP Address!' }]}
              >
                <Input style={{ width: 'calc(100% - 120px)' }} placeholder={ipPlaceholder} />
              </Form.Item>
              <Button
                style={{ width: '120px' }}
                icon={<SearchOutlined />}
                onClick={handleFindNextIp}
                loading={findIpLoading}
              >
                Find Next
              </Button>
            </Input.Group>
          </Form.Item>
          {ipVersion === 'ipv6' && <Form.Item name="prefix" label="Prefix" rules={[{ required: true }]}><InputNumber min={0} max={128} style={{ width: '100%' }} placeholder="e.g., 64" /></Form.Item>}
          {ipVersion === 'ipv4' && <Form.Item name="hostname" label="Hostname"><Input placeholder="e.g., server1.example.com" /></Form.Item>}
          <Form.Item name="title" label="Title"><Input placeholder="e.g., Primary DNS Server" /></Form.Item>
          <Form.Item name="comment" label="Comment"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="customer_id" label="Assigned Customer">
            <Select placeholder="Select a customer" showSearch allowClear filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>{customers.map(c => <Option key={c.id} value={c.id}>{c.name} ({c.login})</Option>)}</Select>
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editingIp ? 'Save Changes' : 'Create IP'}</Button></Form.Item>
        </Form>
      </Modal>

      <Modal title={`Generate ${ipVersion.toUpperCase()} Addresses`} open={isGenerateModalVisible} onCancel={handleGenerateModalCancel} footer={null} destroyOnHidden>
        <Form form={generateForm} layout="vertical" onFinish={handleGenerateFormFinish}>
          <Form.Item name="start_ip" label="Start IP Address" rules={[{ required: true }]}>
            <Input placeholder={ipVersion === 'ipv4' ? 'e.g., 192.168.1.100' : 'e.g., 2001:db8::100'} />
          </Form.Item>
          <Form.Item name="end_ip" label="End IP Address" rules={[{ required: true }]}>
            <Input placeholder={ipVersion === 'ipv4' ? 'e.g., 192.168.1.200' : 'e.g., 2001:db8::200'} />
          </Form.Item>
          {ipVersion === 'ipv6' && (
            <Form.Item name="prefix" label="Prefix for generated IPs" rules={[{ required: true, message: 'Please input a prefix!' }]}><InputNumber min={0} max={128} style={{ width: '100%' }} placeholder="e.g., 128" /></Form.Item>
          )}
          <Form.Item name="title" label="Title (Optional)"><Input placeholder="e.g., DHCP Pool Range" /></Form.Item>
          <Form.Item name="comment" label="Comment (Optional)"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>Generate</Button></Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default IpManagementComponent;