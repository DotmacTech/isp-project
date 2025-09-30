import React from 'react';
import { Card, Statistic, Typography, Space } from 'antd';

const { Text } = Typography;

const StatCard = ({ title, value, unit, icon }) => {
  return (
    <Card>
      <Space align="center">
        {icon && <div style={{ fontSize: '2rem', color: '#007bff' }}>{icon}</div>}
        <div>
          <Text type="secondary" strong style={{ textTransform: 'uppercase', fontSize: '0.9rem' }}>{title}</Text>
          <Statistic value={value} suffix={unit} valueStyle={{ fontSize: '1.75rem' }} />
        </div>
      </Space>
    </Card>
  );
};

export default StatCard;