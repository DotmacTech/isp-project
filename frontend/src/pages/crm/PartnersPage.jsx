import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, message, Popconfirm, Space, Typography } from 'antd';
import apiClient from '../../services/api';

const { Title } = Typography;

const PartnersPage = () => {
    const [partners, setPartners] = useState([]);
    const [loading, setLoading] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingPartner, setEditingPartner] = useState(null);
    const [form] = Form.useForm();

    const fetchPartners = async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/v1/partners/');
            setPartners(response.data.items);
        } catch (error) {
            message.error('Failed to fetch partners.');
            console.error("Fetch partners error:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPartners();
    }, []);

    const handleAdd = () => {
        setEditingPartner(null);
        form.resetFields();
        setIsModalOpen(true);
    };

    const handleEdit = (record) => {
        setEditingPartner(record);
        form.setFieldsValue(record);
        setIsModalOpen(true);
    };

    const handleOk = async () => {
        try {
            const values = await form.validateFields();
            
            if (editingPartner) {
                // Update existing partner
                await apiClient.put(`/v1/partners/${editingPartner.id}`, values);
                message.success('Partner updated successfully');
            } else {
                // Create new partner
                await apiClient.post('/v1/partners/', values);
                message.success('Partner created successfully');
            }
            setIsModalOpen(false);
            fetchPartners(); // Refresh the list
        } catch (error) {
            message.error(error.response?.data?.detail || 'Failed to save partner.');
            console.error("Save partner error:", error);
        }
    };

    const handleCancel = () => {
        setIsModalOpen(false);
    };

    const handleDelete = async (id) => {
        try {
            await apiClient.delete(`/v1/partners/${id}`);
            message.success('Partner deleted successfully');
            fetchPartners(); // Refresh the list
        } catch (error) {
            message.error(error.response?.data?.detail || 'Failed to delete partner.');
            console.error("Delete partner error:", error);
        }
    };

    const columns = [
        {
            title: 'ID',
            dataIndex: 'id',
            key: 'id',
            sorter: (a, b) => a.id - b.id,
        },
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a, b) => a.name.localeCompare(b.name),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space size="middle">
                    <Button type="link" onClick={() => handleEdit(record)}>Edit</Button>
                    <Popconfirm
                        title="Are you sure to delete this partner?"
                        description="This action cannot be undone."
                        onConfirm={() => handleDelete(record.id)}
                        okText="Yes"
                        cancelText="No"
                    >
                        <Button type="link" danger>Delete</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div>
            <Title level={4}>Manage Partners</Title>
            <Button onClick={handleAdd} type="primary" style={{ marginBottom: 16 }}>
                Add Partner
            </Button>
            <Table
                columns={columns}
                dataSource={partners}
                loading={loading}
                rowKey="id"
            />
            <Modal
                title={editingPartner ? 'Edit Partner' : 'Add Partner'}
                open={isModalOpen}
                onOk={handleOk}
                onCancel={handleCancel}
                okText="Save"
                cancelText="Cancel"
            >
                <Form form={form} layout="vertical" name="partner_form">
                    <Form.Item
                        name="name"
                        label="Partner Name"
                        rules={[{ required: true, message: 'Please input the partner name!' }]}
                    >
                        <Input />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default PartnersPage;