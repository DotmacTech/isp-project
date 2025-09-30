import React from 'react';
import { Card, Typography, Row, Col, Tag, Divider } from 'antd';

const { Title, Paragraph, Text } = Typography;

export default {
  title: 'Welcome',
  parameters: {
    layout: 'fullscreen',
  },
};

export const Introduction = () => (
  <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
    <Title level={1}>ISP Billing System - Component Library</Title>
    <Paragraph style={{ fontSize: '16px', marginBottom: '40px' }}>
      Welcome to the ISP Billing System component library! This Storybook contains all the reusable
      components, design patterns, and documentation for our comprehensive Internet Service Provider
      billing and management platform.
    </Paragraph>

    <Row gutter={[24, 24]}>
      <Col span={12}>
        <Card title="🏗️ Design System" hoverable>
          <Paragraph>
            Explore our design system components including buttons, forms, tables, and other
            UI elements that maintain consistency across the application.
          </Paragraph>
          <div>
            <Tag color="blue">Buttons</Tag>
            <Tag color="green">Forms</Tag>
            <Tag color="orange">Tables</Tag>
            <Tag color="purple">Icons</Tag>
          </div>
        </Card>
      </Col>

      <Col span={12}>
        <Card title="💰 Billing Components" hoverable>
          <Paragraph>
            Components specific to billing functionality including invoice management,
            payment processing, customer billing configurations, and financial reporting.
          </Paragraph>
          <div>
            <Tag color="cyan">Invoices</Tag>
            <Tag color="geekblue">Payments</Tag>
            <Tag color="gold">Reports</Tag>
            <Tag color="lime">Analytics</Tag>
          </div>
        </Card>
      </Col>

      <Col span={12}>
        <Card title="🌐 Network Management" hoverable>
          <Paragraph>
            Network monitoring and management components for device configuration,
            performance analytics, and network topology visualization.
          </Paragraph>
          <div>
            <Tag color="red">Devices</Tag>
            <Tag color="volcano">Monitoring</Tag>
            <Tag color="orange">Performance</Tag>
            <Tag color="gold">Topology</Tag>
          </div>
        </Card>
      </Col>

      <Col span={12}>
        <Card title="📱 Pages" hoverable>
          <Paragraph>
            Complete page components showcasing how individual components work together
            to create full user interfaces and workflows.
          </Paragraph>
          <div>
            <Tag color="magenta">Login</Tag>
            <Tag color="red">Dashboard</Tag>
            <Tag color="volcano">Settings</Tag>
            <Tag color="orange">Reports</Tag>
          </div>
        </Card>
      </Col>
    </Row>

    <Divider />

    <Title level={2}>🚀 Getting Started</Title>
    <Row gutter={[24, 24]}>
      <Col span={8}>
        <Card size="small">
          <Title level={4}>1. Explore Components</Title>
          <Paragraph>
            Browse through the component categories in the sidebar to see available components
            and their variations.
          </Paragraph>
        </Card>
      </Col>
      <Col span={8}>
        <Card size="small">
          <Title level={4}>2. View Documentation</Title>
          <Paragraph>
            Each component includes comprehensive documentation with props, usage examples,
            and best practices.
          </Paragraph>
        </Card>
      </Col>
      <Col span={8}>
        <Card size="small">
          <Title level={4}>3. Test Interactions</Title>
          <Paragraph>
            Use the Controls panel to modify component props in real-time and see how
            they behave.
          </Paragraph>
        </Card>
      </Col>
    </Row>

    <Divider />

    <Title level={2}>🛠️ Development</Title>
    <Paragraph>
      This component library is built with:
    </Paragraph>
    <ul>
      <li><Text strong>React 19</Text> - Frontend framework</li>
      <li><Text strong>Ant Design</Text> - UI component library</li>
      <li><Text strong>Vite</Text> - Build tool and development server</li>
      <li><Text strong>Storybook 8</Text> - Component development environment</li>
    </ul>

    <Divider />

    <Title level={2}>📋 Component Categories</Title>
    <Row gutter={[16, 16]}>
      <Col span={6}>
        <Card size="small" title="Design System" style={{ textAlign: 'center' }}>
          <Text>Core UI components and design patterns</Text>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" title="Billing" style={{ textAlign: 'center' }}>
          <Text>Billing and financial management components</Text>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" title="Network" style={{ textAlign: 'center' }}>
          <Text>Network management and monitoring tools</Text>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" title="Pages" style={{ textAlign: 'center' }}>
          <Text>Complete page layouts and workflows</Text>
        </Card>
      </Col>
    </Row>
  </div>
);
