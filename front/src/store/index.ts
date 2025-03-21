import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import accountsReducer from './slices/accountsSlice';
import settingsReducer from './slices/settingsSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    accounts: accountsReducer,
    settings: settingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 