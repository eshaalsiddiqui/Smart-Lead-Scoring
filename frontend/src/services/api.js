import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health check
  getHealth: () => api.get('/health'),

  // Model info
  getModelInfo: () => api.get('/model/info'),

  // Single lead prediction
  predictSingleLead: (leadData) => api.post('/predict/single', leadData),

  // Batch lead prediction
  predictBatchLeads: (leadsData) => api.post('/predict/batch', leadsData),

  // Top leads
  getTopLeads: (params = {}) => {
    const queryParams = new URLSearchParams(params);
    return api.get(`/predict/top-leads?${queryParams}`);
  },

  // Lead management
  getLeads: (params = {}) => {
    return api.get('/leads', { params });
  },

  // Analytics data
  getAnalytics: () => {
    return api.get('/analytics/summary');
  },

  // AI Assistant
  sendChatMessage: (message) => {
    return api.post('/chatbot/query', { message });
  },

  // Lead actions
  updateLeadStatus: (leadId, status) => {
    // Mock implementation
    return Promise.resolve({
      data: { success: true, leadId, status }
    });
  },

  addLeadNote: (leadId, note) => {
    // Mock implementation
    return Promise.resolve({
      data: { success: true, leadId, note }
    });
  },

  // Export functionality
  exportLeads: (format = 'csv', filters = {}) => {
    // Mock implementation
    return Promise.resolve({
      data: { downloadUrl: '/api/export/leads.csv' }
    });
  }
};

export default api;
