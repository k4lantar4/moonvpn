import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Divider,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Avatar,
  useTheme,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  AccessTime as AccessTimeIcon,
  Info as InfoIcon,
  Public as PublicIcon,
  Speed as SpeedIcon,
  NetworkCell as NetworkCellIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';

// Mock data for subscription
const subscriptionData = {
  name: 'Pro Plan',
  status: 'active',
  expiryDate: '2025-04-13',
  dataLimit: 100, // GB
  dataUsed: 42.5, // GB
};

// Mock data for servers
const serverStatuses = [
  { id: 1, name: 'سرور آلمان', status: 'active', latency: 120 },
  { id: 2, name: 'سرور فرانسه', status: 'active', latency: 135 },
  { id: 3, name: 'سرور آمریکا', status: 'maintenance', latency: 200 },
  { id: 4, name: 'سرور هلند', status: 'active', latency: 110 },
];

// Mock data for recent activities
const recentActivities = [
  { 
    id: 1, 
    type: 'login', 
    date: '2025-03-13T09:23:12', 
    details: 'Login from Chrome on Windows' 
  },
  { 
    id: 2, 
    type: 'subscription', 
    date: '2025-03-10T14:05:32', 
    details: 'Renewed Pro Plan subscription' 
  },
  { 
    id: 3, 
    type: 'connection', 
    date: '2025-03-09T18:47:15', 
    details: 'Connected to Germany server' 
  },
  { 
    id: 4, 
    type: 'payment', 
    date: '2025-03-05T11:32:44', 
    details: 'Payment of $9.99 processed' 
  },
];

const Overview: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const { user } = useAuth();
  
  // Format date to local string
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fa-IR');
  };
  
  // Format date time to local string
  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('fa-IR');
  };
  
  // Get remaining days until expiry
  const getRemainingDays = (expiryDate: string) => {
    const now = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry.getTime() - now.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };
  
  // Get status chip for subscription
  const getStatusChip = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <Chip
            icon={<CheckCircleIcon />}
            label={t('dashboard.active')}
            color="success"
            size="small"
          />
        );
      case 'expired':
        return (
          <Chip
            icon={<ErrorIcon />}
            label={t('dashboard.expired')}
            color="error"
            size="small"
          />
        );
      case 'pending':
        return (
          <Chip
            icon={<AccessTimeIcon />}
            label={t('dashboard.pending')}
            color="warning"
            size="small"
          />
        );
      default:
        return (
          <Chip
            icon={<InfoIcon />}
            label={status}
            color="default"
            size="small"
          />
        );
    }
  };
  
  // Get status chip for server
  const getServerStatusChip = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <Chip
            label={t('dashboard.online')}
            color="success"
            size="small"
          />
        );
      case 'maintenance':
        return (
          <Chip
            label={t('dashboard.maintenance')}
            color="warning"
            size="small"
          />
        );
      case 'offline':
        return (
          <Chip
            label={t('dashboard.offline')}
            color="error"
            size="small"
          />
        );
      default:
        return (
          <Chip
            label={status}
            color="default"
            size="small"
          />
        );
    }
  };
  
  // Get icon for activity type
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'login':
        return <Avatar sx={{ bgcolor: 'primary.main' }}><InfoIcon /></Avatar>;
      case 'subscription':
        return <Avatar sx={{ bgcolor: 'success.main' }}><TimelineIcon /></Avatar>;
      case 'connection':
        return <Avatar sx={{ bgcolor: 'info.main' }}><PublicIcon /></Avatar>;
      case 'payment':
        return <Avatar sx={{ bgcolor: 'secondary.main' }}><AccessTimeIcon /></Avatar>;
      default:
        return <Avatar><InfoIcon /></Avatar>;
    }
  };
  
  // Get latency color based on value
  const getLatencyColor = (latency: number) => {
    if (latency < 120) return theme.palette.success.main;
    if (latency < 180) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {t('dashboard.welcomeUser', { name: user?.fullName || t('dashboard.user') })}
      </Typography>
      
      <Grid container spacing={3}>
        {/* Subscription Status */}
        <Grid item xs={12} md={6}>
          <Card elevation={3}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold">
                  {t('dashboard.subscriptionStatus')}
                </Typography>
                {getStatusChip(subscriptionData.status)}
              </Box>
              
              <Typography variant="body1">
                {subscriptionData.name}
              </Typography>
              
              <Box sx={{ mt: 2, mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {t('dashboard.expiresOn')}: {formatDate(subscriptionData.expiryDate)} 
                  ({getRemainingDays(subscriptionData.expiryDate)} {t('dashboard.daysLeft')})
                </Typography>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="body2" gutterBottom>
                {t('dashboard.dataUsage')}
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, mb: 0.5 }}>
                <Box sx={{ width: '100%', mr: 1 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={(subscriptionData.dataUsed / subscriptionData.dataLimit) * 100}
                    sx={{
                      height: 8,
                      borderRadius: 5,
                    }}
                  />
                </Box>
                <Box sx={{ minWidth: 35 }}>
                  <Typography variant="body2" color="text.secondary">
                    {Math.round((subscriptionData.dataUsed / subscriptionData.dataLimit) * 100)}%
                  </Typography>
                </Box>
              </Box>
              
              <Typography variant="body2" color="text.secondary">
                {subscriptionData.dataUsed} GB / {subscriptionData.dataLimit} GB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Server Status */}
        <Grid item xs={12} md={6}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                {t('dashboard.serverStatus')}
              </Typography>
              
              <TableContainer component={Paper} elevation={0}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('dashboard.serverName')}</TableCell>
                      <TableCell align="center">{t('dashboard.status')}</TableCell>
                      <TableCell align="right">{t('dashboard.latency')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {serverStatuses.map((server) => (
                      <TableRow key={server.id}>
                        <TableCell component="th" scope="row">
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <PublicIcon 
                              fontSize="small" 
                              sx={{ mr: 1, color: 'primary.main' }} 
                            />
                            {server.name}
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          {getServerStatusChip(server.status)}
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ 
                            display: 'flex', 
                            alignItems: 'center',
                            justifyContent: 'flex-end'
                          }}>
                            <NetworkCellIcon 
                              fontSize="small" 
                              sx={{ 
                                mr: 0.5, 
                                color: getLatencyColor(server.latency)
                              }} 
                            />
                            <Typography 
                              variant="body2"
                              sx={{ color: getLatencyColor(server.latency) }}
                            >
                              {server.latency} ms
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Stats */}
        <Grid item xs={12}>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card elevation={3}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                      <SpeedIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight="bold">
                        42 GB
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('dashboard.totalUsage')}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card elevation={3}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                      <TimelineIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight="bold">
                        123
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('dashboard.totalConnections')}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card elevation={3}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                      <PublicIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight="bold">
                        4
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('dashboard.availableServers')}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card elevation={3}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                      <AccessTimeIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight="bold">
                        {getRemainingDays(subscriptionData.expiryDate)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('dashboard.daysRemaining')}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
        
        {/* Recent Activities */}
        <Grid item xs={12}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                {t('dashboard.recentActivities')}
              </Typography>
              
              <List>
                {recentActivities.map((activity, index) => (
                  <React.Fragment key={activity.id}>
                    <Box sx={{ display: 'flex', py: 2 }}>
                      {getActivityIcon(activity.type)}
                      <Box sx={{ ml: 2, flexGrow: 1 }}>
                        <Typography variant="body1">
                          {activity.details}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {formatDateTime(activity.date)}
                        </Typography>
                      </Box>
                    </Box>
                    {index < recentActivities.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Custom list component
const List = ({ children }: { children: React.ReactNode }) => (
  <Box component="ul" sx={{ p: 0, m: 0, listStyle: 'none' }}>
    {children}
  </Box>
);

export default Overview; 