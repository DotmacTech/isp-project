import React, { useState } from 'react';
import {
  Table, Button, Modal, Form, Input, message, Popconfirm, Card, Typography, Tag, Space, Descriptions
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { getRadiusUser, createOrUpdateRadiusUser, deleteRadiusUser } from '../../services/freeRadiusApi';

const { Title } = Typography;
const { Search } = Input;

const RadiusUsers = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isViewModalVisible, setIsViewModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form] = Form.useForm();

  const handleSearch = (username) => {
    if (!username) {
      setUser(null);
      return;
    }
    setLoading(true);
    getRadiusUser(username)
      .then(response => {
        setUser(response.data);
        message.success(`Found user: ${username}`);
      })
      .catch(error => {
        setUser(null);
        message.warn(`User '${username}' not found or an error occurred.`);
      })
      .finally(() => setLoading(false));
  };

  const handleCreate = () => {
    setEditingUser(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = () => {
    if (!user) return;
    const rateLimitAttr = user.reply_attributes.find(attr => attr.attribute === 'Mikrotik-Rate-Limit');
    const ipAttr = user.reply_attributes.find(attr => attr.attribute === 'Framed-IP-Address');

    const initialValues = {
      username: user.username,
      password: '', // Never pre-fill password
      rate_limit: rateLimitAttr ? rateLimitAttr.value : '',
      framed_ip_address: ipAttr ? ipAttr.value : '',
    };
    setEditingUser(initialValues);
    form.setFieldsValue(initialValues);
    setIsModalVisible(true);
  };

  const handleDelete = () => {
    if (!user) return;
    setLoading(true);
    deleteRadiusUser(user.username)
      .then(() => {
        message.success(`User '${user.username}' deleted successfully.`);
        setUser(null);
      })
      .catch(() => message.error('Failed to delete user.'))
      .finally(() => setLoading(false));
  };

  const handleOk = () => {
    form.validateFields().then(values => {
      setLoading(true);
      const payload = {
        username: editingUser ? editingUser.username : values.username,
        password: values.password,
        rate_limit: values.rate_limit || null,
        framed_ip_address: values.framed_ip_address || null,
      };
      createOrUpdateRadiusUser(payload)
        .then(response => {
          message.success(`User '${payload.username}' saved successfully.`);
          setUser(response.data);
          setIsModalVisible(false);
        })
        .catch(() => message.error('Failed to save user.'))
        .finally(() => setLoading(false));
    });
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Card>
        <Space>
          <Search
            placeholder="Enter username to find"
            onSearch={handleSearch}
            enterButton
            loading={loading}
            style={{ width: 300 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Create User
          </Button>
        </Space>
      </Card>

      {user && (
        <Card
          title={<Title level={4}>User: {user.username}</Title>}
          actions={[
            <Button icon={<EyeOutlined />} key="view" onClick={() => setIsViewModalVisible(true)}>View Details</Button>,
            <Button icon={<EditOutlined />} key="edit" onClick={handleEdit}>Edit</Button>,
            <Popconfirm title="Delete this user?" onConfirm={handleDelete} okText="Yes" cancelText="No">
              <Button danger icon={<DeleteOutlined />} key="delete">Delete</Button>
            </Popconfirm>,
          ]}
        >
          <Descriptions size="small" bordered>
            <Descriptions.Item label="Check Attributes" span={3}>
              {user.check_attributes.map(attr => (
                <Tag color="blue" key={attr.id}>{`${attr.attribute} ${attr.op} ${attr.attribute === 'Cleartext-Password' ? '********' : attr.value}`}</Tag>
              ))}
            </Descriptions.Item>
            <Descriptions.Item label="Reply Attributes" span={3}>
              {user.reply_attributes.map(attr => (
                <Tag color="green" key={attr.id}>{`${attr.attribute} ${attr.op} ${attr.value}`}</Tag>
              ))}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      <Modal
        title={editingUser ? 'Edit RADIUS User' : 'Create RADIUS User'}
        open={isModalVisible}
        onOk={handleOk}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical" name="radius_user_form">
          <Form.Item name="username" label="Username" rules={[{ required: true }]}>
            <Input disabled={!!editingUser} />
          </Form.Item>
          <Form.Item name="password" label={editingUser ? "New Password (leave blank to keep)" : "Password"} rules={[{ required: !editingUser }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="rate_limit" label="Rate Limit (e.g., 10M/2M)" help="Mikrotik-Rate-Limit attribute">
            <Input />
          </Form.Item>
          <Form.Item name="framed_ip_address" label="Framed IP Address" help="Static IP for the user">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {user && (
        <Modal title={`Details for ${user.username}`} open={isViewModalVisible} onCancel={() => setIsViewModalVisible(false)} footer={null} width={800}>
          <Title level={5}>Check Attributes</Title>
          <Table
            dataSource={user.check_attributes}
            columns={[
              { title: 'Attribute', dataIndex: 'attribute', key: 'attr' },
              { title: 'Operator', dataIndex: 'op', key: 'op' },
              { title: 'Value', dataIndex: 'value', key: 'val', render: (val, rec) => rec.attribute === 'Cleartext-Password' ? '********' : val },
            ]}
            rowKey="id" pagination={false} size="small"
          />
          <Title level={5} style={{ marginTop: 16 }}>Reply Attributes</Title>
          <Table
            dataSource={user.reply_attributes}
            columns={[
              { title: 'Attribute', dataIndex: 'attribute', key: 'attr' },
              { title: 'Operator', dataIndex: 'op', key: 'op' },
              { title: 'Value', dataIndex: 'value', key: 'val' },
            ]}
            rowKey="id" pagination={false} size="small"
          />
        </Modal>
      )}
    </Space>
  );
};

export default RadiusUsers;