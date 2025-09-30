import React from 'react';
import { Button } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, DownloadOutlined } from '@ant-design/icons';

export default {
  title: 'Design System/Button',
  component: Button,
  argTypes: {
    type: {
      control: { type: 'select' },
      options: ['default', 'primary', 'dashed', 'text', 'link'],
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'middle', 'large'],
    },
    shape: {
      control: { type: 'select' },
      options: ['default', 'circle', 'round'],
    },
    danger: {
      control: { type: 'boolean' },
    },
    disabled: {
      control: { type: 'boolean' },
    },
    loading: {
      control: { type: 'boolean' },
    },
    block: {
      control: { type: 'boolean' },
    },
  },
  tags: ['autodocs'],
};

const Template = (args) => <Button {...args} />;

export const Default = Template.bind({});
Default.args = {
  children: 'Default Button',
};

export const Primary = Template.bind({});
Primary.args = {
  type: 'primary',
  children: 'Primary Button',
};

export const Danger = Template.bind({});
Danger.args = {
  danger: true,
  children: 'Danger Button',
};

export const Loading = Template.bind({});
Loading.args = {
  type: 'primary',
  loading: true,
  children: 'Loading Button',
};

export const WithIcon = Template.bind({});
WithIcon.args = {
  type: 'primary',
  icon: <PlusOutlined />,
  children: 'Add Item',
};

export const IconOnly = Template.bind({});
IconOnly.args = {
  type: 'primary',
  shape: 'circle',
  icon: <EditOutlined />,
};

export const ButtonGroup = () => (
  <Button.Group>
    <Button type="primary">
      <PlusOutlined />
      Add
    </Button>
    <Button>
      <EditOutlined />
      Edit
    </Button>
    <Button danger>
      <DeleteOutlined />
      Delete
    </Button>
    <Button>
      <DownloadOutlined />
      Export
    </Button>
  </Button.Group>
);

export const Sizes = () => (
  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
    <Button size="small" type="primary">Small</Button>
    <Button size="middle" type="primary">Middle</Button>
    <Button size="large" type="primary">Large</Button>
  </div>
);

export const Types = () => (
  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
    <Button>Default</Button>
    <Button type="primary">Primary</Button>
    <Button type="dashed">Dashed</Button>
    <Button type="text">Text</Button>
    <Button type="link">Link</Button>
  </div>
);