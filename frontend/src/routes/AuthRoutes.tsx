import React from 'react';
import { Route, Routes } from 'react-router-dom';
import AuthLayout from '../layouts/AuthLayout';
import Login from '../pages/Auth/Login';
import Register from '../pages/Auth/Register';
import ForgotPassword from '../pages/Auth/ForgotPassword';

interface AuthRoutesProps {
  toggleTheme: () => void;
  toggleLanguage: () => void;
}

const AuthRoutes = {
  path: '/auth',
  element: <AuthLayout toggleTheme={undefined} toggleLanguage={undefined} />,
  children: [
    {
      path: 'login',
      element: <Login />
    },
    {
      path: 'register',
      element: <Register />
    },
    {
      path: 'forgot-password',
      element: <ForgotPassword />
    },
    // Redirect to login page by default
    {
      path: '',
      element: <Login />
    }
  ]
};

// This component is only used when the route is rendered directly
const AuthRoutesComponent = ({ toggleTheme, toggleLanguage }: AuthRoutesProps) => {
  return (
    <AuthLayout toggleTheme={toggleTheme} toggleLanguage={toggleLanguage}>
      <Routes>
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="forgot-password" element={<ForgotPassword />} />
        <Route path="" element={<Login />} />
      </Routes>
    </AuthLayout>
  );
};

export default AuthRoutes; 