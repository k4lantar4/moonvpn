import { api } from './api';

export interface MetricData {
  timestamp: number;
  value: number;
}

export interface Metric {
  name: string;
  description: string;
  unit: string;
  data: MetricData[];
}

export interface SystemMetrics {
  cpu: Metric;
  memory: Metric;
  disk: Metric;
  network: Metric;
  response_time: Metric;
  error_rate: Metric;
}

export interface Alert {
  id: number;
  name: string;
  description: string;
  severity: string;
  status: string;
  created_at: number;
  resolved_at: number | null;
  acknowledged_at: number | null;
  acknowledged_by: number | null;
}

export interface AlertRule {
  id: number;
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  severity: string;
  enabled: boolean;
}

export interface NotificationChannel {
  id: number;
  name: string;
  type: string;
  config: Record<string, string>;
  enabled: boolean;
}

export interface MonitoringSettings {
  alertRules: AlertRule[];
  notificationChannels: NotificationChannel[];
  retentionPeriod: number;
  samplingRate: number;
  autoScaling: {
    enabled: boolean;
    minInstances: number;
    maxInstances: number;
    scaleUpThreshold: number;
    scaleDownThreshold: number;
  };
}

export const monitoringService = {
  // Metrics
  getMetrics: async (timeRange: string): Promise<SystemMetrics> => {
    const response = await api.get('/monitoring/metrics', {
      params: { timeRange }
    });
    return response.data;
  },

  // Alerts
  getAlerts: async (filters?: {
    status?: string;
    severity?: string;
    search?: string;
  }): Promise<Alert[]> => {
    const response = await api.get('/monitoring/alerts', {
      params: filters
    });
    return response.data;
  },

  updateAlertStatus: async (alertId: number, status: string): Promise<void> => {
    await api.put(`/monitoring/alerts/${alertId}/status`, { status });
  },

  // Settings
  getSettings: async (): Promise<MonitoringSettings> => {
    const response = await api.get('/monitoring/settings');
    return response.data;
  },

  updateSettings: async (settings: Partial<MonitoringSettings>): Promise<void> => {
    await api.put('/monitoring/settings', settings);
  },

  // Alert Rules
  createAlertRule: async (rule: Omit<AlertRule, 'id'>): Promise<AlertRule> => {
    const response = await api.post('/monitoring/alert-rules', rule);
    return response.data;
  },

  updateAlertRule: async (ruleId: number, rule: Partial<AlertRule>): Promise<AlertRule> => {
    const response = await api.put(`/monitoring/alert-rules/${ruleId}`, rule);
    return response.data;
  },

  deleteAlertRule: async (ruleId: number): Promise<void> => {
    await api.delete(`/monitoring/alert-rules/${ruleId}`);
  },

  // Notification Channels
  createNotificationChannel: async (
    channel: Omit<NotificationChannel, 'id'>
  ): Promise<NotificationChannel> => {
    const response = await api.post('/monitoring/notification-channels', channel);
    return response.data;
  },

  updateNotificationChannel: async (
    channelId: number,
    channel: Partial<NotificationChannel>
  ): Promise<NotificationChannel> => {
    const response = await api.put(`/monitoring/notification-channels/${channelId}`, channel);
    return response.data;
  },

  deleteNotificationChannel: async (channelId: number): Promise<void> => {
    await api.delete(`/monitoring/notification-channels/${channelId}`);
  }
}; 