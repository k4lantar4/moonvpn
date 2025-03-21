import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  Paper,
  useTheme,
  Grid,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Avatar
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Storage as StorageIcon,
  ViewList as ViewListIcon,
  AttachMoney as MoneyIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  TrendingUp as TrendingUpIcon,
  Person as PersonIcon,
  ListAlt as ListAltIcon,
  ManageAccounts as ManageAccountsIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Import admin components
import UserManagement from './UserManagement';
import ServerManagement from './ServerManagement';
import PlanManagement from './PlanManagement';
import FinancialReports from './FinancialReports';
import SystemSettings from './SystemSettings';
import RoleManager from './RoleManager';

// TabPanel component to handle tab content
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
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
      style={{ width: '100%' }}
    >
      {value === index && (
        <Box sx={{ p: 0 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

// Example admin overview data
const overviewData = {
  totalUsers: 125,
  activeUsers: 98,
  totalServers: 8,
  activeServers: 7,
  totalPlans: 12,
  activePlans: 10,
  totalAccounts: 210,
  activeAccounts: 180,
  monthlyRevenue: 25000000,
  monthlyTraffic: 1250
};

// Example recent activities
const recentActivities = [
  { id: 1, type: 'user', action: 'ثبت نام کاربر جدید', user: 'user5', time: '10 دقیقه پیش' },
  { id: 2, type: 'account', action: 'خرید اشتراک جدید', user: 'user3', time: '30 دقیقه پیش' },
  { id: 3, type: 'payment', action: 'پرداخت موفق', user: 'user2', time: '1 ساعت پیش' },
  { id: 4, type: 'server', action: 'بروزرسانی سرور', user: 'admin1', time: '2 ساعت پیش' },
  { id: 5, type: 'plan', action: 'ایجاد پلن جدید', user: 'admin1', time: '3 ساعت پیش' }
];

// Admin Overview component
const AdminOverview: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {t('داشبورد مدیریت')}
      </Typography>
      
      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('کاربران')}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4">
                    {overviewData.totalUsers}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {overviewData.activeUsers} {t('فعال')}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                  <PeopleIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('سرورها')}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4">
                    {overviewData.totalServers}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {overviewData.activeServers} {t('آنلاین')}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: theme.palette.success.main }}>
                  <StorageIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('اکانت‌ها')}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4">
                    {overviewData.totalAccounts}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {overviewData.activeAccounts} {t('فعال')}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: theme.palette.info.main }}>
                  <ViewListIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('درآمد ماهانه')}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4">
                    {overviewData.monthlyRevenue.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('تومان')}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: theme.palette.warning.main }}>
                  <MoneyIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Recent Activities and Traffic */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('فعالیت‌های اخیر')}
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <List>
                {recentActivities.map((activity) => (
                  <ListItem key={activity.id} disablePadding>
                    <ListItemButton>
                      <ListItemIcon>
                        {activity.type === 'user' && <PersonIcon color="primary" />}
                        {activity.type === 'account' && <ViewListIcon color="info" />}
                        {activity.type === 'payment' && <MoneyIcon color="success" />}
                        {activity.type === 'server' && <StorageIcon color="warning" />}
                        {activity.type === 'plan' && <TrendingUpIcon color="error" />}
                      </ListItemIcon>
                      <ListItemText 
                        primary={activity.action}
                        secondary={`${activity.user} - ${activity.time}`}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('مصرف ترافیک ماهانه')}
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ height: 250, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography variant="h3" color="text.secondary">
                  {overviewData.monthlyTraffic} GB
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" align="center">
                {t('نمودار مصرف ترافیک در اینجا نمایش داده خواهد شد')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Main AdminDashboard component
const AdminDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const theme = useTheme();
  const { t } = useTranslation();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%', 
      bgcolor: theme.palette.background.default 
    }}>
      <Paper sx={{ borderRadius: 0 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="scrollable"
          scrollButtons="auto"
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider',
            '& .MuiTab-root': {
              minHeight: '64px',
              fontSize: '0.9rem'
            }
          }}
        >
          <Tab icon={<DashboardIcon />} label={t('داشبورد')} iconPosition="start" />
          <Tab icon={<PeopleIcon />} label={t('مدیریت کاربران')} iconPosition="start" />
          <Tab icon={<StorageIcon />} label={t('مدیریت سرورها')} iconPosition="start" />
          <Tab icon={<ListAltIcon />} label={t('مدیریت پلن‌ها')} iconPosition="start" />
          <Tab icon={<MoneyIcon />} label={t('گزارش‌های مالی')} iconPosition="start" />
          <Tab icon={<SettingsIcon />} label={t('تنظیمات سیستم')} iconPosition="start" />
          <Tab icon={<ManageAccountsIcon />} label={t('مدیریت نقش‌ها')} iconPosition="start" />
        </Tabs>
      </Paper>

      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <TabPanel value={tabValue} index={0}>
          <AdminOverview />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <UserManagement />
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <ServerManagement />
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          <PlanManagement />
        </TabPanel>
        <TabPanel value={tabValue} index={4}>
          <FinancialReports />
        </TabPanel>
        <TabPanel value={tabValue} index={5}>
          <SystemSettings />
        </TabPanel>
        <TabPanel value={tabValue} index={6}>
          <RoleManager />
        </TabPanel>
      </Box>
    </Box>
  );
};

export default AdminDashboard; 