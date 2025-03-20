import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../store';
import { login, logout, setUser } from '../store/slices/authSlice';
import { useApiRequest } from './useApiRequest';
import { useLocalStorage } from './useLocalStorage';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  createdAt: string;
  lastLogin?: string;
}

interface LoginCredentials {
  email: string;
  password: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
  error: Error | null;
}

export const useAuth = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { execute } = useApiRequest();
  const { value: token, setValue: setToken, removeValue: removeToken } = useLocalStorage<string>('auth_token', '');

  const { isAuthenticated, user, isLoading, error } = useSelector(
    (state: RootState) => state.auth
  );

  const handleLogin = useCallback(
    async (credentials: LoginCredentials) => {
      try {
        const result = await execute(
          async () => {
            const response = await fetch('/api/auth/login', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(credentials),
            });

            if (!response.ok) {
              throw new Error('Login failed');
            }

            const data = await response.json();
            return data;
          },
          {
            onSuccess: (data) => {
              const { token, user } = data;
              setToken(token);
              dispatch(login({ token, user }));
              navigate('/dashboard');
            },
          }
        );

        return result;
      } catch (error) {
        console.error('Login error:', error);
        throw error;
      }
    },
    [execute, dispatch, navigate, setToken]
  );

  const handleLogout = useCallback(async () => {
    try {
      await execute(
        async () => {
          const response = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Logout failed');
          }

          return response.json();
        },
        {
          onSuccess: () => {
            removeToken();
            dispatch(logout());
            navigate('/login');
          },
        }
      );
    } catch (error) {
      console.error('Logout error:', error);
      // Still logout locally even if server request fails
      removeToken();
      dispatch(logout());
      navigate('/login');
    }
  }, [execute, dispatch, navigate, token, removeToken]);

  const checkAuth = useCallback(async () => {
    if (!token) {
      dispatch(logout());
      return;
    }

    try {
      const result = await execute(
        async () => {
          const response = await fetch('/api/auth/me', {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Authentication check failed');
          }

          return response.json();
        },
        {
          onSuccess: (data) => {
            dispatch(setUser(data));
          },
          onError: () => {
            removeToken();
            dispatch(logout());
            navigate('/login');
          },
        }
      );

      return result;
    } catch (error) {
      console.error('Auth check error:', error);
      removeToken();
      dispatch(logout());
      navigate('/login');
    }
  }, [execute, dispatch, navigate, token, removeToken]);

  const updateProfile = useCallback(
    async (userData: Partial<User>) => {
      try {
        const result = await execute(
          async () => {
            const response = await fetch('/api/auth/profile', {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify(userData),
            });

            if (!response.ok) {
              throw new Error('Profile update failed');
            }

            return response.json();
          },
          {
            onSuccess: (data) => {
              dispatch(setUser(data));
            },
          }
        );

        return result;
      } catch (error) {
        console.error('Profile update error:', error);
        throw error;
      }
    },
    [execute, dispatch, token]
  );

  return {
    isAuthenticated,
    user,
    isLoading,
    error,
    login: handleLogin,
    logout: handleLogout,
    checkAuth,
    updateProfile,
  };
}; 