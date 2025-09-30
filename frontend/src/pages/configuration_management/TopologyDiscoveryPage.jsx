import React, { useState, useEffect, useCallback } from 'react';
import { Layout, Typography, Button, Input, Form, Space, Alert, Spin, Card, message } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import apiClient from '../../services/api';
import TopologyVisualization from './TopologyVisualization';

const { Title } = Typography;
const { Content } = Layout;

const TopologyDiscoveryPage = () => {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [error, setError] = useState(null);

  const [form] = Form.useForm();

  const mapApiDataToFlow = (data) => {
    const flowNodes = data.nodes.map((node, index) => ({
      id: node.id.toString(),
      position: { x: (index % 8) * 150, y: Math.floor(index / 8) * 150 }, // Simple initial layout
      data: { 
        label: `${node.label} (${node.type})`,
        type: node.type,
        status: node.status,
      },
      style: {
        background: node.status === 'online' ? '#d6f9e2' : '#f8d7da',
        borderColor: node.status === 'online' ? '#28a745' : '#dc3545',
      }
    }));

    const flowEdges = data.edges.map((edge, index) => ({
      id: `e${edge.from}-${edge.to}-${index}`,
      source: edge.from.toString(),
      target: edge.to.toString(),
      label: edge.label,
      animated: true,
    }));

    return { nodes: flowNodes, edges: flowEdges };
  };

  const fetchTopologyData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/v1/network/topology/visualization');
      const data = response.data;
      if (data && data.nodes && data.nodes.length > 0) {
        const { nodes: flowNodes, edges: flowEdges } = mapApiDataToFlow(data);
        setNodes(flowNodes);
        setEdges(flowEdges);
      } else {
        setNodes([]);
        setEdges([]);
      }
    } catch (err) {
      message.error('Failed to fetch topology data.');
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopologyData();
  }, [fetchTopologyData]);

  const onDiscover = async (values) => {
    setDiscovering(true);
    setError(null);
    try {
      await apiClient.post('/v1/network/topology/discover', null, { params: values });
      message.success('Discovery initiated successfully.');
      fetchTopologyData();
    } catch (err) {
      message.error(`Discovery failed: ${err.message}`);
      setError(`Discovery failed: ${err.message}`);
    } finally {
      setDiscovering(false);
    }
  };

  return (
    <Content className="p-6">
      <Title level={2}>Network Topology</Title>

      <Card className="mb-6">
        <Space size="middle" wrap>
          <Form
            form={form}
            layout="inline"
            onFinish={onDiscover}
            initialValues={{
              start_ip: '192.168.1.1',
              subnet_mask: '/24',
              community: 'public',
            }}
          >
            <Form.Item name="start_ip" label="Start IP">
              <Input />
            </Form.Item>
            <Form.Item name="subnet_mask" label="Subnet">
              <Input />
            </Form.Item>
            <Form.Item name="community" label="SNMP Community">
              <Input />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={discovering} icon={<SearchOutlined />}>
                {discovering ? 'Discovering...' : 'Run Discovery'}
              </Button>
            </Form.Item>
          </Form>
          <Button onClick={fetchTopologyData} loading={loading} icon={<ReloadOutlined />}>
            {loading ? 'Refreshing...' : 'Refresh View'}
          </Button>
        </Space>
      </Card>

      {error && <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} className="mb-6" />}

      <Card>
        <div className="h-100">
          {loading ? (
            <Spin tip="Loading topology...">
              <div className="h-100 d-flex justify-content-center align-items-center"></div>
            </Spin>
          ) : nodes.length > 0 ? (
            <TopologyVisualization initialNodes={nodes} initialEdges={edges} />
          ) : (
            <div className="text-center p-12 h-100 d-flex flex-column justify-content-center align-items-center bg-light-gray rounded">
              <p>No topology data found.</p>
              <p>Run a discovery scan to build the network map.</p>
            </div>
          )}
        </div>
      </Card>
    </Content>
  );
};

export default TopologyDiscoveryPage;