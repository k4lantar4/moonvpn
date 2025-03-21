import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Payment as PaymentIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Delete as DeleteIcon,
  Done as DoneIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sellerApi } from '../../services/api';
import { formatDate } from '../../utils/formatters';
import { useTranslation } from 'react-i18next';

const Notifications: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['sellerNotifications', page],
    queryFn: () => sellerApi.getNotifications({ page, limit }),
  });

  const markAsReadMutation = useMutation({
    mutationFn: sellerApi.markNotificationAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sellerNotifications'] });
      setSuccessMessage(t('Notification marked as read'));
    },
    onError: (error: any) => {
      setErrorMessage(error.message || t('Failed to mark notification as read'));
    },
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: sellerApi.markAllNotificationsAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sellerNotifications'] });
      setSuccessMessage(t('All notifications marked as read'));
    },
    onError: (error: any) => {
      setErrorMessage(error.message || t('Failed to mark all notifications as read'));
    },
  });

  const handleMarkAsRead = (id: number) => {
    markAsReadMutation.mutate(id);
  };

  const handleMarkAllAsRead = () => {
    markAllAsReadMutation.mutate();
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'payment':
        return <PaymentIcon color="primary" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'success':
        return <CheckCircleIcon color="success" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'payment':
        return 'primary';
      case 'warning':
        return 'warning';
      case 'success':
        return 'success';
      default:
        return 'info';
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('Notifications')}</Typography>
        <Button
          variant="outlined"
          color="primary"
          startIcon={<DoneIcon />}
          onClick={handleMarkAllAsRead}
          disabled={markAllAsReadMutation.isPending}
        >
          {markAllAsReadMutation.isPending
            ? t('Marking all as read...')
            : t('Mark all as read')}
        </Button>
      </Box>

      <Paper>
        <List>
          {data?.results.map((notification: any, index: number) => (
            <React.Fragment key={notification.id}>
              {index > 0 && <Divider />}
              <ListItem
                alignItems="flex-start"
                sx={{
                  backgroundColor: notification.is_read ? 'transparent' : 'action.hover',
                }}
              >
                <ListItemIcon>
                  {getNotificationIcon(notification.type)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle1">
                        {notification.title}
                      </Typography>
                      {!notification.is_read && (
                        <Chip
                          label={t('New')}
                          size="small"
                          color={getNotificationColor(notification.type)}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.primary"
                      >
                        {notification.message}
                      </Typography>
                      <Typography
                        component="span"
                        variant="caption"
                        display="block"
                        color="text.secondary"
                        sx={{ mt: 1 }}
                      >
                        {formatDate(notification.created_at)}
                      </Typography>
                    </>
                  }
                />
                <ListItemSecondaryAction>
                  {!notification.is_read && (
                    <IconButton
                      edge="end"
                      onClick={() => handleMarkAsRead(notification.id)}
                      disabled={markAsReadMutation.isPending}
                    >
                      <DoneIcon />
                    </IconButton>
                  )}
                </ListItemSecondaryAction>
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      </Paper>

      {data?.results.length === 0 && (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          py={4}
        >
          <NotificationsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            {t('No notifications')}
          </Typography>
        </Box>
      )}

      <Snackbar
        open={!!successMessage}
        autoHideDuration={6000}
        onClose={() => setSuccessMessage('')}
      >
        <Alert severity="success" onClose={() => setSuccessMessage('')}>
          {successMessage}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!errorMessage}
        autoHideDuration={6000}
        onClose={() => setErrorMessage('')}
      >
        <Alert severity="error" onClose={() => setErrorMessage('')}>
          {errorMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Notifications; 