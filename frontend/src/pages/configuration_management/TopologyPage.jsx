import React, { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Form,
  Input,
  Spin,
  Alert,
  Row,
  Col,
  Card,
  Typography,
  message,
} from 'antd';
import { RedoOutlined, ApartmentOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import TopologyVisualization from '../../components/network/TopologyVisualization';

const { Title } = Typography;

const TopologyPage = () => {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [error, setError] = useState(null);
  const [form] = Form.useForm();

  const mapApiDataToFlow = (data) => {
    const flowNodes = data.nodes.map((node, index) => ({
      id: node.id.toString(),
      position: { x: (index % 8) * 150, y: Math.floor(index / 8) * 150 },
      data: {
        label: `${node.label} (${node.type})`,
        type: node.type,
        status: node.status,
      },
      style: {
        background: node.status === 'online' ? '#d6f9e2' : '#f8d7da',
        borderColor: node.status === 'online' ? '#28a745' : '#dc3545',
      },
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
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopologyData();
  }, [fetchTopologyData]);

  const handleDiscover = async (values) => {
    setDiscovering(true);
    setError(null);
    try {
      await apiClient.post('/v1/network/topology/discover', null, { params: values });
      message.success('Network discovery initiated successfully!');
      fetchTopologyData();
    } catch (err) {
      setError(`Discovery failed: ${err.message}`);
    } finally {
      setDiscovering(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>Network Topology</Title>
      <Card style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={handleDiscover}
          initialValues={{
            start_ip: '192.168.1.1',
            subnet_mask: '/24',
            community: 'public',
          }}
        >
          <Row gutter={16} style={{ width: '100%' }}>
            <Col>
              <Form.Item name="start_ip" label="Start IP">
                <Input />
              </Form.Item>
            </Col>
            <Col>
              <Form.Item name="subnet_mask" label="Subnet">
                <Input />
              </Form.Item>
            </Col>
            <Col>
              <Form.Item name="community" label="SNMP Community">
                <Input />
              </Form.Item>
            </Col>
            <Col>
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={discovering}
                  icon={<ApartmentOutlined />}
                >
                  Run Discovery
                </Button>
              </Form.Item>
            </Col>
            <Col>
              <Form.Item>
                <Button
                  onClick={fetchTopologyData}
                  loading={loading}
                  icon={<RedoOutlined />}
                >
                  Refresh View
                </Button>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 24 }} />}

      <Card>
        <div style={{ height: 600, width: '100%' }}>
          <Spin spinning={loading} tip="Loading topology...">
            {nodes.length > 0 ? (
              <TopologyVisualization initialNodes={nodes} initialEdges={edges} />
            ) : (
              <div style={{ textAlign: 'center', paddingTop: 100 }}>
                <p>No topology data found.</p>
                <p>Run a discovery scan to build the network map.</p>
              </div>
            )}
          </Spin>
        </div>
      </Card>
    </div>
  );
};

export default TopologyPage;
