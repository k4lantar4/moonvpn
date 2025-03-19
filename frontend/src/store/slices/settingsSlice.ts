import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Settings {
  language: string;
  theme: 'light' | 'dark';
  notifications: boolean;
  autoRenew: boolean;
  showTraffic: boolean;
  showExpiry: boolean;
}

interface SettingsState {
  settings: Settings;
  loading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  settings: {
    language: 'fa',
    theme: 'dark',
    notifications: true,
    autoRenew: false,
    showTraffic: true,
    showExpiry: true,
  },
  loading: false,
  error: null,
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    fetchSettingsStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchSettingsSuccess: (state, action: PayloadAction<Settings>) => {
      state.loading = false;
      state.settings = action.payload;
    },
    fetchSettingsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    updateSetting: (state, action: PayloadAction<{ key: keyof Settings; value: any }>) => {
      const { key, value } = action.payload;
      state.settings[key] = value;
    },
    updateSettings: (state, action: PayloadAction<Partial<Settings>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    resetSettings: (state) => {
      state.settings = initialState.settings;
    },
  },
});

export const {
  fetchSettingsStart,
  fetchSettingsSuccess,
  fetchSettingsFailure,
  updateSetting,
  updateSettings,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer; 