import React from 'react';
import { Timeline, Tag, Typography, Space } from 'antd';
import { ClockCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

const IncidentTimeline = ({ updates }) => {
  const formatDate = (dateString) => new Date(dateString).toLocaleString();

  return (
    <Timeline mode="left">
      {updates.map(update => (
        <Timeline.Item
          key={update.id}
          dot={update.update_type === 'status_change' ? <ClockCircleOutlined /> : null} // Example dot based on type
          color={update.is_internal ? 'gray' : 'blue'} // Example color based on internal note
        >
          <Space direction="vertical" size={4}>
            <Space wrap>
              <Tag color={update.update_type === 'comment' ? 'blue' : 'geekblue'}>{update.update_type.toUpperCase()}</Tag>
              {update.is_internal && <Tag color="gold">INTERNAL</Tag>}
              <Text type="secondary">{formatDate(update.created_at)}</Text>
            </Space>
            <Text>{update.content}</Text>
          </Space>
        </Timeline.Item>
      ))}
    </Timeline>
  );
};

export default IncidentTimeline;