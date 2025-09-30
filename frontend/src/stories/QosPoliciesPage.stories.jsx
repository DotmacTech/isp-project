import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { rest } from 'msw';
import QosPoliciesPage from '../pages/performance_management/QosPoliciesPage';

export default {
  title: 'Pages/Network/QoS Policies',
  component: QosPoliciesPage,
  decorators: [
    (Story) => (
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<Story />} />
        </Routes>
      </MemoryRouter>
    ),
  ],
  parameters: {
    msw: {
      handlers: [
        rest.get('/v1/network/qos-policies/', (req, res, ctx) => {
          return res(
            ctx.json({
              total: 2,
              items: [
                { id: 1, name: 'Gold Plan', policy_type: 'rate_limit', download_rate_kbps: 50000, upload_rate_kbps: 10000, priority: 1, is_active: true },
                { id: 2, name: 'Silver Plan', policy_type: 'rate_limit', download_rate_kbps: 25000, upload_rate_kbps: 5000, priority: 2, is_active: true },
              ],
            })
          );
        }),
        rest.post('/v1/network/qos-policies/', async (req, res, ctx) => {
            const body = await req.json();
            return res(ctx.status(201), ctx.json({ id: 3, ...body }));
        }),
        rest.put('/v1/network/qos-policies/:id', async (req, res, ctx) => {
            const body = await req.json();
            return res(ctx.json({ id: parseInt(req.params.id, 10), ...body }));
        }),
        rest.delete('/v1/network/qos-policies/:id', (req, res, ctx) => {
            return res(ctx.status(204));
        }),
      ],
    },
  },
};

const Template = (args) => <QosPoliciesPage {...args} />;

export const Default = Template.bind({});
Default.args = {};