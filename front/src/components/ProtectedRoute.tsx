import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, UserRole } from '../contexts/AuthContext';
import LoadingScreen from './LoadingScreen';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: UserRole[];
  redirectPath?: string;
}

/**
 * ProtectedRoute component that restricts access based on user authentication and role
 * 
 * @param children - The protected component/route
 * @param requiredRoles - Roles allowed to access this route (if empty, any authenticated user can access)
 * @param redirectPath - Path to redirect to if not authenticated or not authorized
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles = [],
  redirectPath = '/auth/login',
}) => {
  const { isAuthenticated, user, isLoading, hasPermission } = useAuth();
  const location = useLocation();

  // Show loading screen while checking auth status
  if (isLoading) {
    return <LoadingScreen />;
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to={redirectPath} state={{ from: location }} replace />;
  }

  // If authentication is required but no specific roles, allow access
  if (requiredRoles.length === 0) {
    return <>{children}</>;
  }

  // Check if user has required role
  if (!hasPermission(requiredRoles)) {
    // For admins, redirect to admin dashboard
    if (user?.role === UserRole.ADMIN) {
      return <Navigate to="/admin/dashboard" replace />;
    }
    
    // For regular users, redirect to user dashboard
    return <Navigate to="/dashboard" replace />;
  }

  // User is authenticated and has required role, render the protected route
  return <>{children}</>;
};

export default ProtectedRoute; 