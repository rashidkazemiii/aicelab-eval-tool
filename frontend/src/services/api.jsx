import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE_URL, timeout: 30000 });

// Upload & calculate
export const uploadFile        = (formData, dataType = 'OFT') =>
  api.post(`/upload?data_type=${dataType}`, formData);
export const calculate         = () => api.post('/cof/calculate');

// CoF processing
export const getData           = () => api.get('/cof/calculated');
export const applyOffset       = () => api.post('/cof/offset');
export const getOffset         = () => api.get('/cof/offset');
export const applyFilter       = (window) => api.post(`/cof/filter?window=${window}`);
export const getFilter         = () => api.get('/cof/filter');
export const applyEvaluate     = (params) => api.post('/cof/evaluate', null, { params });

export const viewResult = () => window.open(`${API_BASE_URL}/cof/result/html`, '_blank');
export const getResult  = () => api.get('/cof/result/json');

// Displacement processing
export const getDisplacementData  = () => api.get('/displacement/data');
export const applyDispOffset      = () => api.post('/displacement/offset');
export const getDispOffset        = () => api.get('/displacement/offset');
export const applyDispFilter      = (window) => api.post(`/displacement/filter?window=${window}`);
export const getDispFilter        = () => api.get('/displacement/filter');
export const applyDispEvaluate    = () => api.post('/displacement/evaluate');

// History / database
export const getHistory      = ()             => api.get('/history');
export const getTestCycles   = (testId)       => api.get(`/history/${testId}/cycles`);
export const deleteTest      = (testId)       => api.delete(`/history/${testId}`);
export const saveResult      = (force = false) => api.post(`/history/save?force=${force}`);

export default api;
