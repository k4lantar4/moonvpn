import { authAPI } from './api';
import { store } from '../store';
import { setCredentials, logout } from '../store/slices/authSlice';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    username: string;
    email: string;
    is_staff: boolean;
  };
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await authAPI.login(credentials.username, credentials.password);
      const { access, refresh, user } = response.data;
      
      store.dispatch(setCredentials({ access, refresh, user }));
      localStorage.setItem('refreshToken', refresh);
      
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      const response = await authAPI.register(data.username, data.email, data.password);
      const { access, refresh, user } = response.data;
      
      store.dispatch(setCredentials({ access, refresh, user }));
      localStorage.setItem('refreshToken', refresh);
      
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      await authAPI.logout();
      store.dispatch(logout());
      localStorage.removeItem('refreshToken');
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  async refreshToken(): Promise<string> {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await authAPI.refreshToken(refreshToken);
      const { access } = response.data;
      
      store.dispatch(setCredentials({ access, refresh: refreshToken }));
      return access;
    } catch (error) {
      this.logout();
      throw error;
    }
  }

  isAuthenticated(): boolean {
    const state = store.getState().auth;
    return !!state.token && !!state.user;
  }

  isAdmin(): boolean {
    const state = store.getState().auth;
    return state.user?.is_staff || false;
  }
}

export const authService = new AuthService(); 