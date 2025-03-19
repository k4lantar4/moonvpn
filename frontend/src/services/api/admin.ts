import { apiClient } from './client';

export interface AdminStats {
  total_users: number;
  active_servers: number;
  total_sales: number;
  monthly_growth: number;
  servers: ServerStatus[];
  recent_activity: Activity[];
}

export interface ServerStatus {
  id: number;
  name: string;
  status: 'healthy' | 'unhealthy';
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  uptime: number;
  active_connections: number;
}

export interface Activity {
  id: number;
  type: 'info' | 'warning' | 'error';
  description: string;
  timestamp: string;
}

interface SystemSettings {
  site_name: string;
  site_description: string;
  maintenance_mode: boolean;
  session_timeout: number;
  max_login_attempts: number;
  enable_2fa: boolean;
  enable_email_notifications: boolean;
  enable_telegram_notifications: boolean;
  telegram_bot_token: string;
  zarinpal_merchant_id: string;
  min_withdrawal_amount: number;
  enable_card_payment: boolean;
  default_language: string;
  enable_rtl: boolean;
}

export const adminApi = {
  getStats: async (): Promise<AdminStats> => {
    const response = await apiClient.get('/api/admin/stats');
    return response.data;
  },

  getUsers: async (params?: {
    page?: number;
    limit?: number;
    search?: string;
    role?: string;
  }) => {
    const response = await apiClient.get('/api/admin/users', { params });
    return response.data;
  },

  getUserDetails: async (userId: number) => {
    const response = await apiClient.get(`/api/admin/users/${userId}`);
    return response.data;
  },

  updateUser: async (userId: number, data: any) => {
    const response = await apiClient.put(`/api/admin/users/${userId}`, data);
    return response.data;
  },

  getServers: async () => {
    const response = await apiClient.get('/api/admin/servers');
    return response.data;
  },

  getServerDetails: async (serverId: number) => {
    const response = await apiClient.get(`/api/admin/servers/${serverId}`);
    return response.data;
  },

  updateServer: async (serverId: number, data: any) => {
    const response = await apiClient.put(`/api/admin/servers/${serverId}`, data);
    return response.data;
  },

  getSales: async (params?: {
    start_date?: string;
    end_date?: string;
    seller_id?: number;
  }) => {
    const response = await apiClient.get('/api/admin/sales', { params });
    return response.data;
  },

  getCommissions: async (params?: {
    start_date?: string;
    end_date?: string;
    seller_id?: number;
  }) => {
    const response = await apiClient.get('/api/admin/commissions', { params });
    return response.data;
  },

  getSystemLogs: async (params?: {
    level?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const response = await apiClient.get('/api/admin/logs', { params });
    return response.data;
  },

  sendBulkMessage: async (data: {
    message: string;
    user_ids?: number[];
    role?: string;
  }) => {
    const response = await apiClient.post('/api/admin/bulk-message', data);
    return response.data;
  },

  getBackupStatus: async () => {
    const response = await apiClient.get('/api/admin/backup-status');
    return response.data;
  },

  createBackup: async () => {
    const response = await apiClient.post('/api/admin/backup');
    return response.data;
  },

  restoreBackup: async (backupId: number) => {
    const response = await apiClient.post(`/api/admin/backup/${backupId}/restore`);
    return response.data;
  },

  getSettings: async (): Promise<SystemSettings> => {
    const response = await apiClient.get('/api/admin/settings');
    return response.data;
  },

  updateSettings: async (data: SystemSettings): Promise<SystemSettings> => {
    const response = await apiClient.put('/api/admin/settings', data);
    return response.data;
  },
}; 