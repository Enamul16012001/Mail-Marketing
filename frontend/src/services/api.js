import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stats
export const getStats = () => api.get('/stats');

// Emails
export const getPendingEmails = () => api.get('/emails/pending');
export const getEmailHistory = (limit = 50) => api.get(`/emails/history?limit=${limit}`);
export const getEmail = (id) => api.get(`/emails/${id}`);
export const replyToEmail = (id, response) => api.post(`/emails/reply/${id}`, { response });
export const dismissEmail = (id) => api.delete(`/emails/${id}`);
export const triggerProcessing = () => api.post('/emails/process');
export const composeEmail = (data) => api.post('/emails/compose', data);

// Drafts
export const getPendingDrafts = () => api.get('/drafts');
export const getDraft = (id) => api.get(`/drafts/${id}`);
export const approveDraft = (id) => api.post(`/drafts/${id}/approve`);
export const editDraft = (id, content) => api.put(`/drafts/${id}`, { content });
export const discardDraft = (id) => api.delete(`/drafts/${id}`);

// Knowledge Base
export const getKnowledgeFiles = () => api.get('/knowledge/files');
export const uploadKnowledgeFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const deleteKnowledgeFile = (id) => api.delete(`/knowledge/${id}`);
export const searchKnowledge = (query) => api.post('/knowledge/search', { query });
export const getKnowledgeStats = () => api.get('/knowledge/stats');

// Settings
export const getSettings = () => api.get('/settings');
export const updateSettings = (settings) => api.post('/settings', settings);

// Health
export const healthCheck = () => api.get('/health');

export default api;
