import axios from 'axios';
import { message } from 'antd';

const apiClient = axios.create({
  baseURL: '/api', // Use relative URL, handled by Vite proxy
});

// Request interceptor to add the auth token header to requests
apiClient.interceptors.request.use(
  (config) => {
    // Check if this is a customer portal request
    if (config.url && config.url.includes('/customer/')) {
      const token = localStorage.getItem('customer_access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } else {
      // Regular admin portal requests
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle global errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized: redirect to appropriate login
    if (error.response && error.response.status === 401) {
      // Check if this was a customer portal request
      if (error.config.url && error.config.url.includes('/customer/')) {
        localStorage.removeItem('customer_access_token');
        if (window.location.pathname !== '/customer/login') {
          message.error('Session expired. Please log in again.');
          window.location.href = '/customer/login';
        }
      } else {
        // Regular admin portal
        localStorage.removeItem('access_token');
        if (window.location.pathname !== '/login') {
          message.error('Session expired. Please log in again.');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;