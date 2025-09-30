import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  message,
  Button,
  Modal,
  Form,
  Input,
  Typography,
  Space,
  Popconfirm,
  Card,
  Select,
  InputNumber
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, WifiOutlined } from '@ant-design/icons';
import { getRouters, createRouter, updateRouter, deleteRouter, getLocations, getPartners } from '../../services/routerApi';

const { Title } = Typography;
const { Option } = Select;

const NasDevices = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [locations, setLocations] = useState([]);
  const [partners, setPartners] = useState([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [form] = Form.useForm();

  const fetchData = useCallback(async (current, pageSize) => {
    setLoading(true);
    try {
      const response = await getRouters({
        skip: (current - 1) * pageSize,
        limit: pageSize,
      });
      const { items, total } = response.data;
      // We only want to show routers that have a radius_secret, as they are the NAS devices
      const nasDevices = Array.isArray(items) ? items.filter(item => item.radius_secret) : [];
      setDevices(nasDevices.map(d => ({...d, key: d.id, locationName: d.location?.name})));
      setPagination(prev => ({ ...prev, total: total, current: current }));
    } catch (error) {
      message.error('Failed to fetch RADIUS-enabled routers.');
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLookups = useCallback(async () => {
    try {
      const locRes = await getLocations({ limit: 1000 });
      setLocations(locRes.data || []);
      const partRes = await getPartners({ limit: 1000 });
      setPartners(partRes.data.items || []);
    } catch (error) {
      message.error('Failed to fetch required data (locations/partners).');
    }
  }, []);

  useEffect(() => {
    fetchData(pagination.current, pagination.pageSize);
  }, [fetchData, pagination.current, pagination.pageSize]);

  useEffect(() => {
    fetchLookups();
  }, [fetchLookups]);

  const handleAdd = () => {
    setEditingDevice(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (device) => {
    setEditingDevice(device);
    form.setFieldsValue({
      ...device,
      radius_secret: '', // Do not pre-fill secret
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await deleteRouter(id);
      message.success('Router (NAS) deleted successfully');
      fetchData(pagination.current, pagination.pageSize);
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete router.');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({ ...prev, ...newPagination }));
  };

  const handleFormFinish = async (values) => {
    const payload = { ...values };
    
    // Ensure partners_ids is an array, even if empty
    if (!payload.partners_ids) {
        payload.partners_ids = [];
    }

    if (editingDevice && !payload.radius_secret) {
      delete payload.radius_secret;
    }

    const apiCall = editingDevice
      ? updateRouter(editingDevice.id, payload)
      : createRouter(payload);

    try {
      await apiCall;
      message.success(`Router (NAS) ${editingDevice ? 'updated' : 'created'} successfully.`);
      setIsModalVisible(false);
      fetchData(1, pagination.pageSize); // Go back to first page on create/update
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save router.');
    }
  };

  const columns = [
    { title: 'IP Address', dataIndex: 'ip', key: 'ip', sorter: (a, b) => a.ip.localeCompare(b.ip) },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Model', dataIndex: 'model', key: 'model' },
    { title: 'NAS Type', dataIndex: 'nas_type', key: 'nas_type' },
    { title: 'Location', dataIndex: 'locationName', key: 'locationName' },
    { title: 'Actions', key: 'actions', render: (_, record) => ( <Space> <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>Edit</Button> <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(record.id)}> <Button icon={<DeleteOutlined />} danger>Delete</Button> </Popconfirm> </Space> ), fixed: 'right' },
  ];

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}><WifiOutlined /> RADIUS Enabled Routers (NAS)</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}> Add Router (NAS) </Button>
      </div>
      <Table dataSource={devices} columns={columns} rowKey="id" pagination={pagination} loading={loading} onChange={handleTableChange} scroll={{ x: true }} />
      <Modal title={editingDevice ? 'Edit Router (NAS)' : 'Add Router (NAS)'} open={isModalVisible} onCancel={handleModalCancel} footer={null} destroyOnHidden width={600}>
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name="ip" label="IP Address" rules={[{ required: true, message: 'IP address is required' }]}><Input placeholder="e.g., 192.168.1.1" /></Form.Item>
          <Form.Item name="title" label="Title" rules={[{ required: true, message: 'A unique title is required' }]}><Input placeholder="e.g., Main Office Gateway" /></Form.Item>
          <Form.Item name="radius_secret" label="RADIUS Secret" rules={[{ required: !editingDevice, message: 'Secret is required for a new NAS' }]}><Input.Password placeholder={editingDevice ? 'Enter new secret to change' : 'Enter RADIUS secret'} /></Form.Item>
          <Form.Item name="nas_type" label="NAS Type (Vendor)" rules={[{ required: true, message: 'NAS Type is required' }]}><InputNumber style={{ width: '100%' }} placeholder="e.g., 1 for MikroTik, 2 for Cisco" /></Form.Item>
          <Form.Item name="model" label="Model"><Input placeholder="e.g., CCR1009-7G-1C-1S+" /></Form.Item>
          <Form.Item name="location_id" label="Location" rules={[{ required: true, message: 'Location is required' }]}>
            <Select placeholder="Select a location" loading={!locations.length}>
              {locations.map(loc => <Option key={loc.id} value={loc.id}>{loc.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="partners_ids" label="Partners">
            <Select mode="multiple" placeholder="Select one or more partners" loading={!partners.length}>
              {partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editingDevice ? 'Save Changes' : 'Create Router (NAS)'}</Button></Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default NasDevices;