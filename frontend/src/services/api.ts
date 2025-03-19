import axios from 'axios';
import { store } from '../store';
import { logout } from '../store/slices/authSlice';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = store.getState().auth.token;
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
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      store.dispatch(logout());
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login/', { username, password }),
  register: (username: string, email: string, password: string) =>
    api.post('/auth/register/', { username, email, password }),
  logout: () => api.post('/auth/logout/'),
  refreshToken: (refresh: string) =>
    api.post('/auth/token/refresh/', { refresh }),
};

// Account endpoints
export const accountAPI = {
  getAccounts: () => api.get('/accounts/'),
  getAccount: (id: number) => api.get(`/accounts/${id}/`),
  createAccount: (data: any) => api.post('/accounts/', data),
  updateAccount: (id: number, data: any) =>
    api.put(`/accounts/${id}/`, data),
  deleteAccount: (id: number) => api.delete(`/accounts/${id}/`),
  renewAccount: (id: number) => api.post(`/accounts/${id}/renew/`),
  getAccountTraffic: (id: number) =>
    api.get(`/accounts/${id}/traffic/`),
};

// Settings endpoints
export const settingsAPI = {
  getSettings: () => api.get('/settings/'),
  updateSettings: (data: any) => api.put('/settings/', data),
};

// Support endpoints
export const supportAPI = {
  getTickets: () => api.get('/tickets/'),
  getTicket: (id: number) => api.get(`/tickets/${id}/`),
  createTicket: (data: any) => api.post('/tickets/', data),
  addTicketMessage: (id: number, data: any) =>
    api.post(`/tickets/${id}/messages/`, data),
};

// Payment endpoints
export const paymentAPI = {
  createPayment: (data: any) => api.post('/payments/', data),
  getPayment: (id: number) => api.get(`/payments/${id}/`),
  verifyPayment: (id: number) => api.post(`/payments/${id}/verify/`),
  getPaymentMethods: () => api.get('/payments/methods/'),
};

export default api; 