import React, { useState, useEffect, useCallback } from 'react';
import { Form, Input, Button, message, Spin, Typography, Switch, Select, InputNumber, Card, Divider, Tabs, Table, Modal, Popconfirm, Space, Tag } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;
const { Option } = Select;

const SETTING_KEYS = {
  DEFAULT_TAX_ID: 'billing.default_tax_id',
  INVOICE_PREFIX: 'billing.invoice_prefix',
  DEFAULT_PAYMENT_TERMS: 'billing.default_payment_terms_days',
  AUTO_INVOICING_ENABLED: 'billing.auto_invoicing_enabled',
  AUTO_SUSPENSION_ENABLED: 'billing.auto_suspension_enabled',
};

function BillingSettingsPage() {
  // State for General Settings tab
  const [generalSettingsForm] = Form.useForm();
  const [generalSettingsLoading, setGeneralSettingsLoading] = useState(true);
  const [isSubmittingGeneral, setIsSubmittingGeneral] = useState(false);
  const [taxes, setTaxes] = useState([]);
  const [settingsMap, setSettingsMap] = useState({});

  // State for Payment Methods tab
  const [paymentMethodsForm] = Form.useForm();
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [paymentMethodsLoading, setPaymentMethodsLoading] = useState(true);
  const [isPaymentMethodModalVisible, setIsPaymentMethodModalVisible] = useState(false);
  const [editingPaymentMethod, setEditingPaymentMethod] = useState(null);

  // State for Taxes tab
  const [taxesForm] = Form.useForm();
  const [allTaxes, setAllTaxes] = useState([]); // For the tax management table
  const [taxesLoading, setTaxesLoading] = useState(true);
  const [isTaxModalVisible, setIsTaxModalVisible] = useState(false);
  const [editingTax, setEditingTax] = useState(null);

  const fetchGeneralData = useCallback(async () => {
    setGeneralSettingsLoading(true);

    try {
      const [settingsRes, taxesRes] = await Promise.all([
        apiClient.get('/v1/settings/'),
        apiClient.get('/v1/billing/taxes/') // This fetches active taxes for the dropdown
      ]);

      const settingsData = settingsRes.data;
      const settingKeysList = Object.values(SETTING_KEYS);
      const newSettingsMap = {};
      const formValues = {};

      settingsData.forEach(setting => {
        newSettingsMap[setting.config_key] = setting;
        if (settingKeysList.includes(setting.config_key)) {
          // Handle boolean values from JSON
          const value = setting.config_value.value;
          formValues[setting.config_key] = typeof value === 'boolean' ? value : (setting.config_type === 'number' ? Number(value) : value)
        }
      });

      setSettingsMap(newSettingsMap);
      setTaxes(taxesRes.data);
      generalSettingsForm.setFieldsValue(formValues);

    } catch (error) {
      message.error('Failed to fetch settings data.');
      console.error(error);
    } finally {
      setGeneralSettingsLoading(false);
    }
  }, [generalSettingsForm]);

  const fetchPaymentMethods = useCallback(async () => {
    setPaymentMethodsLoading(true);
    try {
      const response = await apiClient.get('/v1/billing/payment-methods/', {
        params: { show_all: true }
      });
      setPaymentMethods(response.data);
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to fetch payment methods.');
    } finally {
      setPaymentMethodsLoading(false);
    }
  }, []);

  const fetchAllTaxes = useCallback(async () => {
    setTaxesLoading(true);
    try {
      const response = await apiClient.get('/v1/billing/taxes/', {
        params: { show_all: true } // Fetch all taxes for the management table
      });
      setAllTaxes(response.data);
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to fetch taxes.');
    } finally {
      setTaxesLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGeneralData();
    fetchPaymentMethods();
    fetchAllTaxes();
  }, [fetchGeneralData, fetchPaymentMethods, fetchAllTaxes]);

  const handleGeneralFormFinish = async (values) => {
    setIsSubmittingGeneral(true);

    const promises = Object.values(SETTING_KEYS).map(async (key) => {
        const value = values[key];

        // Determine the correct type for the backend.
        let type;
        if (key.includes('enabled')) {
            type = 'boolean';
        } else if (key.includes('tax_id') || key.includes('terms_days')) {
            type = 'number';
        } else {
            type = 'string';
        }

        // For boolean switches, if the value is not in the form submission, it's false. For others, undefined becomes null.
        const finalValue = type === 'boolean' ? !!value : (value === undefined ? null : value);

        const payload = {
            config_key: key,
            config_value: { value: finalValue },
            config_type: type,
        };

        const existingSetting = settingsMap[key];
        const method = existingSetting ? 'put' : 'post';
        const url = existingSetting ? `/v1/settings/${existingSetting.id}` : '/v1/settings/';
        return apiClient[method](url, payload);
    });

    try {
      await Promise.all(promises);
      message.success('Billing settings saved successfully!');
      fetchGeneralData(); // Refresh data after saving
    } catch (error) {
      message.error('Failed to save one or more settings.');
      console.error(error);
    } finally {
      setIsSubmittingGeneral(false);
    }
  };

  // --- Handlers for Payment Methods Tab ---
  const handlePaymentMethodAdd = () => {
    setEditingPaymentMethod(null);
    paymentMethodsForm.resetFields();
    setIsPaymentMethodModalVisible(true);
  };

  const handlePaymentMethodEdit = (record) => {
    setEditingPaymentMethod(record);
    paymentMethodsForm.setFieldsValue(record);
    setIsPaymentMethodModalVisible(true);
  };

  const handlePaymentMethodDelete = async (id) => {
    try {
      await apiClient.delete(`/v1/billing/payment-methods/${id}`);
      message.success('Payment method deleted successfully.');
      fetchPaymentMethods();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to delete payment method.');
    }
  };

  const handlePaymentMethodModalCancel = () => {
    setIsPaymentMethodModalVisible(false);
    setEditingPaymentMethod(null);
  };

  const handlePaymentMethodFormFinish = async (values) => {
    const url = editingPaymentMethod
      ? `/v1/billing/payment-methods/${editingPaymentMethod.id}`
      : '/v1/billing/payment-methods/';
    const method = editingPaymentMethod ? 'put' : 'post';

    try {
      await apiClient[method](url, values);
      message.success(`Payment method ${editingPaymentMethod ? 'updated' : 'created'} successfully.`);
      handlePaymentMethodModalCancel();
      fetchPaymentMethods();
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save payment method.');
    }
  };

  // --- Handlers for Taxes Tab ---
  const handleTaxAdd = () => {
    setEditingTax(null);
    taxesForm.resetFields();
    setIsTaxModalVisible(true);
  };

  const handleTaxEdit = (record) => {
    setEditingTax(record);
    taxesForm.setFieldsValue({ ...record, rate: Number(record.rate) });
    setIsTaxModalVisible(true);
  };

  const handleTaxDelete = async (id) => {
    try {
      // This is a soft delete (archive) on the backend
      await apiClient.delete(`/v1/billing/taxes/${id}`);
      message.success('Tax archived successfully.');
      fetchAllTaxes();
      fetchGeneralData(); // Also refetch general data as default tax dropdown might change
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to archive tax.');
    }
  };

  const handleTaxModalCancel = () => {
    setIsTaxModalVisible(false);
    setEditingTax(null);
  };

  const handleTaxFormFinish = async (values) => {
    const url = editingTax
      ? `/v1/billing/taxes/${editingTax.id}`
      : '/v1/billing/taxes/';
    const method = editingTax ? 'put' : 'post';

    try {
      // Convert rate to a string decimal format if needed, but backend should handle number
      const payload = { ...values, rate: String(values.rate) };
      await apiClient[method](url, payload);
      message.success(`Tax ${editingTax ? 'updated' : 'created'} successfully.`);
      handleTaxModalCancel();
      fetchAllTaxes();
      fetchGeneralData(); // Also refetch general data as default tax dropdown might change
    } catch (error) {
      message.error(error.response?.data?.detail || 'Failed to save tax.');
    }
  };

  const paymentMethodColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Active', dataIndex: 'is_active', key: 'is_active', render: (isActive) => <Tag color={isActive ? 'green' : 'red'}>{isActive ? 'Yes' : 'No'}</Tag> },
    {
      title: 'Actions', key: 'actions', render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handlePaymentMethodEdit(record)}>Edit</Button>
          <Popconfirm title="Are you sure? This may affect existing payments." onConfirm={() => handlePaymentMethodDelete(record.id)}><Button size="small" danger>Delete</Button></Popconfirm>
        </Space>
      ),
    },
  ];

  const taxColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Rate', dataIndex: 'rate', key: 'rate', render: (rate) => `${(Number(rate) * 100).toFixed(2)}%` },
    { title: 'Archived', dataIndex: 'archived', key: 'archived', render: (archived) => <Tag color={archived ? 'red' : 'green'}>{archived ? 'Yes' : 'No'}</Tag> },
    {
      title: 'Actions', key: 'actions', render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleTaxEdit(record)}>Edit</Button>
          {!record.archived && (
            <Popconfirm title="Are you sure you want to archive this tax? It will no longer be selectable for new tariffs." onConfirm={() => handleTaxDelete(record.id)}>
              <Button size="small" danger>Archive</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <Title level={2}>Billing Settings</Title>
      <Tabs defaultActiveKey="1" 
        items={[
          {
            key: '1',
            label: 'General Settings',
            children: (
              <Spin spinning={generalSettingsLoading} tip="Loading settings...">
                <Divider />
                <Form form={generalSettingsForm} layout="vertical" onFinish={handleGeneralFormFinish}>
                  <Form.Item name={SETTING_KEYS.DEFAULT_TAX_ID} label="Default Tax Rate">
                    <Select placeholder="Select a default tax rate for new services" allowClear>
                      {taxes.map(tax => (
                        <Option key={tax.id} value={tax.id}>{tax.name} ({Number(tax.rate * 100).toFixed(2)}%)</Option>
                      ))}
                    </Select>
                  </Form.Item>
                  <Form.Item name={SETTING_KEYS.INVOICE_PREFIX} label="Invoice Number Prefix" initialValue="INV-">
                    <Input placeholder="e.g., INV-" />
                  </Form.Item>
                  <Form.Item name={SETTING_KEYS.DEFAULT_PAYMENT_TERMS} label="Default Payment Terms (Days)" initialValue={14}>
                    <InputNumber style={{ width: '100%' }} min={0} />
                  </Form.Item>
                  <Form.Item name={SETTING_KEYS.AUTO_INVOICING_ENABLED} label="Enable Automatic Invoice Generation" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                  <Form.Item name={SETTING_KEYS.AUTO_SUSPENSION_ENABLED} label="Enable Automatic Service Suspension for Overdue Payments" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={isSubmittingGeneral}>Save Settings</Button>
                  </Form.Item>
                </Form>
              </Spin>
            )
          },
          {
            key: '2',
            label: 'Payment Methods',
            children: (
              <>
                <Divider />
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                  <Button type="primary" onClick={handlePaymentMethodAdd}>Add Payment Method</Button>
                </div>
                <Table dataSource={paymentMethods} columns={paymentMethodColumns} rowKey="id" loading={paymentMethodsLoading} />
              </>
            )
          },
          {
            key: '3',
            label: 'Taxes',
            children: (
              <>
                <Divider />
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                  <Button type="primary" onClick={handleTaxAdd}>Add Tax</Button>
                </div>
                <Table dataSource={allTaxes} columns={taxColumns} rowKey="id" loading={taxesLoading} />
              </>
            )
          }
        ]}
      />
      <Modal
        title={`${editingPaymentMethod ? 'Edit' : 'Add'} Payment Method`}
        open={isPaymentMethodModalVisible}
        onCancel={handlePaymentMethodModalCancel}
        footer={[<Button key="back" onClick={handlePaymentMethodModalCancel}>Cancel</Button>, <Button key="submit" type="primary" onClick={() => paymentMethodsForm.submit()}>Save</Button>]}
        destroyOnHidden
      >
        <Form form={paymentMethodsForm} layout="vertical" onFinish={handlePaymentMethodFormFinish} initialValues={{ is_active: true }}>
            <Form.Item name="name" label="Name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="is_active" label="Active" valuePropName="checked">
              <Switch />
            </Form.Item>
        </Form>
      </Modal>
      <Modal
        title={`${editingTax ? 'Edit' : 'Add'} Tax`}
        open={isTaxModalVisible}
        onCancel={handleTaxModalCancel}
        footer={[<Button key="back" onClick={handleTaxModalCancel}>Cancel</Button>, <Button key="submit" type="primary" onClick={() => taxesForm.submit()}>Save</Button>]}
        destroyOnHidden
      >
        <Form form={taxesForm} layout="vertical" onFinish={handleTaxFormFinish} initialValues={{ archived: false }}>
            <Form.Item name="name" label="Tax Name" rules={[{ required: true }]}>
              <Input placeholder="e.g., VAT" />
            </Form.Item>
            <Form.Item name="rate" label="Rate" help="Enter the rate as a decimal (e.g., 0.075 for 7.5%)" rules={[{ required: true, type: 'number', min: 0, max: 1 }]}>
              <InputNumber style={{ width: '100%' }} step="0.01" />
            </Form.Item>
            <Form.Item name="archived" label="Archived" valuePropName="checked" help="Archived taxes cannot be used for new tariffs but remain for historical records."><Switch /></Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

export default BillingSettingsPage;