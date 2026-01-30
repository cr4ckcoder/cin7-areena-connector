import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - add JWT token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - logout user
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const getSettings = async () => {
  const response = await api.get("/settings");
  return response.data;
};

export const saveSettings = async (settings) => {
  const response = await api.post("/settings", settings);
  return response.data;
};

export const getStats = async () => {
  const response = await api.get("/stats");
  return response.data;
};

export const triggerSync = async (dryRun = false) => {
  const response = await api.post(`/sync/cin7?dry_run=${dryRun}`);
  return response.data;
};

export const testArenaItem = async (guid) => {
    const response = await api.get(`/test/arena/item/${guid}`);
    return response.data;
};
export const syncOnDemand = async (itemNumber, dryRun = true) => {
    const response = await api.post(`/sync/on-demand?item_number=${itemNumber}&dry_run=${dryRun}`);
    return response.data;
};

// Add these to your existing api.js
export const getSyncRules = async () => {
    const response = await api.get('/rules');
    return response.data;
};

export const updateSyncRule = async (id, ruleData) => {
    const response = await api.put(`/rules/${id}`, ruleData);
    return response.data;
};

export const updateConfig = async (configData) => {
    const response = await api.put('/config', configData);
    return response.data;
};

export const createSyncRule = async (ruleData) => {
    const response = await api.post('/rules', ruleData);
    return response.data;
};

export const getLogs = async () => {
    const response = await api.get('/admin/logs');
    return response.data;
};

export default api;
