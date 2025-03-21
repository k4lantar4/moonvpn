import { settingsAPI } from './api';

export interface AppSettings {
  id: number;
  theme: 'light' | 'dark' | 'system';
  language: 'fa' | 'en';
  notifications: {
    email: boolean;
    telegram: boolean;
    sms: boolean;
  };
  security: {
    two_factor: boolean;
    login_notifications: boolean;
  };
  display: {
    currency: string;
    date_format: string;
    time_format: string;
  };
  telegram: {
    bot_token?: string;
    chat_id?: string;
    notifications_enabled: boolean;
  };
  sms: {
    provider?: string;
    api_key?: string;
    template?: string;
    notifications_enabled: boolean;
  };
  created_at: string;
  updated_at: string;
}

export interface SettingsUpdateData {
  theme?: AppSettings['theme'];
  language?: AppSettings['language'];
  notifications?: Partial<AppSettings['notifications']>;
  security?: Partial<AppSettings['security']>;
  display?: Partial<AppSettings['display']>;
  telegram?: Partial<AppSettings['telegram']>;
  sms?: Partial<AppSettings['sms']>;
}

class SettingsService {
  async getSettings(): Promise<AppSettings> {
    try {
      const response = await settingsAPI.getSettings();
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async updateSettings(data: SettingsUpdateData): Promise<AppSettings> {
    try {
      const response = await settingsAPI.updateSettings(data);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  getDefaultSettings(): AppSettings {
    return {
      id: 1,
      theme: 'system',
      language: 'fa',
      notifications: {
        email: true,
        telegram: true,
        sms: false,
      },
      security: {
        two_factor: false,
        login_notifications: true,
      },
      display: {
        currency: 'IRR',
        date_format: 'YYYY/MM/DD',
        time_format: 'HH:mm',
      },
      telegram: {
        notifications_enabled: true,
      },
      sms: {
        notifications_enabled: false,
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }

  getThemeColor(theme: AppSettings['theme']): string {
    const colors = {
      light: '#ffffff',
      dark: '#1a1a1a',
      system: 'transparent',
    };
    return colors[theme];
  }

  getLanguageName(code: AppSettings['language']): string {
    const names = {
      fa: 'فارسی',
      en: 'English',
    };
    return names[code];
  }

  formatDate(date: string | Date, format: string = 'YYYY/MM/DD'): string {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');

    return format
      .replace('YYYY', String(year))
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes);
  }

  validateTelegramSettings(settings: AppSettings['telegram']): boolean {
    if (!settings.notifications_enabled) return true;
    return !!settings.bot_token && !!settings.chat_id;
  }

  validateSMSSettings(settings: AppSettings['sms']): boolean {
    if (!settings.notifications_enabled) return true;
    return !!settings.provider && !!settings.api_key && !!settings.template;
  }

  getSupportedLanguages(): { code: AppSettings['language']; name: string }[] {
    return [
      { code: 'fa', name: 'فارسی' },
      { code: 'en', name: 'English' },
    ];
  }

  getSupportedThemes(): { value: AppSettings['theme']; label: string }[] {
    return [
      { value: 'light', label: 'روشن' },
      { value: 'dark', label: 'تاریک' },
      { value: 'system', label: 'سیستم' },
    ];
  }

  getSupportedCurrencies(): { code: string; name: string }[] {
    return [
      { code: 'IRR', name: 'ریال' },
      { code: 'USD', name: 'دلار' },
      { code: 'EUR', name: 'یورو' },
    ];
  }

  getSupportedDateFormats(): string[] {
    return [
      'YYYY/MM/DD',
      'DD/MM/YYYY',
      'MM/DD/YYYY',
      'YYYY-MM-DD',
      'DD-MM-YYYY',
      'MM-DD-YYYY',
    ];
  }

  getSupportedTimeFormats(): string[] {
    return ['HH:mm', 'hh:mm A'];
  }
}

export const settingsService = new SettingsService(); 