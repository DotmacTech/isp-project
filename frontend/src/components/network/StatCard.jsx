import React from 'react';
import { Card, Statistic } from 'antd';

const StatCard = ({ title, value, unit }) => {
  return (
    <Card>
      <Statistic title={title} value={value} suffix={unit} />
    </Card>
  );
};

export default StatCard;