import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Snackbar,
  Card,
  CardContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Backup as BackupIcon,
  Restore as RestoreIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Payment as PaymentIcon,
  Language as LanguageIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../services/api';
import { useTranslation } from 'react-i18next';

const Settings: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: adminApi.getSettings,
  });

  const updateSettingsMutation = useMutation({
    mutationFn: (data: any) => adminApi.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setSnackbarMessage(t('Settings updated successfully'));
      setSnackbarSeverity('success');
      setOpenSnackbar(true);
    },
    onError: (error: any) => {
      setSnackbarMessage(error.message || t('Error updating settings'));
      setSnackbarSeverity('error');
      setOpenSnackbar(true);
    },
  });

  const createBackupMutation = useMutation({
    mutationFn: () => adminApi.createBackup(),
    onSuccess: () => {
      setSnackbarMessage(t('Backup created successfully'));
      setSnackbarSeverity('success');
      setOpenSnackbar(true);
    },
    onError: (error: any) => {
      setSnackbarMessage(error.message || t('Error creating backup'));
      setSnackbarSeverity('error');
      setOpenSnackbar(true);
    },
  });

  const handleSaveSettings = (event: React.FormEvent) => {
    event.preventDefault();
    if (settings) {
      updateSettingsMutation.mutate(settings);
    }
  };

  const handleCreateBackup = () => {
    createBackupMutation.mutate();
  };

  if (isLoading) {
    return <Typography>{t('Loading...')}</Typography>;
  }

  const SettingCard: React.FC<{
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
  }> = ({ title, icon, children }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          {icon}
          <Typography variant="h6" ml={1}>
            {title}
          </Typography>
        </Box>
        {children}
      </CardContent>
    </Card>
  );

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('System Settings')}</Typography>
        <Box>
          <Tooltip title={t('Create Backup')}>
            <IconButton onClick={handleCreateBackup} color="primary">
              <BackupIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('Refresh')}>
            <IconButton onClick={() => queryClient.invalidateQueries({ queryKey: ['settings'] })}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <form onSubmit={handleSaveSettings}>
        <Grid container spacing={3}>
          {/* General Settings */}
          <Grid item xs={12} md={6}>
            <SettingCard title={t('General Settings')} icon={<SettingsIcon />}>
              <TextField
                fullWidth
                label={t('Site Name')}
                value={settings?.site_name || ''}
                onChange={(e) =>
                  setSettings({ ...settings, site_name: e.target.value })
                }
                margin="normal"
              />
              <TextField
                fullWidth
                label={t('Site Description')}
                value={settings?.site_description || ''}
                onChange={(e) =>
                  setSettings({ ...settings, site_description: e.target.value })
                }
                margin="normal"
                multiline
                rows={3}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.maintenance_mode || false}
                    onChange={(e) =>
                      setSettings({ ...settings, maintenance_mode: e.target.checked })
                    }
                  />
                }
                label={t('Maintenance Mode')}
              />
            </SettingCard>
          </Grid>

          {/* Security Settings */}
          <Grid item xs={12} md={6}>
            <SettingCard title={t('Security Settings')} icon={<SecurityIcon />}>
              <TextField
                fullWidth
                label={t('Session Timeout (minutes)')}
                type="number"
                value={settings?.session_timeout || 30}
                onChange={(e) =>
                  setSettings({ ...settings, session_timeout: parseInt(e.target.value) })
                }
                margin="normal"
              />
              <TextField
                fullWidth
                label={t('Max Login Attempts')}
                type="number"
                value={settings?.max_login_attempts || 5}
                onChange={(e) =>
                  setSettings({ ...settings, max_login_attempts: parseInt(e.target.value) })
                }
                margin="normal"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.enable_2fa || false}
                    onChange={(e) =>
                      setSettings({ ...settings, enable_2fa: e.target.checked })
                    }
                  />
                }
                label={t('Enable 2FA')}
              />
            </SettingCard>
          </Grid>

          {/* Notification Settings */}
          <Grid item xs={12} md={6}>
            <SettingCard title={t('Notification Settings')} icon={<NotificationsIcon />}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.enable_email_notifications || false}
                    onChange={(e) =>
                      setSettings({ ...settings, enable_email_notifications: e.target.checked })
                    }
                  />
                }
                label={t('Enable Email Notifications')}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.enable_telegram_notifications || false}
                    onChange={(e) =>
                      setSettings({ ...settings, enable_telegram_notifications: e.target.checked })
                    }
                  />
                }
                label={t('Enable Telegram Notifications')}
              />
              <TextField
                fullWidth
                label={t('Telegram Bot Token')}
                value={settings?.telegram_bot_token || ''}
                onChange={(e) =>
                  setSettings({ ...settings, telegram_bot_token: e.target.value })
                }
                margin="normal"
                type="password"
              />
            </SettingCard>
          </Grid>

          {/* Payment Settings */}
          <Grid item xs={12} md={6}>
            <SettingCard title={t('Payment Settings')} icon={<PaymentIcon />}>
              <TextField
                fullWidth
                label={t('Zarinpal Merchant ID')}
                value={settings?.zarinpal_merchant_id || ''}
                onChange={(e) =>
                  setSettings({ ...settings, zarinpal_merchant_id: e.target.value })
                }
                margin="normal"
              />
              <TextField
                fullWidth
                label={t('Minimum Withdrawal Amount')}
                type="number"
                value={settings?.min_withdrawal_amount || 100000}
                onChange={(e) =>
                  setSettings({ ...settings, min_withdrawal_amount: parseInt(e.target.value) })
                }
                margin="normal"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.enable_card_payment || false}
                    onChange={(e) =>
                      setSettings({ ...settings, enable_card_payment: e.target.checked })
                    }
                  />
                }
                label={t('Enable Card Payment')}
              />
            </SettingCard>
          </Grid>

          {/* Language Settings */}
          <Grid item xs={12} md={6}>
            <SettingCard title={t('Language Settings')} icon={<LanguageIcon />}>
              <TextField
                fullWidth
                select
                label={t('Default Language')}
                value={settings?.default_language || 'fa'}
                onChange={(e) =>
                  setSettings({ ...settings, default_language: e.target.value })
                }
                margin="normal"
              >
                <MenuItem value="fa">{t('Persian')}</MenuItem>
                <MenuItem value="en">{t('English')}</MenuItem>
              </TextField>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.enable_rtl || true}
                    onChange={(e) =>
                      setSettings({ ...settings, enable_rtl: e.target.checked })
                    }
                  />
                }
                label={t('Enable RTL')}
              />
            </SettingCard>
          </Grid>
        </Grid>

        <Box display="flex" justifyContent="flex-end" mt={3}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            disabled={updateSettingsMutation.isLoading}
          >
            {t('Save Settings')}
          </Button>
        </Box>
      </form>

      <Snackbar
        open={openSnackbar}
        autoHideDuration={6000}
        onClose={() => setOpenSnackbar(false)}
      >
        <Alert
          onClose={() => setOpenSnackbar(false)}
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings; 