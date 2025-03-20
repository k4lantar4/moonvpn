import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface VpnAccount {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'expired';
  plan: string;
  expiryDate: string;
  traffic: {
    used: number;
    total: number;
  };
  server: {
    id: string;
    name: string;
    location: string;
  };
}

interface VpnState {
  accounts: VpnAccount[];
  selectedAccount: VpnAccount | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    status: string[];
    plan: string[];
    server: string[];
  };
}

const initialState: VpnState = {
  accounts: [],
  selectedAccount: null,
  isLoading: false,
  error: null,
  filters: {
    status: [],
    plan: [],
    server: [],
  },
};

const vpnSlice = createSlice({
  name: 'vpn',
  initialState,
  reducers: {
    setAccounts: (state, action: PayloadAction<VpnAccount[]>) => {
      state.accounts = action.payload;
    },
    addAccount: (state, action: PayloadAction<VpnAccount>) => {
      state.accounts.push(action.payload);
    },
    updateAccount: (state, action: PayloadAction<VpnAccount>) => {
      const index = state.accounts.findIndex(
        (account) => account.id === action.payload.id
      );
      if (index !== -1) {
        state.accounts[index] = action.payload;
      }
    },
    deleteAccount: (state, action: PayloadAction<string>) => {
      state.accounts = state.accounts.filter(
        (account) => account.id !== action.payload
      );
    },
    setSelectedAccount: (state, action: PayloadAction<VpnAccount | null>) => {
      state.selectedAccount = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setFilters: (
      state,
      action: PayloadAction<{
        status?: string[];
        plan?: string[];
        server?: string[];
      }>
    ) => {
      state.filters = {
        ...state.filters,
        ...action.payload,
      };
    },
    clearFilters: (state) => {
      state.filters = {
        status: [],
        plan: [],
        server: [],
      };
    },
  },
});

export const {
  setAccounts,
  addAccount,
  updateAccount,
  deleteAccount,
  setSelectedAccount,
  setLoading,
  setError,
  setFilters,
  clearFilters,
} = vpnSlice.actions;

export default vpnSlice.reducer; 