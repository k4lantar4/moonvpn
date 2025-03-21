import { apiClient } from './client';

export interface UserStats {
  total_subscriptions: number;
  active_subscriptions: number;
  total_traffic: number;
  remaining_traffic: number;
  wallet_balance: number;
  total_purchases: number;
  recent_activity: Activity[];
}

export interface Activity {
  id: number;
  type: 'subscription' | 'payment' | 'traffic' | 'system';
  description: string;
  timestamp: string;
}

export interface Subscription {
  id: number;
  plan_name: string;
  status: 'active' | 'expired' | 'cancelled';
  start_date: string;
  end_date: string;
  total_traffic: number;
  used_traffic: number;
  server_name: string;
  server_status: 'healthy' | 'unhealthy';
  config_url: string;
  qr_code: string;
}

export interface Transaction {
  id: number;
  type: 'deposit' | 'withdrawal' | 'purchase' | 'refund';
  amount: number;
  status: 'pending' | 'completed' | 'failed';
  description: string;
  timestamp: string;
}

export const userApi = {
  getStats: async (): Promise<UserStats> => {
    const response = await apiClient.get('/api/user/stats');
    return response.data;
  },

  getSubscriptions: async (): Promise<Subscription[]> => {
    const response = await apiClient.get('/api/user/subscriptions');
    return response.data;
  },

  getTransactions: async (params?: {
    page?: number;
    limit?: number;
    type?: string;
  }): Promise<{
    transactions: Transaction[];
    total: number;
  }> => {
    const response = await apiClient.get('/api/user/transactions', { params });
    return response.data;
  },

  getWalletBalance: async (): Promise<number> => {
    const response = await apiClient.get('/api/user/wallet/balance');
    return response.data.balance;
  },

  depositToWallet: async (amount: number): Promise<{
    payment_url: string;
    order_id: string;
  }> => {
    const response = await apiClient.post('/api/user/wallet/deposit', { amount });
    return response.data;
  },

  withdrawFromWallet: async (amount: number, card_number: string): Promise<void> => {
    await apiClient.post('/api/user/wallet/withdraw', { amount, card_number });
  },

  getProfile: async (): Promise<{
    username: string;
    email: string;
    phone: string;
    telegram_id: string;
    created_at: string;
  }> => {
    const response = await apiClient.get('/api/user/profile');
    return response.data;
  },

  updateProfile: async (data: {
    username?: string;
    email?: string;
    phone?: string;
  }): Promise<void> => {
    await apiClient.put('/api/user/profile', data);
  },

  getNotifications: async (params?: {
    page?: number;
    limit?: number;
    read?: boolean;
  }): Promise<{
    notifications: Notification[];
    total: number;
  }> => {
    const response = await apiClient.get('/api/user/notifications', { params });
    return response.data;
  },

  markNotificationAsRead: async (notificationId: number): Promise<void> => {
    await apiClient.put(`/api/user/notifications/${notificationId}/read`);
  },

  markAllNotificationsAsRead: async (): Promise<void> => {
    await apiClient.put('/api/user/notifications/read-all');
  },
}; 