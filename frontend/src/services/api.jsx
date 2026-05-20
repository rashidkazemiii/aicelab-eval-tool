import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE_URL });

// Upload & calculate
export const uploadFile        = (formData, dataType = 'OFT') =>
  api.post(`/upload?data_type=${dataType}`, formData);
export const calculate         = () => api.post('/calculate');

// CoF processing
export const getData           = () => api.get('/data');
export const applyOffset       = () => api.post('/offset');
export const applyFilter       = (window) => api.post(`/filter?window=${window}`);
export const applyEvaluate     = (params) => api.post('/evaluate', null, { params });

export const viewResult = () => window.open(`${API_BASE_URL}/result/html`, '_blank');
export const getResult  = () => api.get('/result/json');

// Displacement processing
export const getDisplacementData  = () => api.get('/displacement/data');
export const applyDispOffset      = () => api.post('/displacement/offset');
export const applyDispFilter      = (window) => api.post(`/displacement/filter?window=${window}`);
export const applyDispEvaluate    = () => api.post('/displacement/evaluate');

export default api;
