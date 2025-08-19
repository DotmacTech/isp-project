import React from 'react';
import { Card, Col, Row, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

function DashboardContent() {
    return (
        <div className="site-statistic-demo-card">
            <Row gutter={16}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Active Users"
                            value={112893}
                            precision={0}
                            valueStyle={{ color: '#3f8600' }}
                            prefix={<ArrowUpOutlined />}
                            suffix=""
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Online Devices"
                            value={93}
                            precision={0}
                            valueStyle={{ color: '#3f8600' }}
                            prefix={<ArrowUpOutlined />}
                            suffix=""
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Open Tickets"
                            value={12}
                            precision={0}
                            valueStyle={{ color: '#cf1322' }}
                            prefix={<ArrowDownOutlined />}
                            suffix=""
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Revenue (Today)"
                            value={5600}
                            precision={2}
                            valueStyle={{ color: '#3f8600' }}
                            prefix="$"
                            suffix=""
                        />
                    </Card>
                </Col>
            </Row>
        </div>
    );
}

export default DashboardContent;