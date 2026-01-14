import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export const getSettings = async () => {
  const response = await api.get("/settings");
  return response.data;
};

export const saveSettings = async (settings) => {
  const response = await api.post("/settings", settings);
  return response.data;
};

export const triggerSync = async () => {
  const response = await api.post("/sync");
  return response.data;
};

export const testArenaItem = async (guid) => {
    const response = await api.get(`/test/arena/item/${guid}`);
    return response.data;
};

export default api;
