import { useCallback, useState } from 'react';
import { useDispatch } from 'react-redux';
import { addNotification, removeNotification } from '../store/slices/notificationSlice';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface NotificationOptions {
  duration?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  autoHide?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface Notification {
  id: string;
  message: string;
  type: NotificationType;
  options: NotificationOptions;
}

export const useNotification = () => {
  const dispatch = useDispatch();
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const showNotification = useCallback(
    (
      message: string,
      type: NotificationType = 'info',
      options: NotificationOptions = {}
    ) => {
      const defaultOptions: NotificationOptions = {
        duration: 5000,
        position: 'top-right',
        autoHide: true,
        ...options,
      };

      const notification: Notification = {
        id: Date.now().toString(),
        message,
        type,
        options: defaultOptions,
      };

      dispatch(addNotification(notification));
      setNotifications((prev) => [...prev, notification]);

      if (defaultOptions.autoHide && defaultOptions.duration) {
        setTimeout(() => {
          hideNotification(notification.id);
        }, defaultOptions.duration);
      }

      return notification.id;
    },
    [dispatch]
  );

  const hideNotification = useCallback(
    (id: string) => {
      dispatch(removeNotification(id));
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    },
    [dispatch]
  );

  const showSuccess = useCallback(
    (message: string, options?: NotificationOptions) => {
      return showNotification(message, 'success', options);
    },
    [showNotification]
  );

  const showError = useCallback(
    (message: string, options?: NotificationOptions) => {
      return showNotification(message, 'error', options);
    },
    [showNotification]
  );

  const showWarning = useCallback(
    (message: string, options?: NotificationOptions) => {
      return showNotification(message, 'warning', options);
    },
    [showNotification]
  );

  const showInfo = useCallback(
    (message: string, options?: NotificationOptions) => {
      return showNotification(message, 'info', options);
    },
    [showNotification]
  );

  const clearAll = useCallback(() => {
    notifications.forEach((notification) => {
      hideNotification(notification.id);
    });
  }, [notifications, hideNotification]);

  return {
    notifications,
    showNotification,
    hideNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    clearAll,
  };
}; 