import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Endpoint for uploading the laboratory file
export const uploadFile = (formData) => api.post('/upload', formData);

// Endpoint for triggering analysis (if needed separately)
export const getAnalysis = () => api.get('/analyze');

export default api;