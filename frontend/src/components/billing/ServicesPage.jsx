import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Typography, Tag, Button, Modal, Form, Input, Select, DatePicker, Row, Col, Space, Popconfirm, InputNumber, Tabs } from 'antd';
import apiClient from '../../api';
import moment from 'moment';

const { Title } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

// --- Form Components ---

const InternetServiceForm = ({ customers, tariffs }) => (
  <>
    <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
      <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
        {customers.map(c => <Option key={c.id} value={c.id}>{c.name} (ID: {c.id})</Option>)}
      </Select>
    </Form.Item>
    <Form.Item name="tariff_id" label="Tariff" rules={[{ required: true }]}>
      <Select>
        {(tariffs || []).map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}
      </Select>
    </Form.Item>
    <Form.Item name="description" label="Description" rules={[{ required: true }]}><Input.TextArea /></Form.Item>
    <Form.Item name="login" label="Login" rules={[{ required: true }]}><Input /></Form.Item>
    <Form.Item name="password" label="Password"><Input.Password /></Form.Item>
    <Form.Item name="ipv4" label="Static IP"><Input /></Form.Item>
    <Row gutter={16}>
      <Col span={12}><Form.Item name="start_date" label="Start Date" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
      <Col span={12}><Form.Item name="end_date" label="End Date"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
    </Row>
    <Form.Item name="status" label="Status" rules={[{ required: true }]}>
      <Select><Option value="active">Active</Option><Option value="stopped">Stopped</Option><Option value="pending">Pending</Option><Option value="terminated">Terminated</Option></Select>
    </Form.Item>
  </>
);

const VoiceServiceForm = ({ customers, tariffs }) => (
    <>
      <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
        <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
          {customers.map(c => <Option key={c.id} value={c.id}>{c.name} (ID: {c.id})</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="tariff_id" label="Voice Tariff" rules={[{ required: true }]}>
        <Select>
          {(tariffs || []).map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="description" label="Description" rules={[{ required: true }]}><Input.TextArea /></Form.Item>
      <Form.Item name="phone" label="Phone Number" rules={[{ required: true }]}><Input /></Form.Item>
      <Form.Item name="password" label="VoIP Password"><Input.Password /></Form.Item>
      <Row gutter={16}>
        <Col span={12}><Form.Item name="start_date" label="Start Date" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={12}><Form.Item name="end_date" label="End Date"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
      </Row>
      <Form.Item name="status" label="Status" rules={[{ required: true }]}>
        <Select><Option value="active">Active</Option><Option value="stopped">Stopped</Option><Option value="pending">Pending</Option><Option value="terminated">Terminated</Option></Select>
      </Form.Item>
    </>
  );
  
const RecurringServiceForm = ({ customers, tariffs }) => (
    <>
      <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
        <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
          {customers.map(c => <Option key={c.id} value={c.id}>{c.name} (ID: {c.id})</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="tariff_id" label="Recurring Tariff" rules={[{ required: true }]}>
        <Select>
          {(tariffs || []).map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="description" label="Description" rules={[{ required: true }]}><Input.TextArea /></Form.Item>
      <Form.Item name="unit_price" label="Price Override (Optional)"><InputNumber style={{ width: '100%' }} min={0} step="0.01" /></Form.Item>
      <Row gutter={16}>
        <Col span={12}><Form.Item name="start_date" label="Start Date" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={12}><Form.Item name="end_date" label="End Date"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
      </Row>
      <Form.Item name="status" label="Status" rules={[{ required: true }]}>
        <Select><Option value="active">Active</Option><Option value="stopped">Stopped</Option><Option value="pending">Pending</Option><Option value="terminated">Terminated</Option></Select>
      </Form.Item>
    </>
);

const BundleServiceForm = ({ customers, tariffs }) => (
    <>
      <Form.Item name="customer_id" label="Customer" rules={[{ required: true }]}>
        <Select showSearch filterOption={(input, option) => option.children.toLowerCase().includes(input.toLowerCase())}>
          {customers.map(c => <Option key={c.id} value={c.id}>{c.name} (ID: {c.id})</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="tariff_id" label="Bundle Tariff" rules={[{ required: true }]}>
        <Select>
          {(tariffs || []).map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="description" label="Description" rules={[{ required: true }]}><Input.TextArea /></Form.Item>
      <Row gutter={16}>
        <Col span={12}><Form.Item name="start_date" label="Start Date" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={12}><Form.Item name="end_date" label="End Date"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
      </Row>
      <Form.Item name="status" label="Status" rules={[{ required: true }]}>
        <Select><Option value="active">Active</Option><Option value="stopped">Stopped</Option><Option value="pending">Pending</Option><Option value="terminated">Terminated</Option></Select>
      </Form.Item>
    </>
);

const SERVICE_TYPES = {
    internet: { key: 'internet', title: 'Internet Services', endpoint: '/api/v1/internet-services/', form: InternetServiceForm, tariffEndpoint: '/api/v1/internet-tariffs/' },
    voice: { key: 'voice', title: 'Voice Services', endpoint: '/api/v1/voice-services/', form: VoiceServiceForm, tariffEndpoint: '/api/v1/voice-tariffs/' },
    recurring: { key: 'recurring', title: 'Recurring Services', endpoint: '/api/v1/recurring-services/', form: RecurringServiceForm, tariffEndpoint: '/api/v1/recurring-tariffs/' },
    bundle: { key: 'bundle', title: 'Bundle Services', endpoint: '/api/v1/bundle-services/', form: BundleServiceForm, tariffEndpoint: '/api/v1/bundle-tariffs/' },
};

const initialStates = Object.keys(SERVICE_TYPES).reduce((acc, key) => {
    acc.data[key] = [];
    acc.loading[key] = true;
    acc.pagination[key] = { current: 1, pageSize: 10, total: 0 };
    acc.tariffs[key] = [];
    return acc;
}, { data: {}, loading: {}, pagination: {}, tariffs: {} });

function ServicesPage() {
  const [data, setData] = useState(initialStates.data);
  const [loading, setLoading] = useState(initialStates.loading);
  const [pagination, setPagination] = useState(initialStates.pagination);
  const [tariffs, setTariffs] = useState(initialStates.tariffs);
  
  const [customers, setCustomers] = useState([]);
  const [modalState, setModalState] = useState({ visible: false, type: null, record: null });
  const [form] = Form.useForm();

  const fetchData = useCallback(async (params = {}) => {
    const type = params.type;
    const config = SERVICE_TYPES[type];
    if (!config) return;

    setLoading(prev => ({ ...prev, [type]: true }));

    try {
      const currentPagination = params.pagination || pagination[type];
      const response = await apiClient.get(config.endpoint, {
        params: {
          skip: (currentPagination.current - 1) * currentPagination.pageSize,
          limit: currentPagination.pageSize,
        },
      });
      setData(prev => ({ ...prev, [type]: response.data.items }));
      setPagination(prev => ({
        ...prev,
        [type]: {
          ...prev[type],
          total: response.data.total,
          current: currentPagination.current,
        }
      }));
    } catch (error) {
      message.error(`Failed to fetch ${config.title.toLowerCase()}.`);
    } finally {
      setLoading(prev => ({ ...prev, [type]: false }));
    }
  }, [pagination]);

  const fetchDropdownData = useCallback(async () => {
    try {
        const customerRes = await apiClient.get('/v1/customers/', { params: { limit: 1000 } });
        setCustomers(customerRes.data.items);

        const tariffPromises = Object.values(SERVICE_TYPES).map(config => 
            apiClient.get(config.tariffEndpoint, { params: { limit: 1000 } })
        );
        const tariffResults = await Promise.all(tariffPromises);
        
        const newTariffs = {};
        Object.keys(SERVICE_TYPES).forEach((type, index) => {
            newTariffs[type] = tariffResults[index].data.items;
        });
        setTariffs(newTariffs);

    } catch (error) {
        message.error('Failed to fetch data for dropdowns.');
    }
  }, []);

  useEffect(() => {
    Object.keys(SERVICE_TYPES).forEach(type => fetchData({ type, pagination: pagination[type] }));
    fetchDropdownData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTableChange = (type, newPagination) => {
    setPagination(prev => ({ ...prev, [type]: newPagination }));
    fetchData({ type, pagination: newPagination });
  };

  const handleAdd = (type) => {
    setModalState({ visible: true, type, record: null });
    form.resetFields();
    form.setFieldsValue({
      status: 'active',
      start_date: moment(),
    });
  };

  const handleEdit = (type, record) => {
    setModalState({ visible: true, type, record });
    const isBundle = type === 'bundle';
    form.setFieldsValue({
        ...record,
        customer_id: record.customer.id,
        tariff_id: isBundle ? record.bundle?.id : record.tariff?.id,
        start_date: record.start_date ? moment(record.start_date) : null,
        end_date: record.end_date ? moment(record.end_date) : null,
    });
  };

  const handleDelete = async (type, id) => {
    const config = SERVICE_TYPES[type];
    try {
      await apiClient.delete(`${config.endpoint}${id}`);
      message.success(`${config.title.slice(0, -1)} deleted successfully`);
      fetchData({ type, pagination: pagination[type] });
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to delete ${config.title.slice(0, -1).toLowerCase()}.`);
    }
  };

  const handleModalCancel = () => {
    setModalState({ visible: false, type: null, record: null });
  };

  const handleFormFinish = async (values) => {
    const { type, record } = modalState;
    const config = SERVICE_TYPES[type];
    const method = record ? 'put' : 'post';
    const url = record ? `${config.endpoint}${record.id}` : config.endpoint;

    // prepare payload with formatted dates
    const payload = {
      ...values,
      start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : null,
      end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : null,
    };

    if (type === 'bundle' && payload.tariff_id) {
      // The backend expects 'bundle_id' for bundle services, not tariff_id
      payload.bundle_id = payload.tariff_id;
      delete payload.tariff_id;
    }

    try {
      await apiClient({
        method,
        url,
        data: payload,
      });

      message.success(`Service ${record ? 'updated' : 'created'} successfully.`);

      form.resetFields();       // ✅ clear form fields
      handleModalCancel();      // ✅ close modal
      fetchData({ type, pagination: pagination[type] }); // ✅ reload list
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save service.');
    }
  };

  const getColumns = (type) => {
    const isBundle = type === 'bundle';
    const baseColumns = [
        { title: 'ID', dataIndex: 'id', key: 'id' },
        { title: 'Customer', dataIndex: ['customer', 'name'], key: 'customer' },
        { title: 'Tariff', dataIndex: isBundle ? ['bundle', 'title'] : ['tariff', 'title'], key: 'tariff' },
        { title: 'Status', dataIndex: 'status', key: 'status', render: (status) => <Tag color={status === 'active' ? 'green' : 'red'}>{status?.toUpperCase()}</Tag> },
        { title: 'Actions', key: 'actions', render: (_, record) => (
            <Space>
                <Button size="small" onClick={() => handleEdit(type, record)}>Edit</Button>
                <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(type, record.id)}>
                    <Button size="small" danger>Delete</Button>
                </Popconfirm>
            </Space>
        )},
    ];

    switch (type) {
        case 'internet':
            return [
                ...baseColumns.slice(0, 2),
                { title: 'Description', dataIndex: 'description', key: 'description' },
                ...baseColumns.slice(2, 3),
                { title: 'Login', dataIndex: 'login', key: 'login' },
                { title: 'IP Address', dataIndex: 'ipv4', key: 'ipv4' },
                ...baseColumns.slice(3),
            ];
        case 'voice':
            return [
                ...baseColumns.slice(0, 2),
                { title: 'Phone Number', dataIndex: 'phone', key: 'phone' },
                ...baseColumns.slice(2),
            ];
        case 'recurring':
            return [
                ...baseColumns.slice(0, 2),
                { title: 'Description', dataIndex: 'description', key: 'description' },
                { 
                  title: 'Price', 
                  key: 'price', 
                  render: (_, record) => record.unit_price ? `$${Number(record.unit_price).toFixed(2)}` : (record.tariff ? `$${Number(record.tariff.price).toFixed(2)}` : 'N/A')
                },
                ...baseColumns.slice(2),
            ];
        case 'bundle':
            return baseColumns;
        default:
            return baseColumns;
    }
  };

  const { type, record } = modalState;
  const currentConfig = SERVICE_TYPES[type];
  const FormComponent = currentConfig?.form;

  return (
    <div>
      <Title level={2}>Services</Title>
      <Tabs defaultActiveKey="internet">
          {Object.values(SERVICE_TYPES).map(config => (
              <TabPane tab={config.title} key={config.key}>
                  <Button type="primary" onClick={() => handleAdd(config.key)} style={{ marginBottom: 16 }}>
                      Add {config.title.slice(0, -1)}
                  </Button>
                  <Table
                      dataSource={data[config.key]}
                      columns={getColumns(config.key)}
                      rowKey="id"
                      loading={loading[config.key]}
                      pagination={pagination[config.key]}
                      onChange={(p) => handleTableChange(config.key, p)}
                  />
              </TabPane>
          ))}
      </Tabs>

      <Modal
        title={currentConfig ? `${record ? 'Edit' : 'Add'} ${currentConfig.title.slice(0, -1)}` : ''}
        open={modalState.visible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnClose
      >
        {FormComponent && (
            <Form form={form} layout="vertical" onFinish={handleFormFinish}>
                <FormComponent customers={customers} tariffs={tariffs[type]} />
                <Button type="primary" htmlType="submit" style={{ width: '100%' }}>Save Service</Button>
            </Form>
        )}
      </Modal>
    </div>
  );
}

export default ServicesPage;