import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Payment {
  id: string;
  amount: number;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  method: string;
  createdAt: string;
  description?: string;
  transactionId?: string;
}

interface PaymentState {
  payments: Payment[];
  selectedPayment: Payment | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    status: string[];
    method: string[];
    dateRange: {
      start: string | null;
      end: string | null;
    };
  };
  statistics: {
    totalAmount: number;
    completedAmount: number;
    pendingAmount: number;
    failedAmount: number;
    refundedAmount: number;
  };
}

const initialState: PaymentState = {
  payments: [],
  selectedPayment: null,
  isLoading: false,
  error: null,
  filters: {
    status: [],
    method: [],
    dateRange: {
      start: null,
      end: null,
    },
  },
  statistics: {
    totalAmount: 0,
    completedAmount: 0,
    pendingAmount: 0,
    failedAmount: 0,
    refundedAmount: 0,
  },
};

const paymentSlice = createSlice({
  name: 'payment',
  initialState,
  reducers: {
    setPayments: (state, action: PayloadAction<Payment[]>) => {
      state.payments = action.payload;
      // Update statistics
      state.statistics = action.payload.reduce(
        (acc, payment) => {
          acc.totalAmount += payment.amount;
          switch (payment.status) {
            case 'completed':
              acc.completedAmount += payment.amount;
              break;
            case 'pending':
              acc.pendingAmount += payment.amount;
              break;
            case 'failed':
              acc.failedAmount += payment.amount;
              break;
            case 'refunded':
              acc.refundedAmount += payment.amount;
              break;
          }
          return acc;
        },
        {
          totalAmount: 0,
          completedAmount: 0,
          pendingAmount: 0,
          failedAmount: 0,
          refundedAmount: 0,
        }
      );
    },
    addPayment: (state, action: PayloadAction<Payment>) => {
      state.payments.push(action.payload);
      // Update statistics
      const payment = action.payload;
      state.statistics.totalAmount += payment.amount;
      switch (payment.status) {
        case 'completed':
          state.statistics.completedAmount += payment.amount;
          break;
        case 'pending':
          state.statistics.pendingAmount += payment.amount;
          break;
        case 'failed':
          state.statistics.failedAmount += payment.amount;
          break;
        case 'refunded':
          state.statistics.refundedAmount += payment.amount;
          break;
      }
    },
    updatePayment: (state, action: PayloadAction<Payment>) => {
      const index = state.payments.findIndex(
        (payment) => payment.id === action.payload.id
      );
      if (index !== -1) {
        // Update statistics for old payment
        const oldPayment = state.payments[index];
        state.statistics.totalAmount -= oldPayment.amount;
        switch (oldPayment.status) {
          case 'completed':
            state.statistics.completedAmount -= oldPayment.amount;
            break;
          case 'pending':
            state.statistics.pendingAmount -= oldPayment.amount;
            break;
          case 'failed':
            state.statistics.failedAmount -= oldPayment.amount;
            break;
          case 'refunded':
            state.statistics.refundedAmount -= oldPayment.amount;
            break;
        }
        // Update payment
        state.payments[index] = action.payload;
        // Update statistics for new payment
        const newPayment = action.payload;
        state.statistics.totalAmount += newPayment.amount;
        switch (newPayment.status) {
          case 'completed':
            state.statistics.completedAmount += newPayment.amount;
            break;
          case 'pending':
            state.statistics.pendingAmount += newPayment.amount;
            break;
          case 'failed':
            state.statistics.failedAmount += newPayment.amount;
            break;
          case 'refunded':
            state.statistics.refundedAmount += newPayment.amount;
            break;
        }
      }
    },
    deletePayment: (state, action: PayloadAction<string>) => {
      const payment = state.payments.find((p) => p.id === action.payload);
      if (payment) {
        state.payments = state.payments.filter((p) => p.id !== action.payload);
        // Update statistics
        state.statistics.totalAmount -= payment.amount;
        switch (payment.status) {
          case 'completed':
            state.statistics.completedAmount -= payment.amount;
            break;
          case 'pending':
            state.statistics.pendingAmount -= payment.amount;
            break;
          case 'failed':
            state.statistics.failedAmount -= payment.amount;
            break;
          case 'refunded':
            state.statistics.refundedAmount -= payment.amount;
            break;
        }
      }
    },
    setSelectedPayment: (state, action: PayloadAction<Payment | null>) => {
      state.selectedPayment = action.payload;
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
        method?: string[];
        dateRange?: {
          start: string | null;
          end: string | null;
        };
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
        method: [],
        dateRange: {
          start: null,
          end: null,
        },
      };
    },
  },
});

export const {
  setPayments,
  addPayment,
  updatePayment,
  deletePayment,
  setSelectedPayment,
  setLoading,
  setError,
  setFilters,
  clearFilters,
} = paymentSlice.actions;

export default paymentSlice.reducer; 