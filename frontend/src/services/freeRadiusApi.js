import apiClient from './api'; // Assuming you have a configured axios instance

// User Management
export const getRadiusUser = (username) => apiClient.get(`/v1/freeradius/users/${username}`);

export const createOrUpdateRadiusUser = (userData) => apiClient.post('/v1/freeradius/users/', userData);

export const deleteRadiusUser = (username) => apiClient.delete(`/v1/freeradius/users/${username}`);

// Log Viewing
export const getOnlineUsers = (params) => apiClient.get('/v1/freeradius/logs/online/', { params });

export const getOnlineUsersDetailed = (params) => apiClient.get('/v1/freeradius/sessions/online/detailed/', { params });

export const getSessionStats = () => apiClient.get('/v1/freeradius/sessions/stats');

export const getSessionHistoryChart = (params) => apiClient.get('/v1/freeradius/sessions/history-chart', { params });

export const getAccountingLogs = (params) => apiClient.get('/v1/freeradius/logs/accounting/', { params });

export const getPostAuthLogs = (params) => apiClient.get('/v1/freeradius/logs/postauth/', { params });

// NAS Management
export const getNasDevices = (params) => apiClient.get('/v1/freeradius/nas/', { params });

export const createNasDevice = (nasData) => apiClient.post('/v1/freeradius/nas/', nasData);

export const updateNasDevice = (id, nasData) => apiClient.put(`/v1/freeradius/nas/${id}`, nasData);

export const deleteNasDevice = (id) => apiClient.delete(`/v1/freeradius/nas/${id}`);