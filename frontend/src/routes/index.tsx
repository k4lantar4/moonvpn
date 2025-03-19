import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
import ResponsiveLayout from '../layouts/ResponsiveLayout';
import Dashboard from '../pages/Dashboard';
import Accounts from '../pages/Accounts';
import Settings from '../pages/Settings';
import Help from '../pages/Help';
import Login from '../pages/Login';
import Register from '../pages/Register';
import NotFound from '../pages/NotFound';

// Lazy load components
const UserManagement = React.lazy(() => import('../components/Users/UserManagement'));
const ServerManagement = React.lazy(() => import('../components/Servers/ServerManagement'));
const AccessibilitySettings = React.lazy(() => import('../components/Settings/AccessibilitySettings'));
const KeyboardShortcuts = React.lazy(() => import('../components/Settings/KeyboardShortcuts'));
const TutorialGuide = React.lazy(() => import('../components/Tutorial/TutorialGuide'));

// Lazy load our new components
const UserDashboard = React.lazy(() => import('../components/Dashboard'));
const AccountManagement = React.lazy(() => import('../pages/AccountManagement'));
const AdminDashboard = React.lazy(() => import('../pages/AdminDashboard'));

// Loading component
const LoadingFallback = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="100vh"
  >
    <CircularProgress />
  </Box>
);

const AppRoutes = () => {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={
            <ResponsiveLayout title="Dashboard">
              <Dashboard />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/user-dashboard"
          element={
            <ResponsiveLayout title="User Dashboard">
              <UserDashboard />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/account-management"
          element={
            <ResponsiveLayout title="Account Management">
              <AccountManagement />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/admin"
          element={
            <ResponsiveLayout title="Admin Dashboard">
              <AdminDashboard />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/accounts"
          element={
            <ResponsiveLayout title="Accounts">
              <Accounts />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/settings"
          element={
            <ResponsiveLayout title="Settings">
              <Settings />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/help"
          element={
            <ResponsiveLayout title="Help">
              <Help />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/login"
          element={
            <ResponsiveLayout title="Login">
              <Login />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/register"
          element={
            <ResponsiveLayout title="Register">
              <Register />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/users"
          element={
            <ResponsiveLayout title="User Management">
              <UserManagement />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/servers"
          element={
            <ResponsiveLayout title="Server Management">
              <ServerManagement />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/settings/accessibility"
          element={
            <ResponsiveLayout title="Accessibility Settings">
              <AccessibilitySettings />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/settings/keyboard-shortcuts"
          element={
            <ResponsiveLayout title="Keyboard Shortcuts">
              <KeyboardShortcuts />
            </ResponsiveLayout>
          }
        />
        <Route
          path="/tutorial"
          element={
            <ResponsiveLayout title="Tutorial">
              <TutorialGuide />
            </ResponsiveLayout>
          }
        />
        <Route
          path="*"
          element={
            <ResponsiveLayout title="Not Found">
              <NotFound />
            </ResponsiveLayout>
          }
        />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes; 