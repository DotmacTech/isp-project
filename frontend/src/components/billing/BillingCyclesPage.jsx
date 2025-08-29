import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Typography,
  Space,
  Popconfirm,
  message,
  Tag,
  Card,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SettingOutlined
} from '@ant-design/icons';
import billingAPI from '../../services/billingAPI';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

function BillingCyclesPage() {
  const [cycles, setCycles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCycle, setEditingCycle] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchCycles();
  }, []);

  const fetchCycles = async () => {
    setLoading(true);
    try {
      const response = await billingAPI.billingCycles.getAll();
      setCycles(response.data);
    } catch (error) {
      message.error('Failed to fetch billing cycles');
      console.error('Fetch cycles error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingCycle(null);
    form.resetFields();
    form.setFieldsValue({
      cycle_type: 'monthly',
      billing_day_type: 'fixed',
      billing_day: 1,
      prorate_first_bill: true,
      prorate_last_bill: true,
      proration_method: 'daily',
      payment_terms_days: 14,
      due_date_type: 'fixed',
      grace_period_days: 0,
      late_fee_type: 'none',
      late_fee_amount: 0,
      is_active: true
    });
    setIsModalVisible(true);
  };

  const handleEdit = (cycle) => {
    setEditingCycle(cycle);
    form.setFieldsValue(cycle);
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await billingAPI.billingCycles.delete(id);
      message.success('Billing cycle deleted successfully');
      fetchCycles();
    } catch (error) {
      message.error('Failed to delete billing cycle');
      console.error('Delete cycle error:', error);
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingCycle(null);
    form.resetFields();
  };

  const handleFormFinish = async (values) => {
    try {
      if (editingCycle) {
        await billingAPI.billingCycles.update(editingCycle.id, values);
        message.success('Billing cycle updated successfully');
      } else {
        await billingAPI.billingCycles.create(values);
        message.success('Billing cycle created successfully');
      }
      setIsModalVisible(false);
      fetchCycles();
    } catch (error) {
      message.error(`Failed to ${editingCycle ? 'update' : 'create'} billing cycle`);
      console.error('Form submission error:', error);
    }
  };

  const getCycleTypeColor = (type) => {
    const colors = {
      monthly: 'blue',
      quarterly: 'green',
      semi_annual: 'orange',
      annual: 'purple',
      custom: 'red'
    };
    return colors[type] || 'default';
  };

  const getLateFeeBadge = (type, amount) => {
    if (type === 'none') return <Tag color="green">No Late Fee</Tag>;
    if (type === 'percentage') return <Tag color="orange">{amount}%</Tag>;
    if (type === 'fixed') return <Tag color="red">${amount}</Tag>;
    return <Tag>-</Tag>;
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Tag color={getCycleTypeColor(record.cycle_type)}>
            {record.cycle_type.replace('_', ' ').toUpperCase()}
          </Tag>
        </div>
      ),
    },
    {
      title: 'Billing Schedule',
      key: 'schedule',
      render: (_, record) => (
        <div>
          <Text>Billing Day: {record.billing_day_type === 'fixed' ? `${record.billing_day}` : 'End of Month'}</Text>
          <br />
          <Text type="secondary">Payment Terms: {record.payment_terms_days} days</Text>
          {record.grace_period_days > 0 && (
            <>
              <br />
              <Text type="secondary">Grace Period: {record.grace_period_days} days</Text>
            </>
          )}
        </div>
      ),
    },
    {
      title: 'Pro-rating',
      key: 'proration',
      render: (_, record) => (
        <div>
          <Text>First Bill: {record.prorate_first_bill ? 'Yes' : 'No'}</Text>
          <br />
          <Text>Last Bill: {record.prorate_last_bill ? 'Yes' : 'No'}</Text>
          <br />
          <Text type="secondary">Method: {record.proration_method}</Text>
        </div>
      ),
    },
    {
      title: 'Late Fees',
      key: 'late_fees',
      render: (_, record) => getLateFeeBadge(record.late_fee_type, record.late_fee_amount),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this billing cycle?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="primary"
              danger
              size="small"
              icon={<DeleteOutlined />}
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2} style={{ margin: 0 }}>
            <SettingOutlined /> Billing Cycles Management
          </Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            Create Billing Cycle
          </Button>
        </div>

        <Table
          dataSource={cycles}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} billing cycles`,
          }}
        />
      </Card>

      <Modal
        title={editingCycle ? 'Edit Billing Cycle' : 'Create Billing Cycle'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFormFinish}
        >
          <Form.Item
            name="name"
            label="Cycle Name"
            rules={[{ required: true, message: 'Please enter cycle name' }]}
          >
            <Input placeholder="e.g., Monthly Standard Billing" />
          </Form.Item>

          <Form.Item
            name="cycle_type"
            label="Cycle Type"
            rules={[{ required: true, message: 'Please select cycle type' }]}
          >
            <Select>
              <Option value="monthly">Monthly</Option>
              <Option value="quarterly">Quarterly</Option>
              <Option value="semi_annual">Semi-Annual</Option>
              <Option value="annual">Annual</Option>
              <Option value="custom">Custom</Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.cycle_type !== currentValues.cycle_type
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('cycle_type') === 'custom' ? (
                <Form.Item
                  name="frequency_days"
                  label="Frequency (Days)"
                  rules={[{ required: true, message: 'Please enter frequency in days' }]}
                >
                  <InputNumber min={1} max={365} />
                </Form.Item>
              ) : null
            }
          </Form.Item>

          <Divider orientation="left">Billing Day Configuration</Divider>

          <Form.Item
            name="billing_day_type"
            label="Billing Day Type"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="fixed">Fixed Day of Month</Option>
              <Option value="end_of_month">End of Month</Option>
              <Option value="custom">Custom Logic</Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.billing_day_type !== currentValues.billing_day_type
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('billing_day_type') === 'fixed' ? (
                <Form.Item
                  name="billing_day"
                  label="Billing Day"
                  rules={[{ required: true, message: 'Please enter billing day' }]}
                >
                  <InputNumber min={1} max={31} />
                </Form.Item>
              ) : null
            }
          </Form.Item>

          <Divider orientation="left">Pro-rating Configuration</Divider>

          <Form.Item name="prorate_first_bill" valuePropName="checked">
            <Switch /> Pro-rate First Bill
          </Form.Item>

          <Form.Item name="prorate_last_bill" valuePropName="checked">
            <Switch /> Pro-rate Last Bill
          </Form.Item>

          <Form.Item name="proration_method" label="Pro-rating Method">
            <Select>
              <Option value="daily">Daily Pro-rating</Option>
              <Option value="monthly">Monthly Pro-rating</Option>
            </Select>
          </Form.Item>

          <Divider orientation="left">Payment Terms</Divider>

          <Form.Item
            name="payment_terms_days"
            label="Payment Terms (Days)"
            rules={[{ required: true, message: 'Please enter payment terms' }]}
          >
            <InputNumber min={0} max={90} />
          </Form.Item>

          <Form.Item name="due_date_type" label="Due Date Type">
            <Select>
              <Option value="fixed">Fixed Days After Invoice</Option>
              <Option value="end_of_month">End of Month</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="grace_period_days"
            label="Grace Period (Days)"
          >
            <InputNumber min={0} max={30} />
          </Form.Item>

          <Divider orientation="left">Late Fee Configuration</Divider>

          <Form.Item name="late_fee_type" label="Late Fee Type">
            <Select>
              <Option value="none">No Late Fee</Option>
              <Option value="percentage">Percentage</Option>
              <Option value="fixed">Fixed Amount</Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.late_fee_type !== currentValues.late_fee_type
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('late_fee_type') !== 'none' ? (
                <Form.Item
                  name="late_fee_amount"
                  label={getFieldValue('late_fee_type') === 'percentage' ? 'Late Fee (%)' : 'Late Fee ($)'}
                  rules={[{ required: true, message: 'Please enter late fee amount' }]}
                >
                  <InputNumber 
                    min={0} 
                    max={getFieldValue('late_fee_type') === 'percentage' ? 100 : undefined}
                    step={getFieldValue('late_fee_type') === 'percentage' ? 0.1 : 0.01}
                  />
                </Form.Item>
              ) : null
            }
          </Form.Item>

          <Form.Item name="is_active" valuePropName="checked">
            <Switch /> Active
          </Form.Item>

          <Form.Item style={{ marginTop: '24px' }}>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingCycle ? 'Update' : 'Create'} Billing Cycle
              </Button>
              <Button onClick={handleModalCancel}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default BillingCyclesPage;