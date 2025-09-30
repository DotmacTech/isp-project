import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Spin, Typography, Button, Modal, Form, Input, Popconfirm, Row, Col } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;

function LocationsPage() {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);

    try {
      const response = await apiClient.get('/v1/locations/');
      setLocations(response.data);
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to view locations.');
      } else {
        message.error('Failed to fetch locations.');
      }
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdd = () => {
    setEditingLocation(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (location) => {
    setEditingLocation(location);
    form.setFieldsValue(location);
    setIsModalVisible(true);
  };

  const handleDelete = async (locationId) => {
    const token = localStorage.getItem('access_token');
    try {
      await apiClient.delete(`/v1/locations/${locationId}`);
      message.success('Location deleted successfully');
      setLocations(currentLocations => currentLocations.filter(location => location.id !== locationId));
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error('You do not have permission to delete locations.');
      } else {
        message.error('Failed to delete location.');
      }
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingLocation(null);
  };

  const handleFormFinish = async (values) => {
    const url = editingLocation ? `/v1/locations/${editingLocation.id}` : '/v1/locations/';
    const method = editingLocation ? 'put' : 'post';

    try {
      await apiClient[method](url, values);
      message.success(`Location ${editingLocation ? 'updated' : 'added'} successfully`);
      setIsModalVisible(false);
      fetchData();
    } catch (error) {
      if (error.response && error.response.status === 403) {
        message.error(`You do not have permission to ${editingLocation ? 'edit' : 'create'} locations.`);
      } else {
        const errorDetail = error.response?.data?.detail;
        const errorMessage = Array.isArray(errorDetail) 
          ? errorDetail.map(e => `${e.loc[1]}: ${e.msg}`).join('; ')
          : errorDetail || `Failed to ${editingLocation ? 'update' : 'add'} location`;
        message.error(errorMessage);
      }
      console.error('Form submission error:', error);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'City', dataIndex: 'city', key: 'city' },
    { title: 'Country', dataIndex: 'country', key: 'country' },
    { title: 'Timezone', dataIndex: 'timezone', key: 'timezone' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <span>
          <Button size="small" onClick={() => handleEdit(record)} style={{ marginRight: 8 }}>Edit</Button>
          <Popconfirm title="Are you sure you want to delete this location?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Location Management</Title>
      <Row justify="end" style={{ marginBottom: 16 }}>
        <Col>
          <Button type="primary" onClick={handleAdd}>
            Add Location
          </Button>
        </Col>
      </Row>
      <Table
        dataSource={locations}
        columns={columns}
        rowKey="id"
        loading={loading}
      />
      <Modal
        title={editingLocation ? 'Edit Location' : 'Add Location'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={handleFormFinish} initialValues={{ country: 'Nigeria', timezone: 'Africa/Lagos' }}>
          <Form.Item name="name" label="Location Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="address_line_1" label="Address Line 1"><Input /></Form.Item>
          <Form.Item name="address_line_2" label="Address Line 2"><Input /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="city" label="City"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="state_province" label="State/Province"><Input /></Form.Item></Col>
          </Row>
           <Row gutter={16}>
            <Col span={12}><Form.Item name="postal_code" label="Postal Code"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="country" label="Country"><Input /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="latitude" label="Latitude"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="longitude" label="Longitude"><Input /></Form.Item></Col>
          </Row>
          <Form.Item name="timezone" label="Timezone"><Input /></Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Location</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default LocationsPage;