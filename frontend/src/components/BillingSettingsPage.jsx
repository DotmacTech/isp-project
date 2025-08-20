import React, { useState, useEffect, useCallback } from 'react';
import { Form, Input, Button, message, Spin, Typography, Switch, Select, InputNumber, Card, Divider } from 'antd';
import axios from 'axios';

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
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [taxes, setTaxes] = useState([]);
  const [settingsMap, setSettingsMap] = useState({});

  const fetchData = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      message.error('Authentication required.');
      return;
    }

    try {
      const [settingsRes, taxesRes] = await Promise.all([
        axios.get('/api/v1/settings/', { headers: { Authorization: `Bearer ${token}` } }),
        axios.get('/api/v1/billing/taxes/', { headers: { Authorization: `Bearer ${token}` } })
      ]);

      const settingsData = settingsRes.data;
      const newSettingsMap = {};
      const formValues = {};

      settingsData.forEach(setting => {
        newSettingsMap[setting.config_key] = setting;
        if (setting.config_key in SETTING_KEYS) {
          formValues[setting.config_key] = setting.config_value.value;
        }
      });

      setSettingsMap(newSettingsMap);
      setTaxes(taxesRes.data);
      form.setFieldsValue(formValues);

    } catch (error) {
      message.error('Failed to fetch settings data.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [form]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFormFinish = async (values) => {
    setIsSubmitting(true);
    const token = localStorage.getItem('access_token');

    const promises = Object.entries(values).map(async ([key, value]) => {
      const existingSetting = settingsMap[key];
      const payload = {
        config_key: key,
        config_value: { value }, // Store as a JSON object
        config_type: typeof value,
      };

      if (existingSetting) {
        return axios.put(`/api/v1/settings/${existingSetting.id}`, payload, { headers: { Authorization: `Bearer ${token}` } });
      } else {
        return axios.post('/api/v1/settings/', payload, { headers: { Authorization: `Bearer ${token}` } });
      }
    });

    try {
      await Promise.all(promises);
      message.success('Billing settings saved successfully!');
      fetchData(); // Refresh data after saving
    } catch (error) {
      message.error('Failed to save one or more settings.');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Spin spinning={loading} tip="Loading settings...">
      <Card>
        <Title level={2}>Billing Settings</Title>
        <Divider />
        <Form form={form} layout="vertical" onFinish={handleFormFinish}>
          <Form.Item name={SETTING_KEYS.DEFAULT_TAX_ID} label="Default Tax Rate">
            <Select placeholder="Select a default tax rate for new services">
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
            <Button type="primary" htmlType="submit" loading={isSubmitting}>Save Settings</Button>
          </Form.Item>
        </Form>
      </Card>
    </Spin>
  );
}

export default BillingSettingsPage;