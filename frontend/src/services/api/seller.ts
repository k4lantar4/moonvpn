import { apiClient } from './client';

export interface SellerStats {
  total_sales: number;
  total_commission: number;
  active_customers: number;
  total_customers: number;
  recent_sales: Sale[];
  commission_history: CommissionHistory[];
}

export interface Sale {
  id: number;
  customer: string;
  plan: string;
  amount: number;
  commission: number;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
}

export interface CommissionHistory {
  id: number;
  amount: number;
  status: 'pending' | 'paid' | 'cancelled';
  created_at: string;
  paid_at?: string;
}

export interface WithdrawalRequest {
  id: number;
  amount: number;
  status: 'pending' | 'approved' | 'rejected' | 'paid';
  created_at: string;
  processed_at?: string;
}

export const sellerApi = {
  getStats: async (): Promise<SellerStats> => {
    const response = await apiClient.get('/api/seller/stats');
    return response.data;
  },

  getSales: async (params?: {
    page?: number;
    limit?: number;
    status?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{
    sales: Sale[];
    total: number;
  }> => {
    const response = await apiClient.get('/api/seller/sales', { params });
    return response.data;
  },

  getCommissionHistory: async (params?: {
    page?: number;
    limit?: number;
    status?: string;
  }): Promise<{
    commissions: CommissionHistory[];
    total: number;
  }> => {
    const response = await apiClient.get('/api/seller/commissions', { params });
    return response.data;
  },

  getWithdrawalRequests: async (params?: {
    page?: number;
    limit?: number;
    status?: string;
  }): Promise<{
    withdrawals: WithdrawalRequest[];
    total: number;
  }> => {
    const response = await apiClient.get('/api/seller/withdrawals', { params });
    return response.data;
  },

  requestWithdrawal: async (amount: number, card_number: string): Promise<void> => {
    await apiClient.post('/api/seller/withdrawals', { amount, card_number });
  },

  getProfile: async (): Promise<{
    username: string;
    email: string;
    phone: string;
    telegram_id: string;
    commission_rate: number;
    total_earned: number;
    available_balance: number;
    created_at: string;
  }> => {
    const response = await apiClient.get('/api/seller/profile');
    return response.data;
  },

  updateProfile: async (data: {
    username?: string;
    email?: string;
    phone?: string;
    telegram_id?: string;
  }): Promise<void> => {
    await apiClient.put('/api/seller/profile', data);
  },

  getNotifications: async (params?: {
    page?: number;
    limit?: number;
    read?: boolean;
  }): Promise<{
    notifications: Notification[];
    total: number;
  }> => {
    const response = await apiClient.get('/api/seller/notifications', { params });
    return response.data;
  },

  markNotificationAsRead: async (notificationId: number): Promise<void> => {
    await apiClient.put(`/api/seller/notifications/${notificationId}/read`);
  },

  markAllNotificationsAsRead: async (): Promise<void> => {
    await apiClient.put('/api/seller/notifications/read-all');
  },
}; 