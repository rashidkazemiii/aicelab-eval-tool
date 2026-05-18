import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const uploadFile = (formData) => api.post('/upload', formData);
export const calculate = () => api.post('/calculate');
export const getData = () => api.get('/data');
export const applyOffset = () => api.post('/offset');
export const applyFilter = (window) => api.post(`/filter?window=${window}`);

export default api;
