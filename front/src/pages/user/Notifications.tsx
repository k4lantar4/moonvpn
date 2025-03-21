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
  Divider,
  Button,
  Chip,
  Badge,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Delete as DeleteIcon,
  DoneAll as DoneAllIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '../../services/api';
import { useTranslation } from 'react-i18next';
import { formatDate } from '../../utils/formatters';

const Notifications: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [limit] = useState(20);

  const { data: notificationsData, isLoading } = useQuery({
    queryKey: ['notifications', page],
    queryFn: () => userApi.getNotifications({ page, limit }),
  });

  const markAsReadMutation = useMutation({
    mutationFn: (id: string) => userApi.markNotificationAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: userApi.markAllNotificationsAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const handleMarkAsRead = (id: string) => {
    markAsReadMutation.mutate(id);
  };

  const handleMarkAllAsRead = () => {
    markAllAsReadMutation.mutate();
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'info':
        return <InfoIcon color="info" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <NotificationsIcon />;
    }
  };

  const getNotificationChip = (type: string) => {
    const typeMap = {
      info: { color: 'info', label: t('Info') },
      warning: { color: 'warning', label: t('Warning') },
      success: { color: 'success', label: t('Success') },
      error: { color: 'error', label: t('Error') },
    };

    const typeInfo = typeMap[type as keyof typeof typeMap] || {
      color: 'default',
      label: type,
    };

    return (
      <Chip
        label={typeInfo.label}
        color={typeInfo.color as any}
        size="small"
      />
    );
  };

  if (isLoading) {
    return <Typography>{t('Loading...')}</Typography>;
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('Notifications')}</Typography>
        <Button
          startIcon={<DoneAllIcon />}
          onClick={handleMarkAllAsRead}
          disabled={markAllAsReadMutation.isPending}
        >
          {t('Mark all as read')}
        </Button>
      </Box>

      <Paper>
        <List>
          {notificationsData?.notifications.map((notification: any, index: number) => (
            <React.Fragment key={notification.id}>
              {index > 0 && <Divider />}
              <ListItem
                sx={{
                  bgcolor: notification.read ? 'transparent' : 'action.hover',
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                }}
              >
                <ListItemIcon>
                  <Badge
                    color="error"
                    variant="dot"
                    invisible={notification.read}
                    sx={{
                      '& .MuiBadge-badge': {
                        right: -3,
                        top: 13,
                      },
                    }}
                  >
                    {getNotificationIcon(notification.type)}
                  </Badge>
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle1">
                        {notification.title}
                      </Typography>
                      {getNotificationChip(notification.type)}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(notification.created_at)}
                      </Typography>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    onClick={() => handleMarkAsRead(notification.id)}
                    disabled={markAsReadMutation.isPending || notification.read}
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      </Paper>

      {notificationsData?.total > page * limit && (
        <Box display="flex" justifyContent="center" mt={3}>
          <Button
            variant="outlined"
            onClick={() => setPage((prev) => prev + 1)}
          >
            {t('Load more')}
          </Button>
        </Box>
      )}

      {notificationsData?.notifications.length === 0 && (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          py={5}
        >
          <NotificationsIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography color="text.secondary">
            {t('No notifications found')}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default Notifications; 