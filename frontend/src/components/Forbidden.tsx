import React from 'react';
import { Box, Typography, Button, Paper, useTheme } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LockOutlined as LockIcon, Home as HomeIcon } from '@mui/icons-material';

interface ForbiddenProps {
  message?: string;
}

/**
 * Forbidden component displays a "403 Forbidden" error when user tries to access an unauthorized page
 * 
 * @param message - Optional custom error message
 */
const Forbidden: React.FC<ForbiddenProps> = ({ message }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // Default forbidden message
  const defaultMessage = t('شما اجازه دسترسی به این صفحه را ندارید');
  
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        bgcolor: theme.palette.background.default,
        p: 2,
      }}
    >
      <Paper
        elevation={4}
        sx={{
          p: 5,
          borderRadius: 2,
          textAlign: 'center',
          maxWidth: '500px',
          width: '100%',
        }}
      >
        <LockIcon 
          color="error" 
          sx={{ fontSize: 60, mb: 2 }}
        />
        
        <Typography variant="h4" color="error" gutterBottom>
          403
        </Typography>
        
        <Typography variant="h5" gutterBottom>
          {t('دسترسی محدود شده')}
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          {message || defaultMessage}
        </Typography>
        
        <Button
          component={RouterLink}
          to="/"
          variant="contained"
          color="primary"
          startIcon={<HomeIcon />}
          sx={{ mt: 2 }}
        >
          {t('بازگشت به صفحه اصلی')}
        </Button>
      </Paper>
    </Box>
  );
};

export default Forbidden; 