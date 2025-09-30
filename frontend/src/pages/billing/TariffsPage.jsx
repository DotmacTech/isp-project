import React, { useState, useEffect, useCallback } from 'react';
import { Table, message, Button, Modal, Form, Input, Select, Typography, Row, Col, Space, Popconfirm, InputNumber, Checkbox, Tabs, Tag } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Option } = Select;

// --- Form Components ---
const InternetTariffForm = ({ editing, partners, taxes, transactionCategories, locations }) => (
  <>
    <Title level={4}>Basic Information</Title>
    <Row gutter={16}>
      <Col span={12}><Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item></Col>
      <Col span={12}><Form.Item name="price" label="Price" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={0} step="0.01" /></Form.Item></Col>
    </Row>
    <Form.Item name="partners_ids" label="Partners" rules={[{ required: true }]}>
      <Select mode="multiple" placeholder="Select partners">
        {partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}
      </Select>
    </Form.Item>
    <Row gutter={16}>
      <Col span={12}><Form.Item name="tax_id" label="Tax"><Select placeholder="Select a tax rate" allowClear>{taxes.map(tax => <Option key={tax.id} value={tax.id}>{tax.name} ({Number(tax.rate * 100).toFixed(2)}%)</Option>)}</Select></Form.Item></Col>
      <Col span={12}><Form.Item name="transaction_category_id" label="Transaction Category"><Select placeholder="Select a category" allowClear>{transactionCategories.map(cat => <Option key={cat.id} value={cat.id}>{cat.name}</Option>)}</Select></Form.Item></Col>
    </Row>
    <Form.Item name="available_for_locations" label="Available for Locations">
      <Select mode="multiple" placeholder="Select locations (optional, all if empty)">{locations.map(l => <Option key={l.id} value={l.id}>{l.name}</Option>)}</Select>
    </Form.Item>
    <Title level={4}>Speed Configuration (kbps)</Title>
    <Row gutter={16}>
      <Col span={12}><Form.Item name="speed_download" label="Download Speed" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={0} /></Form.Item></Col>
      <Col span={12}><Form.Item name="speed_upload" label="Upload Speed" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={0} /></Form.Item></Col>
    </Row>
    <Title level={4}>Burst Configuration</Title>
    <Row gutter={16}>
      <Col span={8}><Form.Item name="burst_limit" label="Burst Limit"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
      <Col span={8}><Form.Item name="burst_threshold" label="Burst Threshold"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
      <Col span={8}><Form.Item name="burst_time" label="Burst Time (s)"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
    </Row>
    <Title level={4}>Availability</Title>
    <Row gutter={16}>
      <Col span={8}><Form.Item name="show_on_customer_portal" label="Show on Portal" valuePropName="checked"><Checkbox /></Form.Item></Col>
      <Col span={8}><Form.Item name="hide_on_admin_portal" label="Hide on Admin" valuePropName="checked"><Checkbox /></Form.Item></Col>
    </Row>
    <Form.Item>
      <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
        {editing ? 'Save Changes' : 'Create Tariff'}
      </Button>
    </Form.Item>
  </>
);

const VoiceTariffForm = ({ editing, partners, taxes, transactionCategories }) => (
  <>
    <Row gutter={16}><Col span={12}><Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item></Col><Col span={12}><Form.Item name="price" label="Price" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={0} step="0.01" /></Form.Item></Col></Row>
    <Row gutter={16}><Col span={12}><Form.Item name="service_name" label="Service Name (Optional)"><Input /></Form.Item></Col><Col span={12}><Form.Item name="type" label="Type" rules={[{ required: true }]}><Input /></Form.Item></Col></Row>
    <Form.Item name="partners_ids" label="Partners" rules={[{ required: true }]}>
      <Select mode="multiple" placeholder="Select partners">{partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select>
    </Form.Item>
    <Row gutter={16}><Col span={12}><Form.Item name="tax_id" label="Tax"><Select placeholder="Select a tax rate" allowClear>{taxes.map(tax => <Option key={tax.id} value={tax.id}>{tax.name} ({Number(tax.rate * 100).toFixed(2)}%)</Option>)}</Select></Form.Item></Col><Col span={12}><Form.Item name="transaction_category_id" label="Transaction Category"><Select placeholder="Select a category" allowClear>{transactionCategories.map(cat => <Option key={cat.id} value={cat.id}>{cat.name}</Option>)}</Select></Form.Item></Col></Row>
    <Row gutter={16}><Col span={12}><Form.Item name="billing_days_count" label="Billing Days Count" initialValue={1}><InputNumber style={{ width: '100%' }} min={1} /></Form.Item></Col></Row>
    <Row gutter={16}><Col span={12}><Form.Item name="show_on_customer_portal" label="Show on Portal" valuePropName="checked"><Checkbox /></Form.Item></Col><Col span={12}><Form.Item name="hide_on_admin_portal" label="Hide on Admin" valuePropName="checked"><Checkbox /></Form.Item></Col></Row>
    <Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editing ? 'Save Changes' : 'Create Voice Tariff'}</Button>
  </>
);

const RecurringTariffForm = ({ editing, partners, taxes, transactionCategories }) => (
  <>
    <Row gutter={16}><Col span={12}><Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item></Col><Col span={12}><Form.Item name="price" label="Price" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={0} step="0.01" /></Form.Item></Col></Row>
    <Form.Item name="service_name" label="Service Name (Optional)"><Input /></Form.Item>
    <Form.Item name="billing_days_count" label="Billing Days Count" initialValue={1}><InputNumber style={{ width: '100%' }} min={1} /></Form.Item>
    <Form.Item name="partners_ids" label="Partners" rules={[{ required: true }]}>
      <Select mode="multiple" placeholder="Select partners">{partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select>
    </Form.Item>
    <Row gutter={16}><Col span={12}><Form.Item name="tax_id" label="Tax"><Select placeholder="Select a tax rate" allowClear>{taxes.map(tax => <Option key={tax.id} value={tax.id}>{tax.name} ({Number(tax.rate * 100).toFixed(2)}%)</Option>)}</Select></Form.Item></Col><Col span={12}><Form.Item name="transaction_category_id" label="Transaction Category"><Select placeholder="Select a category" allowClear>{transactionCategories.map(cat => <Option key={cat.id} value={cat.id}>{cat.name}</Option>)}</Select></Form.Item></Col></Row>
    <Row gutter={16}><Col span={12}><Form.Item name="show_on_customer_portal" label="Show on Portal" valuePropName="checked"><Checkbox /></Form.Item></Col><Col span={12}><Form.Item name="hide_on_admin_portal" label="Hide on Admin" valuePropName="checked"><Checkbox /></Form.Item></Col></Row>
    <Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editing ? 'Save Changes' : 'Create Recurring Tariff'}</Button>
  </>
);

const BundleTariffForm = ({ editing, partners, allInternetTariffs, allVoiceTariffs, allRecurringTariffs }) => (
  <>
    <Row gutter={16}><Col span={12}><Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item></Col><Col span={12}><Form.Item name="price" label="Price" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={0} step="0.01" /></Form.Item></Col></Row>
    <Form.Item name="service_description" label="Service Description"><Input.TextArea /></Form.Item>
    <Row gutter={16}><Col span={12}><Form.Item name="activation_fee" label="Activation Fee"><InputNumber style={{ width: '100%' }} min={0} step="0.01" /></Form.Item></Col><Col span={12}><Form.Item name="cancellation_fee" label="Cancellation Fee"><InputNumber style={{ width: '100%' }} min={0} step="0.01" /></Form.Item></Col></Row>
    <Form.Item name="contract_duration" label="Contract Duration (days)"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
    <Form.Item name="partners_ids" label="Partners" rules={[{ required: true }]}>
      <Select mode="multiple" placeholder="Select partners">{partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select>
    </Form.Item>
    <Row gutter={16}><Col span={8}><Form.Item name="internet_tariffs" label="Internet Tariffs"><Select mode="multiple" placeholder="Select internet tariffs">{allInternetTariffs.map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}</Select></Form.Item></Col><Col span={8}><Form.Item name="voice_tariffs" label="Voice Tariffs"><Select mode="multiple" placeholder="Select voice tariffs">{allVoiceTariffs.map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}</Select></Form.Item></Col><Col span={8}><Form.Item name="custom_tariffs" label="Recurring Tariffs"><Select mode="multiple" placeholder="Select recurring tariffs">{allRecurringTariffs.map(t => <Option key={t.id} value={t.id}>{t.title}</Option>)}</Select></Form.Item></Col></Row>
    <Form.Item name="automatic_renewal" label="Automatic Renewal" valuePropName="checked"><Checkbox /></Form.Item>
    <Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editing ? 'Save Changes' : 'Create Bundle Tariff'}</Button>
  </>
);

const OneTimeTariffForm = ({ editing, partners, taxes, transactionCategories }) => (
  <>
    <Row gutter={16}><Col span={12}><Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item></Col><Col span={12}><Form.Item name="price" label="Price" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} min={0} step="0.01" /></Form.Item></Col></Row>
    <Form.Item name="service_description" label="Description"><Input.TextArea /></Form.Item>
    <Form.Item name="partners_ids" label="Partners" rules={[{ required: true }]}>
      <Select mode="multiple" placeholder="Select partners">{partners.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}</Select>
    </Form.Item>
    <Row gutter={16}><Col span={12}><Form.Item name="tax_id" label="Tax"><Select placeholder="Select a tax rate" allowClear>{taxes.map(tax => <Option key={tax.id} value={tax.id}>{tax.name} ({Number(tax.rate * 100).toFixed(2)}%)</Option>)}</Select></Form.Item></Col><Col span={12}><Form.Item name="transaction_category_id" label="Transaction Category"><Select placeholder="Select a category" allowClear>{transactionCategories.map(cat => <Option key={cat.id} value={cat.id}>{cat.name}</Option>)}</Select></Form.Item></Col></Row>
    <Row gutter={16}><Col span={8}><Form.Item name="enabled" label="Enabled" valuePropName="checked"><Checkbox /></Form.Item></Col><Col span={8}><Form.Item name="show_on_customer_portal" label="Show on Portal" valuePropName="checked"><Checkbox /></Form.Item></Col><Col span={8}><Form.Item name="hide_on_admin_portal" label="Hide on Admin" valuePropName="checked"><Checkbox /></Form.Item></Col></Row>
    <Button type="primary" htmlType="submit" style={{ width: '100%' }}>{editing ? 'Save Changes' : 'Create One-Time Tariff'}</Button>
  </>
);

const TARIFF_TYPES = {
  internet: { key: 'internet', title: 'Internet Tariffs', endpoint: '/v1/internet-tariffs/', form: InternetTariffForm, initialValues: {} },
  voice: { key: 'voice', title: 'Voice Tariffs', endpoint: '/v1/voice-tariffs/', form: VoiceTariffForm, initialValues: { type: 'voip' } },
  recurring: { key: 'recurring', title: 'Recurring Tariffs', endpoint: '/v1/recurring-tariffs/', form: RecurringTariffForm, initialValues: {} },
  bundle: { key: 'bundle', title: 'Bundle Tariffs', endpoint: '/v1/bundle-tariffs/', form: BundleTariffForm, initialValues: {} },
  onetime: { key: 'onetime', title: 'One-Time Tariffs', endpoint: '/v1/one-time-tariffs/', form: OneTimeTariffForm, initialValues: { enabled: true } },
};

const initialStates = Object.keys(TARIFF_TYPES).reduce((acc, key) => {
  acc.data[key] = [];
  acc.loading[key] = true;
  acc.pagination[key] = { current: 1, pageSize: 10, total: 0 };
  return acc;
}, { data: {}, loading: {}, pagination: {} });


function TariffsPage() {  
  const [locations, setLocations] = useState([]);
  const [partners, setPartners] = useState([]);
  const [taxes, setTaxes] = useState([]);
  const [transactionCategories, setTransactionCategories] = useState([]);
  // For bundle tariff dropdowns
  const [allInternetTariffs, setAllInternetTariffs] = useState([]);
  const [allVoiceTariffs, setAllVoiceTariffs] = useState([]);
  const [allRecurringTariffs, setAllRecurringTariffs] = useState([]);
  
  const [data, setData] = useState(initialStates.data);
  const [loading, setLoading] = useState(initialStates.loading);
  const [pagination, setPagination] = useState(initialStates.pagination);
  
  const [modalState, setModalState] = useState({ visible: false, type: null, record: null });
  const [form] = Form.useForm();

  const fetchData = useCallback(async (type, params = {}) => {
    const config = TARIFF_TYPES[type];
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
      const [partnersRes, taxesRes, transactionCategoriesRes, internetTariffsRes, voiceTariffsRes, recurringTariffsRes, locationsRes] = await Promise.all([
        apiClient.get('/v1/partners/'),
        apiClient.get('/v1/billing/taxes/'),
        apiClient.get('/v1/billing/transaction-categories/'),
        apiClient.get('/v1/internet-tariffs/', { params: { limit: 1000 } }),
        apiClient.get('/v1/voice-tariffs/', { params: { limit: 1000 } }),
        apiClient.get('/v1/recurring-tariffs/', { params: { limit: 1000 } }),
        apiClient.get('/v1/locations/')
      ]);
      setPartners(partnersRes.data.items);
      setTaxes(taxesRes.data);
      setTransactionCategories(transactionCategoriesRes.data);
      setAllInternetTariffs(internetTariffsRes.data.items);
      setAllVoiceTariffs(voiceTariffsRes.data.items);
      setAllRecurringTariffs(recurringTariffsRes.data.items);
      setLocations(locationsRes.data);
    } catch (error) {
      message.error('Failed to fetch data for forms.');
    }
  }, []);

  useEffect(() => {
    Object.keys(TARIFF_TYPES).forEach(type => fetchData(type));
    fetchDropdownData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTableChange = (type, newPagination) => {
    setPagination(prev => ({ ...prev, [type]: newPagination }));
    fetchData(type, { pagination: newPagination });
  };

  const handleAdd = (type) => {
    setModalState({ visible: true, type, record: null });
    form.resetFields();
    form.setFieldsValue(TARIFF_TYPES[type].initialValues);
  };

  const handleEdit = (type, record) => {
    setModalState({ visible: true, type, record });
    form.setFieldsValue(record);
  };

  const handleDelete = async (type, id) => {
    const config = TARIFF_TYPES[type];
    try {
      await apiClient.delete(`${config.endpoint}${id}`);
      message.success(`${config.title.slice(0, -1)} deleted successfully`);
      fetchData(type);
    } catch (error) {
      message.error(error.response?.data?.detail || `Failed to delete ${config.title.slice(0, -1).toLowerCase()}.`);
    }
  };

  const handleModalCancel = () => {
    setModalState({ visible: false, type: null, record: null });
  };

  const handleFormFinish = async (values) => {
  const { type, record } = modalState;
  const config = TARIFF_TYPES[type];
  const method = record ? 'put' : 'post';
  const url = record ? `${config.endpoint}${record.id}` : config.endpoint;

  try {
    await apiClient({
      method,
      url,
      data: values,
    });

    message.success(
      `${config.title.slice(0, -1)} ${record ? 'updated' : 'created'} successfully.`
    );

    form.resetFields();      // ✅ reset form values
    handleModalCancel();     // close modal
    fetchData(type);         // reload the list
  } catch (error) {
    message.error(
      error.response?.data?.detail ||
        `Failed to save ${config.title.slice(0, -1).toLowerCase()}.`
    );
  }
};

  const getColumns = (type) => [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Price', dataIndex: 'price', key: 'price', render: (text) => `$${Number(text).toFixed(2)}` },
    { title: 'Download Speed', dataIndex: 'speed_download', key: 'speed_download', render: (text) => `${text} kbps` },
    { title: 'Upload Speed', dataIndex: 'speed_upload', key: 'speed_upload', render: (text) => `${text} kbps` },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(type, record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(type, record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const getVoiceColumns = (type) => [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Price', dataIndex: 'price', key: 'price', render: (text) => `$${Number(text).toFixed(2)}` },
    { title: 'Type', dataIndex: 'type', key: 'type' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(type, record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(type, record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const getRecurringColumns = (type) => [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Price', dataIndex: 'price', key: 'price', render: (text) => `$${Number(text).toFixed(2)}` },
    { title: 'Billing Days', dataIndex: 'billing_days_count', key: 'billing_days_count' },
    { title: 'Show on Portal', dataIndex: 'show_on_customer_portal', key: 'show_on_customer_portal', render: (show) => <Tag color={show ? 'green' : 'red'}>{show ? 'Yes' : 'No'}</Tag> },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(type, record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(type, record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const getBundleColumns = (type) => [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Price', dataIndex: 'price', key: 'price', render: (text) => `$${Number(text).toFixed(2)}` },
    { title: 'Activation Fee', dataIndex: 'activation_fee', key: 'activation_fee', render: (text) => `$${Number(text).toFixed(2)}` },
    { title: 'Contract (days)', dataIndex: 'contract_duration', key: 'contract_duration' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(type, record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(type, record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const getOneTimeColumns = (type) => [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Price', dataIndex: 'price', key: 'price', render: (text) => `$${Number(text).toFixed(2)}` },
    { title: 'Enabled', dataIndex: 'enabled', key: 'enabled', render: (enabled) => <Tag color={enabled ? 'green' : 'red'}>{enabled ? 'Yes' : 'No'}</Tag> },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(type, record)}>Edit</Button>
          <Popconfirm title="Are you sure?" onConfirm={() => handleDelete(type, record.id)}>
            <Button size="small" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];
  
  const TARIFF_CONFIG = {
    internet: { ...TARIFF_TYPES.internet, columns: getColumns('internet') },
    voice: { ...TARIFF_TYPES.voice, columns: getVoiceColumns('voice') },
    recurring: { ...TARIFF_TYPES.recurring, columns: getRecurringColumns('recurring') },
    bundle: { ...TARIFF_TYPES.bundle, columns: getBundleColumns('bundle') },
    onetime: { ...TARIFF_TYPES.onetime, columns: getOneTimeColumns('onetime') },
  };

  const { type, record } = modalState;
  const currentConfig = TARIFF_CONFIG[type];
  const FormComponent = currentConfig?.form;

  // Create tabs items for the new Tabs API
  const tabsItems = Object.values(TARIFF_CONFIG).map(config => ({
    key: config.key,
    label: config.title,
    children: (
      <>
        <Button type="primary" onClick={() => handleAdd(config.key)} style={{ marginBottom: 16 }}>
          Add {config.title.slice(0, -1)}
        </Button>
        <Table
          dataSource={data[config.key]}
          columns={config.columns}
          rowKey="id"
          loading={loading[config.key]}
          pagination={pagination[config.key]}
          onChange={(p) => handleTableChange(config.key, p)}
        />
      </>
    )
  }));

  return (
    <div>
      <Title level={2}>Tariff Management</Title>
      <Tabs defaultActiveKey="internet" items={tabsItems} />

      <Modal
        title={currentConfig ? (record ? `Edit ${currentConfig.title.slice(0, -1)}` : `Add ${currentConfig.title.slice(0, -1)}`) : ''}
        open={modalState.visible}
        onCancel={handleModalCancel}
        footer={null}
        destroyOnHidden
        width={type === 'internet' || type === 'bundle' ? 800 : 600}
      >
        {FormComponent && (
          <Form form={form} layout="vertical" onFinish={handleFormFinish}>
            <FormComponent
              editing={!!record}
              partners={partners}
              taxes={taxes}
              transactionCategories={transactionCategories}
              locations={locations}
              allInternetTariffs={allInternetTariffs}
              allVoiceTariffs={allVoiceTariffs}
              allRecurringTariffs={allRecurringTariffs}
            />
          </Form>
        )}
      </Modal>
    </div>
  );
}

export default TariffsPage;