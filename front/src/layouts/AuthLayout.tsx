import React, { ReactNode } from 'react';
import {
  Box,
  Container,
  Paper,
  IconButton,
  Typography,
  useTheme,
  Tooltip
} from '@mui/material';
import { Outlet } from 'react-router-dom';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import TranslateIcon from '@mui/icons-material/Translate';
import { useTranslation } from 'react-i18next';

interface AuthLayoutProps {
  children?: ReactNode;
  toggleTheme?: () => void;
  toggleLanguage?: () => void;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ 
  children, 
  toggleTheme, 
  toggleLanguage 
}) => {
  const theme = useTheme();
  const { t } = useTranslation();
  const isDarkMode = theme.palette.mode === 'dark';
  const isRtl = theme.direction === 'rtl';

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        bgcolor: 'background.default',
        background: theme.palette.mode === 'dark' 
          ? 'linear-gradient(45deg, #050505 0%, #1a1a1a 100%)' 
          : 'linear-gradient(45deg, #f0f0f0 0%, #ffffff 100%)',
      }}
    >
      {/* Header with theme toggle and language toggle */}
      <Box
        component="header"
        sx={{
          p: 2,
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
        }}
      >
        <Tooltip title={t('layout.toggleTheme')}>
          <IconButton
            onClick={toggleTheme}
            color="inherit"
            sx={{ mr: 1 }}
          >
            {isDarkMode ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>
        </Tooltip>
        <Tooltip title={t('layout.toggleLanguage')}>
          <IconButton
            onClick={toggleLanguage}
            color="inherit"
          >
            <TranslateIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Main content */}
      <Container 
        component="main" 
        maxWidth="xs" 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          flexGrow: 1,
          py: 4
        }}
      >
        {/* Logo and app name */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            mb: 4,
          }}
        >
          <img 
            src="/logo.png" 
            alt="مدیریت وی‌پی‌ان" 
            style={{ 
              width: 80, 
              height: 80, 
              marginBottom: 16 
            }} 
          />
          <Typography
            component="h1"
            variant="h4"
            color="primary"
            fontWeight="bold"
            sx={{ mb: 1 }}
          >
            {t('layout.appName')}
          </Typography>
          <Typography
            variant="subtitle1"
            color="text.secondary"
            align="center"
          >
            {t('layout.appTagline')}
          </Typography>
        </Box>

        {/* Auth form container */}
        <Paper
          elevation={6}
          sx={{
            p: 4,
            width: '100%',
            borderRadius: 2,
            boxShadow: theme.palette.mode === 'dark'
              ? '0 8px 32px rgba(0, 0, 0, 0.5)'
              : '0 8px 32px rgba(0, 0, 0, 0.1)',
          }}
        >
          {children || <Outlet />}
        </Paper>
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          textAlign: 'center',
        }}
      >
        <Typography variant="body2" color="text.secondary">
          {t('layout.copyright', { year: new Date().getFullYear() })}
        </Typography>
      </Box>
    </Box>
  );
};

export default AuthLayout; 