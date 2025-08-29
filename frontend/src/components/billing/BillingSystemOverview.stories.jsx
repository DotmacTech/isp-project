import BillingSystemOverview from './billing/BillingSystemOverview';

export default {
  title: 'Billing/BillingSystemOverview',
  component: BillingSystemOverview,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => {
      // Mock API calls and localStorage
      const mockLocalStorage = {
        getItem: (key) => {
          if (key === 'access_token') return 'mock_token_12345';
          return null;
        },
      };
      
      // Mock window.localStorage
      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true,
      });
      
      return (
        <div style={{ padding: '20px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
          <Story />
        </div>
      );
    },
  ],
};

// Default billing overview
export const Default = {
  args: {},
};

// With loading state
export const Loading = {
  args: {},
  decorators: [
    (Story) => {
      // Mock the loading state by intercepting API calls
      const originalFetch = window.fetch;
      window.fetch = () => new Promise(() => {}); // Never resolves to show loading
      
      const result = Story();
      
      // Restore fetch after a timeout
      setTimeout(() => {
        window.fetch = originalFetch;
      }, 5000);
      
      return result;
    },
  ],
};

// With mock data
export const WithMockData = {
  args: {},
  decorators: [
    (Story) => {
      // Mock successful API responses
      const originalFetch = window.fetch;
      window.fetch = (url) => {
        const mockResponses = {
          '/api/v1/billing/dashboard/stats/': {
            ok: true,
            json: () => Promise.resolve({
              total_revenue: 125000.50,
              monthly_revenue: 45000.00,
              total_customers: 1500,
              active_customers: 1420,
              total_invoices: 850,
              overdue_invoices: 25,
              total_payments: 780,
              pending_payments: 15,
            }),
          },
          '/api/v1/billing/dashboard/recent-invoices/': {
            ok: true,
            json: () => Promise.resolve({
              items: [
                {
                  id: 1,
                  invoice_number: 'INV-2024-001',
                  customer_name: 'Acme Corp',
                  amount: 2500.00,
                  status: 'paid',
                  due_date: '2024-01-15',
                },
                {
                  id: 2,
                  invoice_number: 'INV-2024-002',
                  customer_name: 'Tech Solutions Ltd',
                  amount: 1800.00,
                  status: 'pending',
                  due_date: '2024-01-20',
                },
              ],
            }),
          },
        };
        
        if (url.includes('/api/v1/billing/')) {
          const mockResponse = mockResponses[url] || mockResponses[Object.keys(mockResponses).find(key => url.includes(key))];
          if (mockResponse) {
            return Promise.resolve(mockResponse);
          }
        }
        
        return originalFetch(url);
      };
      
      const result = Story();
      
      // Restore fetch
      setTimeout(() => {
        window.fetch = originalFetch;
      }, 100);
      
      return result;
    },
  ],
};