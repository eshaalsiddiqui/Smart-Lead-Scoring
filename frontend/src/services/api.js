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

  // Lead management (mock endpoints for demo)
  getLeads: (params = {}) => {
    // Mock implementation - in production, this would call your actual API
    return Promise.resolve({
      data: {
        leads: [
          {
            id: 'LEAD_001',
            company_name: 'TechCorp Inc.',
            contact_name: 'John Smith',
            email: 'john@techcorp.com',
            industry: 'Technology',
            company_size: '51-200',
            region: 'NA',
            conversion_probability: 0.89,
            revenue_impact: 45000,
            next_best_action: 'Call',
            status: 'high'
          },
          {
            id: 'LEAD_002',
            company_name: 'Finance Solutions',
            contact_name: 'Sarah Johnson',
            email: 'sarah@financesolutions.com',
            industry: 'Finance',
            company_size: '201-1000',
            region: 'EU',
            conversion_probability: 0.76,
            revenue_impact: 32000,
            next_best_action: 'Email',
            status: 'high'
          }
        ],
        total: 2,
        page: 1,
        limit: 10
      }
    });
  },

  // Analytics data
  getAnalytics: () => {
    // Mock implementation
    return Promise.resolve({
      data: {
        conversionRate: 0.234,
        totalLeads: 1247,
        totalRevenue: 2840000,
        highPriorityLeads: 89,
        industryBreakdown: [
          { industry: 'Technology', leads: 350, conversions: 108 },
          { industry: 'Finance', leads: 275, conversions: 71 },
          { industry: 'Healthcare', leads: 225, conversions: 54 },
          { industry: 'E-commerce', leads: 187, conversions: 39 },
          { industry: 'Manufacturing', leads: 150, conversions: 28 }
        ],
        monthlyTrend: [
          { month: 'Jan', leads: 120, conversions: 28 },
          { month: 'Feb', leads: 150, conversions: 35 },
          { month: 'Mar', leads: 180, conversions: 42 },
          { month: 'Apr', leads: 200, conversions: 48 },
          { month: 'May', leads: 220, conversions: 52 },
          { month: 'Jun', leads: 250, conversions: 58 }
        ]
      }
    });
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
