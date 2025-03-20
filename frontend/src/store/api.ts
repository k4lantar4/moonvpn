import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from './index';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.REACT_APP_API_URL,
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  endpoints: (builder) => ({
    // Auth endpoints
    login: builder.mutation<{ token: string }, { email: string; password: string }>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),
    register: builder.mutation<{ token: string }, { email: string; password: string; name: string }>({
      query: (userData) => ({
        url: '/auth/register',
        method: 'POST',
        body: userData,
      }),
    }),
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
    }),

    // VPN endpoints
    getVpnAccounts: builder.query<Array<{ id: string; name: string; status: string }>, void>({
      query: () => '/vpn/accounts',
    }),
    createVpnAccount: builder.mutation<{ id: string }, { name: string; plan: string }>({
      query: (accountData) => ({
        url: '/vpn/accounts',
        method: 'POST',
        body: accountData,
      }),
    }),
    deleteVpnAccount: builder.mutation<void, string>({
      query: (id) => ({
        url: `/vpn/accounts/${id}`,
        method: 'DELETE',
      }),
    }),

    // Payment endpoints
    getPayments: builder.query<Array<{ id: string; amount: number; status: string }>, void>({
      query: () => '/payments',
    }),
    createPayment: builder.mutation<{ id: string }, { amount: number; method: string }>({
      query: (paymentData) => ({
        url: '/payments',
        method: 'POST',
        body: paymentData,
      }),
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
  useGetVpnAccountsQuery,
  useCreateVpnAccountMutation,
  useDeleteVpnAccountMutation,
  useGetPaymentsQuery,
  useCreatePaymentMutation,
} = api; 