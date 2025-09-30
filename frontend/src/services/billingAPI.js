import apiClient from './api';

// Basic Customers API (used by billing components)
export const customersAPI = {
  getAll: (params = {}) =>
    apiClient.get('/v1/customers/', { params }),
  
  getById: (id) =>
    apiClient.get(`/v1/customers/${id}/`)
};

// Billing Cycles API
export const billingCyclesAPI = {
  getAll: (params = {}) =>
    apiClient.get('/v1/billing/cycles/', { params }),
  
  create: (data) =>
    apiClient.post('/v1/billing/cycles/', data),
  
  getById: (id) =>
    apiClient.get(`/v1/billing/cycles/${id}/`),
  
  update: (id, data) =>
    apiClient.put(`/v1/billing/cycles/${id}/`, data),
  
  delete: (id) =>
    apiClient.delete(`/v1/billing/cycles/${id}/`)
};

// Customer Billing Configuration API
export const customerBillingConfigAPI = {
  getAll: (params = {}) =>
    apiClient.get('/v1/billing/customer-config/', { params }),
  
  getByCustomerId: (customerId) =>
    apiClient.get(`/v1/billing/customer-config/${customerId}/`),
  
  create: (data) =>
    apiClient.post('/v1/billing/customer-config/', data),
  
  update: (customerId, data) =>
    apiClient.put(`/v1/billing/customer-config/${customerId}/`, data),
  
  delete: (customerId) =>
    apiClient.delete(`/v1/billing/customer-config/${customerId}/`)
};

// Enhanced Billing Engine Operations API
export const billingEngineAPI = {
  runBilling: () =>
    apiClient.post('/v1/billing/run-billing/'),
  
  runDunning: () =>
    apiClient.post('/v1/billing/run-dunning/'),
  
  processPaymentAllocation: (paymentId, strategy = 'oldest_first') =>
    apiClient.post(`/v1/billing/process-payment-allocation/${paymentId}/`, {}, {
      params: { allocation_strategy: strategy }
    }),
  
  healthCheck: () =>
    apiClient.get('/v1/billing/health-check/')
};

// Usage Tracking API
export const usageTrackingAPI = {
  getAll: (params = {}) =>
    apiClient.get('/v1/billing/usage/', { params }),
  
  create: (data) =>
    apiClient.post('/v1/billing/usage/', data),
  
  getCustomerUsage: (customerId, startDate, endDate) =>
    apiClient.get(`/v1/billing/usage/${customerId}/`, {
      params: { start_date: startDate, end_date: endDate }
    })
};

// Billing Events (Audit Trail) API
export const billingEventsAPI = {
  getAll: (params = {}) =>
    apiClient.get('/v1/billing/events/', { params }),
  
  create: (data) =>
    apiClient.post('/v1/billing/events/', data)
};

// Enhanced Analytics API
export const billingAnalyticsAPI = {
  getRevenueAnalytics: (data) =>
    apiClient.post('/v1/billing/analytics/revenue/', data),
  
  getAgingAnalytics: (data) =>
    apiClient.post('/v1/billing/analytics/aging/', data),
  
  getPaymentAnalytics: (data) =>
    apiClient.post('/v1/billing/analytics/payments/', data)
};

// Enhanced Tax Management API
export const taxManagementAPI = {
  getApplicableTaxes: (serviceType, locationId = null) =>
    apiClient.get('/v1/billing/taxes/applicable/', {
      params: { service_type: serviceType, location_id: locationId }
    })
};

// Customer Account Management API
export const customerAccountAPI = {
  getOverdueInvoices: (customerId) =>
    apiClient.get(`/v1/billing/customers/${customerId}/overdue-invoices/`),
  
  getOutstandingInvoices: (customerId) =>
    apiClient.get(`/v1/billing/customers/${customerId}/outstanding-invoices/`),
  
  getCreditBalance: (customerId) =>
    apiClient.get(`/v1/billing/customers/${customerId}/credit-balance/`)
};

// Payment Gateways API
export const paymentGatewaysAPI = {
  getAll: (params = {}) =>
    apiClient.get('/v1/billing/payment-gateways/', { params }),
  
  getById: (id) =>
    apiClient.get(`/v1/billing/payment-gateways/${id}/`),

  create: (data) =>
    apiClient.post('/v1/billing/payment-gateways/', data),
  
  update: (id, data) =>
    apiClient.put(`/v1/billing/payment-gateways/${id}/`, data),
  
  delete: (id) =>
    apiClient.delete(`/v1/billing/payment-gateways/${id}/`),

};

// Enhanced Invoices API (extends existing)
export const enhancedInvoicesAPI = {
  getAll: (params = {}) =>
    apiClient.get('/v1/billing/invoices/', { params }),
  
  create: (data) =>
    apiClient.post('/v1/billing/invoices/', data),
  
  getById: (id) =>
    apiClient.get(`/v1/billing/invoices/${id}/`),
  
  update: (id, data) =>
    apiClient.put(`/v1/billing/invoices/${id}/`, data),
  
  // Enhanced features
  generateForCustomer: (customerId) =>
    apiClient.post(`/v1/billing/invoices/generate/${customerId}/`),
  
  applyCredit: (invoiceId, amount) =>
    apiClient.post(`/v1/billing/invoices/${invoiceId}/apply-credit/`, { amount })
};

// Enhanced Payments API (extends existing)
export const enhancedPaymentsAPI = {
  getAll: (params = {}) =>
    apiClient.get('/v1/billing/payments/', { params }),
  
  create: (data) =>
    apiClient.post('/v1/billing/payments/', data),
  
  getById: (id) =>
    apiClient.get(`/v1/billing/payments/${id}/`),
  
  update: (id, data) =>
    apiClient.put(`/v1/billing/payments/${id}/`, data),
  
  // Enhanced features
  allocateToInvoices: (paymentId, strategy = 'oldest_first') =>
    apiClient.post(`/v1/billing/payments/${paymentId}/allocate/`, {}, {
      params: { strategy }
    })
};

// Comprehensive Reports API
export const billingReportsAPI = {
  generateRevenue: (startDate, endDate, filters = {}) =>
    apiClient.post('/v1/billing/reports/revenue/', {
      start_date: startDate,
      end_date: endDate,
      ...filters
    }),
  
  generateAging: (asOfDate = null) =>
    apiClient.post('/v1/billing/reports/aging/', {
      as_of_date: asOfDate || new Date().toISOString().split('T')[0]
    }),
  
  generatePaymentAnalysis: (startDate, endDate) =>
    apiClient.post('/v1/billing/reports/payment-analysis/', {
      start_date: startDate,
      end_date: endDate
    }),
  
  generateTaxSummary: (startDate, endDate) =>
    apiClient.post('/v1/billing/reports/tax-summary/', {
      start_date: startDate,
      end_date: endDate
    }),
  
  generateUsageReport: (customerId, startDate, endDate) =>
    apiClient.get(`/v1/billing/reports/usage/${customerId}/`, {
      params: { start_date: startDate, end_date: endDate }
    })
};

// Export all APIs
export default {
  customers: customersAPI,
  billingCycles: billingCyclesAPI,
  customerBillingConfig: customerBillingConfigAPI,
  billingEngine: billingEngineAPI,
  usageTracking: usageTrackingAPI,
  billingEvents: billingEventsAPI,
  analytics: billingAnalyticsAPI,
  taxManagement: taxManagementAPI,
  customerAccount: customerAccountAPI,
  paymentGateways: paymentGatewaysAPI,
  invoices: enhancedInvoicesAPI,
  payments: enhancedPaymentsAPI,
  reports: billingReportsAPI
};