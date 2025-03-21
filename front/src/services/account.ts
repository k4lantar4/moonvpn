import { accountAPI } from './api';

export interface Account {
  id: number;
  name: string;
  email: string;
  password: string;
  port: number;
  protocol: string;
  settings: {
    network: string;
    security: string;
    [key: string]: any;
  };
  traffic: {
    upload: number;
    download: number;
    total: number;
  };
  expiry_date: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountCreateData {
  name: string;
  email: string;
  password: string;
  protocol: string;
  settings: {
    network: string;
    security: string;
    [key: string]: any;
  };
  expiry_date: string;
}

export interface AccountUpdateData {
  name?: string;
  email?: string;
  password?: string;
  settings?: {
    network?: string;
    security?: string;
    [key: string]: any;
  };
  expiry_date?: string;
  is_active?: boolean;
}

export interface AccountTraffic {
  upload: number;
  download: number;
  total: number;
  last_update: string;
}

class AccountService {
  async getAccounts(): Promise<Account[]> {
    try {
      const response = await accountAPI.getAccounts();
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async getAccount(id: number): Promise<Account> {
    try {
      const response = await accountAPI.getAccount(id);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async createAccount(data: AccountCreateData): Promise<Account> {
    try {
      const response = await accountAPI.createAccount(data);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async updateAccount(id: number, data: AccountUpdateData): Promise<Account> {
    try {
      const response = await accountAPI.updateAccount(id, data);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async deleteAccount(id: number): Promise<void> {
    try {
      await accountAPI.deleteAccount(id);
    } catch (error) {
      throw error;
    }
  }

  async renewAccount(id: number): Promise<Account> {
    try {
      const response = await accountAPI.renewAccount(id);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async getAccountTraffic(id: number): Promise<AccountTraffic> {
    try {
      const response = await accountAPI.getAccountTraffic(id);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  formatTraffic(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  getAccountStatus(account: Account): 'active' | 'expired' | 'suspended' {
    if (!account.is_active) return 'suspended';
    if (new Date(account.expiry_date) < new Date()) return 'expired';
    return 'active';
  }

  getDaysUntilExpiry(account: Account): number {
    const expiryDate = new Date(account.expiry_date);
    const now = new Date();
    const diffTime = expiryDate.getTime() - now.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }
}

export const accountService = new AccountService(); 