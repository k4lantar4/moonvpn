import { supportAPI } from './api';

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: 'open' | 'in_progress' | 'closed';
  priority: 'low' | 'medium' | 'high';
  category: string;
  created_by: {
    id: number;
    username: string;
    email: string;
  };
  assigned_to?: {
    id: number;
    username: string;
    email: string;
  };
  created_at: string;
  updated_at: string;
  last_message_at: string;
  messages: TicketMessage[];
}

export interface TicketMessage {
  id: number;
  content: string;
  created_by: {
    id: number;
    username: string;
    email: string;
  };
  created_at: string;
  attachments?: {
    id: number;
    name: string;
    url: string;
    size: number;
    type: string;
  }[];
}

export interface TicketCreateData {
  title: string;
  description: string;
  priority: Ticket['priority'];
  category: string;
}

export interface TicketMessageData {
  content: string;
  attachments?: File[];
}

class SupportService {
  async getTickets(): Promise<Ticket[]> {
    try {
      const response = await supportAPI.getTickets();
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async getTicket(id: number): Promise<Ticket> {
    try {
      const response = await supportAPI.getTicket(id);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async createTicket(data: TicketCreateData): Promise<Ticket> {
    try {
      const response = await supportAPI.createTicket(data);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async addTicketMessage(id: number, data: TicketMessageData): Promise<TicketMessage> {
    try {
      const formData = new FormData();
      formData.append('content', data.content);
      
      if (data.attachments) {
        data.attachments.forEach((file) => {
          formData.append('attachments', file);
        });
      }

      const response = await supportAPI.addTicketMessage(id, formData);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  getTicketStatusColor(status: Ticket['status']): string {
    const colors = {
      open: '#10b981',
      in_progress: '#f59e0b',
      closed: '#6b7280',
    };
    return colors[status];
  }

  getTicketStatusText(status: Ticket['status']): string {
    const texts = {
      open: 'باز',
      in_progress: 'در حال بررسی',
      closed: 'بسته شده',
    };
    return texts[status];
  }

  getPriorityColor(priority: Ticket['priority']): string {
    const colors = {
      low: '#10b981',
      medium: '#f59e0b',
      high: '#ef4444',
    };
    return colors[priority];
  }

  getPriorityText(priority: Ticket['priority']): string {
    const texts = {
      low: 'کم',
      medium: 'متوسط',
      high: 'زیاد',
    };
    return texts[priority];
  }

  formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  validateFile(file: File): boolean {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];

    return file.size <= maxSize && allowedTypes.includes(file.type);
  }

  getTicketCategories(): string[] {
    return [
      'عمومی',
      'فنی',
      'پرداخت',
      'حساب کاربری',
      'گزارش مشکل',
      'پیشنهاد',
      'سایر',
    ];
  }
}

export const supportService = new SupportService(); 