import apiClient from './api'; // Assuming apiClient is your configured axios instance

export const getRouters = (params) => {
  return apiClient.get('/v1/network/routers/', { params });
};

export const createRouter = (data) => {
  return apiClient.post('/v1/network/routers/', data);
};

export const updateRouter = (id, data) => {
  return apiClient.put(`/v1/network/routers/${id}/`, data);
};

export const deleteRouter = (id) => {
  return apiClient.delete(`/v1/network/routers/${id}/`);
};

// Helper functions to fetch data for form dropdowns
export const getLocations = (params) => {
  // Assuming a /locations endpoint exists
  return apiClient.get('/v1/locations/', { params });
};

export const getPartners = (params) => {
  // Assuming a /partners endpoint exists
  return apiClient.get('/v1/partners/', { params });
};