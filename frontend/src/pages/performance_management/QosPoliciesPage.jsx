import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Typography, Button, Modal, Form, Input, Popconfirm, Row, Col, Select, InputNumber, Switch } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Option } = Select;

function QosPoliciesPage() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  const fetchData = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const response = await apiClient.get('/v1/network/qos-policies/', {
        params: {
          skip: (params.current - 1) * params.pageSize,
          limit: params.pageSize,
          active_only: false, // Show all policies
        },
      });
      setPolicies(response.data.items);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        current: params.current,
        pageSize: params.pageSize,
      }));
    } catch (error) {
      message.error('Failed to fetch QoS policies.');
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData({ ...pagination, current: 1 });
  }, [fetchData]);

  const handleTableChange = (newPagination) => {
    fetchData({ ...newPagination });
  };

  const handleAdd = () => {
    setEditingPolicy(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true, policy_type: 'rate_limit', priority: 0 });
    setIsModalVisible(true);
  };

  const handleEdit = (policy) => {
    setEditingPolicy(policy);
    form.setFieldsValue(policy);
    setIsModalVisible(true);
  };

  const handleDelete = async (policyId) => {
    try {
      await apiClient.delete(`/v1/network/qos-policies/${policyId}`);
      message.success('QoS Policy deleted successfully');
      fetchData({ ...pagination }); // Refresh data
    } catch (error) {
      const errorDetail = error.response?.data?.detail || 'Failed to delete QoS policy.';
      message.error(errorDetail);
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingPolicy(null);
  };

  const handleFormFinish = async (values) => {
    const url = editingPolicy ? `/v1/network/qos-policies/${editingPolicy.id}` : '/v1/network/qos-policies/';
    const method = editingPolicy ? 'put' : 'post';

    try {
      await apiClient[method](url, values);
      message.success(`QoS Policy ${editingPolicy ? 'updated' : 'added'} successfully`);
      setIsModalVisible(false);
      fetchData({ ...pagination });
    } catch (error) {
      const errorDetail = error.response?.data?.detail || `Failed to ${editingPolicy ? 'update' : 'add'} QoS Policy`;
      message.error(errorDetail);
      console.error('Form submission error:', error);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80, sorter: (a, b) => a.id - b.id },
    { title: 'Name', dataIndex: 'name', key: 'name', sorter: (a, b) => a.name.localeCompare(b.name) },
    { title: 'Policy Type', dataIndex: 'policy_type', key: 'policy_type' },
    { title: 'Download Rate (kbps)', dataIndex: 'download_rate_kbps', key: 'download_rate_kbps' },
    { title: 'Upload Rate (kbps)', dataIndex: 'upload_rate_kbps', key: 'upload_rate_kbps' },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', sorter: (a, b) => a.priority - b.priority },
    { title: 'Active', dataIndex: 'is_active', key: 'is_active', render: (active) => (active ? 'Yes' : 'No') },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <span>
          <Button size="small" onClick={() => handleEdit(record)} style={{ marginRight: 8 }}>Edit</Button>
          <Popconfirm title="Are you sure you want to delete this policy?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>QoS Policy Management</Title>
      <Row justify="end" style={{ marginBottom: 16 }}>
        <Col>
          <Button type="primary" onClick={handleAdd}>
            Add QoS Policy
          </Button>
        </Col>
      </Row>
      <Table
        dataSource={policies}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
      />
      <Modal
        title={editingPolicy ? 'Edit QoS Policy' : 'Add QoS Policy'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnHidden
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="name" label="Policy Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="policy_type" label="Policy Type" rules={[{ required: true }]}>
                <Select>
                  <Option value="rate_limit">Rate Limit</Option>
                  <Option value="priority">Priority</Option>
                  <Option value="shaping">Traffic Shaping</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="priority" label="Priority" rules={[{ required: true }]}>
                <InputNumber min={0} max={8} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="download_rate_kbps" label="Download Rate (kbps)">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="upload_rate_kbps" label="Upload Rate (kbps)">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="is_active" label="Active" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Policy</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default QosPoliciesPage;