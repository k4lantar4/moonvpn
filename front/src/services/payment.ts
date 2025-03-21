import { paymentAPI } from './api';

export interface PaymentMethod {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
  settings: {
    [key: string]: any;
  };
}

export interface Payment {
  id: number;
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  method: string;
  transaction_id?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentCreateData {
  amount: number;
  method: string;
  description?: string;
}

export interface ZarinpalPaymentData {
  amount: number;
  description?: string;
  email?: string;
  phone?: string;
  callback_url: string;
}

class PaymentService {
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    try {
      const response = await paymentAPI.getPaymentMethods();
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async createPayment(data: PaymentCreateData): Promise<Payment> {
    try {
      const response = await paymentAPI.createPayment(data);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async getPayment(id: number): Promise<Payment> {
    try {
      const response = await paymentAPI.getPayment(id);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async verifyPayment(id: number): Promise<Payment> {
    try {
      const response = await paymentAPI.verifyPayment(id);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async initiateZarinpalPayment(data: ZarinpalPaymentData): Promise<{
    authority: string;
    payment_url: string;
  }> {
    try {
      const response = await paymentAPI.createPayment({
        amount: data.amount,
        method: 'zarinpal',
        description: data.description,
        settings: {
          email: data.email,
          phone: data.phone,
          callback_url: data.callback_url,
        },
      });

      return {
        authority: response.data.transaction_id,
        payment_url: `https://www.zarinpal.com/pg/StartPay/${response.data.transaction_id}`,
      };
    } catch (error) {
      throw error;
    }
  }

  formatAmount(amount: number, currency: string = 'IRR'): string {
    const formatter = new Intl.NumberFormat('fa-IR', {
      style: 'currency',
      currency: currency,
    });
    return formatter.format(amount);
  }

  getPaymentStatusColor(status: Payment['status']): string {
    const colors = {
      pending: '#f59e0b',
      completed: '#10b981',
      failed: '#ef4444',
      cancelled: '#6b7280',
    };
    return colors[status];
  }

  getPaymentStatusText(status: Payment['status']): string {
    const texts = {
      pending: 'در انتظار پرداخت',
      completed: 'پرداخت موفق',
      failed: 'پرداخت ناموفق',
      cancelled: 'لغو شده',
    };
    return texts[status];
  }

  validateAmount(amount: number): boolean {
    return amount > 0 && amount <= 1000000000; // Max 1 billion IRR
  }

  generatePaymentDescription(accountId: number, days: number): string {
    return `پرداخت اشتراک ${days} روزه برای اکانت ${accountId}`;
  }
}

export const paymentService = new PaymentService(); 