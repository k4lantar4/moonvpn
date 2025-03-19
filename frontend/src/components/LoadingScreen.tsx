import React from 'react';
import { Box, CircularProgress, Typography, useTheme } from '@mui/material';
import { useTranslation } from 'react-i18next';

interface LoadingScreenProps {
  message?: string;
}

/**
 * LoadingScreen component displays a full-screen loading indicator
 * 
 * @param message - Optional custom loading message
 */
const LoadingScreen: React.FC<LoadingScreenProps> = ({ message }) => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // Default loading message
  const defaultMessage = t('در حال بارگذاری...');
  
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        bgcolor: theme.palette.background.default,
      }}
    >
      <CircularProgress 
        color="primary" 
        size={60} 
        thickness={4}
      />
      
      <Typography
        variant="h6"
        color="textSecondary"
        sx={{ mt: 3 }}
      >
        {message || defaultMessage}
      </Typography>
    </Box>
  );
};

export default LoadingScreen; 