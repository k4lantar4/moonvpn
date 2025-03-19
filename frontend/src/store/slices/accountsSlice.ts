import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Account {
  id: number;
  name: string;
  server: string;
  protocol: string;
  config: string;
  status: 'active' | 'expired' | 'suspended';
  expiryDate: string;
  trafficLimit: number;
  trafficUsed: number;
  createdAt: string;
  updatedAt: string;
}

interface AccountsState {
  accounts: Account[];
  loading: boolean;
  error: string | null;
  selectedAccount: Account | null;
}

const initialState: AccountsState = {
  accounts: [],
  loading: false,
  error: null,
  selectedAccount: null,
};

const accountsSlice = createSlice({
  name: 'accounts',
  initialState,
  reducers: {
    fetchAccountsStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchAccountsSuccess: (state, action: PayloadAction<Account[]>) => {
      state.loading = false;
      state.accounts = action.payload;
    },
    fetchAccountsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    addAccount: (state, action: PayloadAction<Account>) => {
      state.accounts.push(action.payload);
    },
    updateAccount: (state, action: PayloadAction<Account>) => {
      const index = state.accounts.findIndex((acc) => acc.id === action.payload.id);
      if (index !== -1) {
        state.accounts[index] = action.payload;
      }
    },
    deleteAccount: (state, action: PayloadAction<number>) => {
      state.accounts = state.accounts.filter((acc) => acc.id !== action.payload);
    },
    setSelectedAccount: (state, action: PayloadAction<Account | null>) => {
      state.selectedAccount = action.payload;
    },
    updateAccountTraffic: (state, action: PayloadAction<{ id: number; trafficUsed: number }>) => {
      const account = state.accounts.find((acc) => acc.id === action.payload.id);
      if (account) {
        account.trafficUsed = action.payload.trafficUsed;
      }
    },
  },
});

export const {
  fetchAccountsStart,
  fetchAccountsSuccess,
  fetchAccountsFailure,
  addAccount,
  updateAccount,
  deleteAccount,
  setSelectedAccount,
  updateAccountTraffic,
} = accountsSlice.actions;

export default accountsSlice.reducer; 