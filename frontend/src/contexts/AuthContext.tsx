import React, { createContext, useState, useContext, useEffect } from 'react';

// Define user roles
export enum UserRole {
  USER = 'user',
  RESELLER = 'reseller',
  ADMIN = 'admin',
}

// Define user interface
export interface User {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
  lastLogin: string;
  avatar?: string;
}

// Define auth state interface
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  error: string | null;
}

// Define auth context interface
interface AuthContextType extends AuthState {
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  verifyCode: (email: string, code: string) => Promise<boolean>;
  updateUser: (userData: Partial<User>) => void;
  hasPermission: (requiredRoles: UserRole[]) => boolean;
  clearError: () => void;
}

// Create context with default values
const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  accessToken: null,
  isLoading: false,
  error: null,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  forgotPassword: async () => {},
  resetPassword: async () => {},
  verifyCode: async () => false,
  updateUser: () => {},
  hasPermission: () => false,
  clearError: () => {},
});

// Sample mock data for development
const mockUser: User = {
  id: '1',
  email: 'test@example.com',
  fullName: 'کاربر تست',
  role: UserRole.ADMIN,
  isActive: true,
  createdAt: new Date().toISOString(),
  lastLogin: new Date().toISOString(),
  avatar: 'https://mui.com/static/images/avatar/1.jpg',
};

// Auth provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Initialize state
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    accessToken: null,
    isLoading: true,  // Start with loading true to check local storage
    error: null,
  });

  // Effect to check for saved auth state on component mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const savedToken = localStorage.getItem('accessToken');
        const savedUser = localStorage.getItem('user');
        
        if (savedToken && savedUser) {
          // In a real app, we would validate the token with the server
          setState({
            isAuthenticated: true,
            user: JSON.parse(savedUser),
            accessToken: savedToken,
            isLoading: false,
            error: null,
          });
        } else {
          setState(prev => ({ ...prev, isLoading: false }));
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'خطا در بارگذاری اطلاعات کاربری',
        }));
      }
    };

    initAuth();
  }, []);

  // Login function
  const login = async (email: string, password: string, rememberMe = false) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      // In a real app, this would be an API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // For demo, only allow login with the mock credentials
      if (email === 'test@example.com' && password === 'password123') {
        const token = 'mock-jwt-token-' + Date.now();
        
        setState({
          isAuthenticated: true,
          user: mockUser,
          accessToken: token,
          isLoading: false,
          error: null,
        });
        
        // Save to localStorage if rememberMe is true
        if (rememberMe) {
          localStorage.setItem('accessToken', token);
          localStorage.setItem('user', JSON.stringify(mockUser));
        }
      } else {
        throw new Error('ایمیل یا رمز عبور اشتباه است');
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'خطا در ورود به سیستم',
      }));
    }
  };

  // Register function
  const register = async (userData: any) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      // In a real app, this would be an API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // For demo purposes, always succeed
      console.log('Register with:', userData);
      
      setState(prev => ({ ...prev, isLoading: false }));
      
      // In a real app, we might log in the user automatically after registration
      // or redirect to a verification page
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'خطا در ثبت نام',
      }));
    }
  };

  // Logout function
  const logout = () => {
    // Clear local storage
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    
    // Reset state
    setState({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      isLoading: false,
      error: null,
    });
  };

  // Forgot password function
  const forgotPassword = async (email: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      // In a real app, this would be an API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('Password reset requested for:', email);
      
      setState(prev => ({ ...prev, isLoading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'خطا در ارسال درخواست بازیابی رمز عبور',
      }));
    }
  };

  // Reset password function
  const resetPassword = async (token: string, newPassword: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      // In a real app, this would be an API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('Password reset with token:', token, 'and new password');
      
      setState(prev => ({ ...prev, isLoading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'خطا در بازنشانی رمز عبور',
      }));
    }
  };

  // Verify code function (for 2-factor, email verification, etc.)
  const verifyCode = async (email: string, code: string): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      // In a real app, this would be an API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('Verify code for:', email, 'Code:', code);
      
      // For demo purposes, accept code '123456'
      const isValid = code === '123456';
      
      setState(prev => ({ ...prev, isLoading: false }));
      
      return isValid;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'خطا در تأیید کد',
      }));
      
      return false;
    }
  };

  // Update user information
  const updateUser = (userData: Partial<User>) => {
    if (!state.user) return;
    
    const updatedUser = { ...state.user, ...userData };
    
    setState(prev => ({
      ...prev,
      user: updatedUser,
    }));
    
    // Update localStorage if user is remembered
    if (localStorage.getItem('accessToken')) {
      localStorage.setItem('user', JSON.stringify(updatedUser));
    }
  };

  // Check if user has required permissions
  const hasPermission = (requiredRoles: UserRole[]): boolean => {
    if (!state.isAuthenticated || !state.user) {
      return false;
    }
    
    // If no specific roles required, just being authenticated is enough
    if (!requiredRoles.length) {
      return true;
    }
    
    // Check if user's role is in the required roles
    return requiredRoles.includes(state.user.role);
  };

  // Clear error state
  const clearError = () => {
    setState(prev => ({ ...prev, error: null }));
  };

  // Provide auth context
  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        forgotPassword,
        resetPassword,
        verifyCode,
        updateUser,
        hasPermission,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => useContext(AuthContext);

export default AuthContext; 