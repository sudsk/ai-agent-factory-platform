import axios from 'axios';

// Base URL - should be configured via environment variables
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor for auth tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Agent Registry APIs
export const getAgents = async (filters = {}) => {
  try {
    const response = await api.get('/agents', { params: filters });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch agents:', error);
    throw error;
  }
};

export const getAgent = async (agentName) => {
  try {
    const response = await api.get(`/agents/${agentName}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch agent ${agentName}:`, error);
    throw error;
  }
};

export const registerAgent = async (agentConfig) => {
  try {
    const response = await api.post('/agents', agentConfig);
    return response.data;
  } catch (error) {
    console.error('Failed to register agent:', error);
    throw error;
  }
};

export const updateAgent = async (agentName, updates) => {
  try {
    const response = await api.put(`/agents/${agentName}`, updates);
    return response.data;
  } catch (error) {
    console.error(`Failed to update agent ${agentName}:`, error);
    throw error;
  }
};

export const deactivateAgent = async (agentName) => {
  try {
    const response = await api.delete(`/agents/${agentName}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to deactivate agent ${agentName}:`, error);
    throw error;
  }
};

export const invokeAgent = async (agentName, inputData) => {
  try {
    const response = await api.post(`/agents/${agentName}/invoke`, inputData);
    return response.data;
  } catch (error) {
    console.error(`Failed to invoke agent ${agentName}:`, error);
    throw error;
  }
};

// Intake System APIs
export const submitIntakeRequest = async (requestData) => {
  try {
    const response = await api.post('/agents/intake-processor/invoke', requestData);
    return response.data;
  } catch (error) {
    console.error('Failed to submit intake request:', error);
    throw error;
  }
};

export const getIntakeRequests = async (filters = {}) => {
  try {
    // This would fetch from a requests collection in Firestore
    // For now, return mock data
    return {
      requests: [
        {
          id: '1',
          business_unit: 'Sales',
          agent_category: 'customer-ops',
          problem_statement: 'Need to automate lead qualification',
          status: 'pending',
          priority_score: 85,
          created_at: '2025-01-27T10:00:00Z',
        },
        {
          id: '2',
          business_unit: 'Finance',
          agent_category: 'financial',
          problem_statement: 'Automate expense report processing',
          status: 'approved',
          priority_score: 92,
          created_at: '2025-01-26T14:30:00Z',
        },
      ],
    };
  } catch (error) {
    console.error('Failed to fetch intake requests:', error);
    throw error;
  }
};

// Monitoring APIs
export const getMetrics = async (agentName = null, timeRange = '24h') => {
  try {
    // This would query Cloud Monitoring
    // For now, return mock data
    return {
      total_invocations: 12547,
      avg_latency: 245,
      success_rate: 98.5,
      error_rate: 1.5,
      cost: 127.45,
    };
  } catch (error) {
    console.error('Failed to fetch metrics:', error);
    throw error;
  }
};

export const getAgentHealth = async (agentName) => {
  try {
    const response = await api.get(`/agents/${agentName}/health`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch health for ${agentName}:`, error);
    throw error;
  }
};

export const getAgentLogs = async (agentName, limit = 100) => {
  try {
    // This would query Cloud Logging
    // For now, return mock data
    return {
      logs: [
        {
          timestamp: '2025-01-28T10:30:00Z',
          level: 'INFO',
          message: 'Agent invoked successfully',
          duration: 234,
        },
        {
          timestamp: '2025-01-28T10:29:45Z',
          level: 'INFO',
          message: 'Processing request',
          duration: 189,
        },
      ],
    };
  } catch (error) {
    console.error(`Failed to fetch logs for ${agentName}:`, error);
    throw error;
  }
};

// Prioritization APIs
export const scoreRequest = async (requestData) => {
  try {
    const response = await api.post('/agents/prioritization-scorer/invoke', requestData);
    return response.data;
  } catch (error) {
    console.error('Failed to score request:', error);
    throw error;
  }
};

// Matchmaking APIs
export const searchSimilarAgents = async (description, category = null) => {
  try {
    const response = await api.post('/agents/matchmaking-search/invoke', {
      description,
      category,
    });
    return response.data;
  } catch (error) {
    console.error('Failed to search similar agents:', error);
    throw error;
  }
};

// Requirements Refinement APIs
export const refineRequirements = async (requestData) => {
  try {
    const response = await api.post('/agents/requirements-refiner/invoke', requestData);
    return response.data;
  } catch (error) {
    console.error('Failed to refine requirements:', error);
    throw error;
  }
};

export default api;
