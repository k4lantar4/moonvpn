import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  useTheme
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  CloudDownload as CloudDownloadIcon,
  CloudUpload as CloudUploadIcon,
  Notifications as NotificationsIcon,
  Language as LanguageIcon,
  ColorLens as ColorLensIcon,
  Security as SecurityIcon,
  Storage as StorageIcon,
  Email as EmailIcon,
  Telegram as TelegramIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Example system settings data
const systemSettingsData = {
  general: {
    siteName: 'VPN Manager',
    siteDescription: 'مدیریت سرویس‌های VPN',
    adminEmail: 'admin@example.com',
    defaultLanguage: 'fa',
    theme: 'dark',
    maintenanceMode: false
  },
  notification: {
    emailNotifications: true,
    telegramNotifications: true,
    telegramBotToken: '1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    telegramAdminId: '123456789',
    lowBalanceThreshold: 10000,
    expiryReminderDays: 3
  },
  backup: {
    autoBackup: true,
    backupFrequency: 'daily',
    backupRetention: 7,
    backupLocation: 'local',
    lastBackup: '1402/06/25 14:30'
  },
  backupHistory: [
    { id: 1, date: '1402/06/25 14:30', size: '15.2 MB', status: 'success' },
    { id: 2, date: '1402/06/24 14:30', size: '14.8 MB', status: 'success' },
    { id: 3, date: '1402/06/23 14:30', size: '14.5 MB', status: 'success' },
    { id: 4, date: '1402/06/22 14:30', size: '14.3 MB', status: 'failed' },
    { id: 5, date: '1402/06/21 14:30', size: '14.1 MB', status: 'success' }
  ]
};

// TabPanel component
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const SystemSettings: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // State for tabs
  const [tabValue, setTabValue] = useState(0);
  
  // State for settings
  const [generalSettings, setGeneralSettings] = useState(systemSettingsData.general);
  const [notificationSettings, setNotificationSettings] = useState(systemSettingsData.notification);
  const [backupSettings, setBackupSettings] = useState(systemSettingsData.backup);
  
  // State for alerts
  const [showSuccessAlert, setShowSuccessAlert] = useState(false);
  
  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // Handle general settings change
  const handleGeneralSettingsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = e.target;
    setGeneralSettings({
      ...generalSettings,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  // Handle notification settings change
  const handleNotificationSettingsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = e.target;
    setNotificationSettings({
      ...notificationSettings,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  // Handle backup settings change
  const handleBackupSettingsChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    setBackupSettings({
      ...backupSettings,
      [name as string]: value
    });
  };
  
  // Handle save settings
  const handleSaveSettings = () => {
    // Save settings logic would go here
    console.log('Saving settings:', {
      general: generalSettings,
      notification: notificationSettings,
      backup: backupSettings
    });
    
    // Show success alert
    setShowSuccessAlert(true);
    setTimeout(() => {
      setShowSuccessAlert(false);
    }, 3000);
  };
  
  // Handle manual backup
  const handleManualBackup = () => {
    console.log('Creating manual backup');
    // Manual backup logic would go here
  };
  
  // Handle backup restore
  const handleRestoreBackup = (backupId: number) => {
    console.log('Restoring backup:', backupId);
    // Restore backup logic would go here
  };
  
  // Handle backup delete
  const handleDeleteBackup = (backupId: number) => {
    console.log('Deleting backup:', backupId);
    // Delete backup logic would go here
  };
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {t('تنظیمات سیستم')}
      </Typography>
      
      {/* Success Alert */}
      {showSuccessAlert && (
        <Alert 
          severity="success" 
          sx={{ mb: 3 }}
          onClose={() => setShowSuccessAlert(false)}
        >
          {t('تنظیمات با موفقیت ذخیره شد.')}
        </Alert>
      )}
      
      {/* Tabs */}
      <Card sx={{ mb: 3, bgcolor: theme.palette.background.paper }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<SettingsIcon />} label={t('تنظیمات عمومی')} iconPosition="start" />
          <Tab icon={<NotificationsIcon />} label={t('اعلان‌ها')} iconPosition="start" />
          <Tab icon={<StorageIcon />} label={t('پشتیبان‌گیری')} iconPosition="start" />
        </Tabs>
        
        {/* General Settings Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                name="siteName"
                label={t('نام سایت')}
                fullWidth
                margin="normal"
                value={generalSettings.siteName}
                onChange={handleGeneralSettingsChange}
              />
              
              <TextField
                name="siteDescription"
                label={t('توضیحات سایت')}
                fullWidth
                margin="normal"
                multiline
                rows={2}
                value={generalSettings.siteDescription}
                onChange={handleGeneralSettingsChange}
              />
              
              <TextField
                name="adminEmail"
                label={t('ایمیل مدیر')}
                fullWidth
                margin="normal"
                value={generalSettings.adminEmail}
                onChange={handleGeneralSettingsChange}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>{t('زبان پیش‌فرض')}</InputLabel>
                <Select
                  name="defaultLanguage"
                  value={generalSettings.defaultLanguage}
                  label={t('زبان پیش‌فرض')}
                  onChange={handleGeneralSettingsChange as any}
                >
                  <MenuItem value="fa">{t('فارسی')}</MenuItem>
                  <MenuItem value="en">{t('انگلیسی')}</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>{t('تم')}</InputLabel>
                <Select
                  name="theme"
                  value={generalSettings.theme}
                  label={t('تم')}
                  onChange={handleGeneralSettingsChange as any}
                >
                  <MenuItem value="light">{t('روشن')}</MenuItem>
                  <MenuItem value="dark">{t('تیره')}</MenuItem>
                </Select>
              </FormControl>
              
              <FormControlLabel
                control={
                  <Switch
                    name="maintenanceMode"
                    checked={generalSettings.maintenanceMode}
                    onChange={handleGeneralSettingsChange}
                  />
                }
                label={t('حالت تعمیر و نگهداری')}
                sx={{ mt: 2 }}
              />
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Notification Settings Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                {t('تنظیمات ایمیل')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    name="emailNotifications"
                    checked={notificationSettings.emailNotifications}
                    onChange={handleNotificationSettingsChange}
                  />
                }
                label={t('فعال‌سازی اعلان‌های ایمیل')}
              />
              
              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                {t('تنظیمات تلگرام')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    name="telegramNotifications"
                    checked={notificationSettings.telegramNotifications}
                    onChange={handleNotificationSettingsChange}
                  />
                }
                label={t('فعال‌سازی اعلان‌های تلگرام')}
              />
              
              <TextField
                name="telegramBotToken"
                label={t('توکن ربات تلگرام')}
                fullWidth
                margin="normal"
                value={notificationSettings.telegramBotToken}
                onChange={handleNotificationSettingsChange}
              />
              
              <TextField
                name="telegramAdminId"
                label={t('شناسه مدیر تلگرام')}
                fullWidth
                margin="normal"
                value={notificationSettings.telegramAdminId}
                onChange={handleNotificationSettingsChange}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                {t('آستانه‌های اعلان')}
              </Typography>
              
              <TextField
                name="lowBalanceThreshold"
                label={t('آستانه موجودی کم (تومان)')}
                fullWidth
                margin="normal"
                type="number"
                value={notificationSettings.lowBalanceThreshold}
                onChange={handleNotificationSettingsChange}
              />
              
              <TextField
                name="expiryReminderDays"
                label={t('یادآوری انقضا (روز قبل)')}
                fullWidth
                margin="normal"
                type="number"
                value={notificationSettings.expiryReminderDays}
                onChange={handleNotificationSettingsChange}
              />
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Backup Settings Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                {t('تنظیمات پشتیبان‌گیری')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    name="autoBackup"
                    checked={backupSettings.autoBackup}
                    onChange={handleBackupSettingsChange as any}
                  />
                }
                label={t('پشتیبان‌گیری خودکار')}
              />
              
              <FormControl fullWidth margin="normal">
                <InputLabel>{t('تناوب پشتیبان‌گیری')}</InputLabel>
                <Select
                  name="backupFrequency"
                  value={backupSettings.backupFrequency}
                  label={t('تناوب پشتیبان‌گیری')}
                  onChange={handleBackupSettingsChange}
                >
                  <MenuItem value="daily">{t('روزانه')}</MenuItem>
                  <MenuItem value="weekly">{t('هفتگی')}</MenuItem>
                  <MenuItem value="monthly">{t('ماهانه')}</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                name="backupRetention"
                label={t('نگهداری پشتیبان (روز)')}
                fullWidth
                margin="normal"
                type="number"
                value={backupSettings.backupRetention}
                onChange={handleBackupSettingsChange as any}
              />
              
              <FormControl fullWidth margin="normal">
                <InputLabel>{t('محل ذخیره‌سازی')}</InputLabel>
                <Select
                  name="backupLocation"
                  value={backupSettings.backupLocation}
                  label={t('محل ذخیره‌سازی')}
                  onChange={handleBackupSettingsChange}
                >
                  <MenuItem value="local">{t('محلی')}</MenuItem>
                  <MenuItem value="cloud">{t('ابری')}</MenuItem>
                </Select>
              </FormControl>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  {t('آخرین پشتیبان‌گیری')}: {backupSettings.lastBackup}
                </Typography>
              </Box>
              
              <Button
                variant="contained"
                color="primary"
                startIcon={<CloudDownloadIcon />}
                sx={{ mt: 2 }}
                onClick={handleManualBackup}
              >
                {t('پشتیبان‌گیری دستی')}
              </Button>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                {t('تاریخچه پشتیبان‌گیری')}
              </Typography>
              
              <List>
                {systemSettingsData.backupHistory.map((backup) => (
                  <ListItem key={backup.id} divider>
                    <ListItemText
                      primary={backup.date}
                      secondary={`${t('اندازه')}: ${backup.size} - ${t('وضعیت')}: ${
                        backup.status === 'success' ? t('موفق') : t('ناموفق')
                      }`}
                    />
                    <ListItemSecondaryAction>
                      <Tooltip title={t('بازیابی')}>
                        <IconButton
                          edge="end"
                          onClick={() => handleRestoreBackup(backup.id)}
                          disabled={backup.status !== 'success'}
                        >
                          <CloudUploadIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={t('حذف')}>
                        <IconButton
                          edge="end"
                          onClick={() => handleDeleteBackup(backup.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>
      
      {/* Save Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
        <Button
          variant="contained"
          color="primary"
          startIcon={<SaveIcon />}
          onClick={handleSaveSettings}
        >
          {t('ذخیره تنظیمات')}
        </Button>
      </Box>
    </Box>
  );
};

export default SystemSettings; 