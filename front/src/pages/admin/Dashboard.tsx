import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Server as ServerIcon,
  People as PeopleIcon,
  ShoppingCart as ShoppingCartIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../../services/api';
import { formatNumber, formatDate } from '../../utils/formatters';
import { useTranslation } from 'react-i18next';

const AdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { data: stats, refetch } = useQuery({
    queryKey: ['adminStats'],
    queryFn: adminApi.getStats,
  });

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, icon, color }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4">{value}</Typography>
          </Box>
          <Box
            sx={{
              backgroundColor: `${color}20`,
              borderRadius: '50%',
              p: 1,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const ServerStatusCard: React.FC<{
    server: any;
  }> = ({ server }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h6">{server.name}</Typography>
            <Typography color="textSecondary">
              {server.status === 'healthy' ? t('Healthy') : t('Unhealthy')}
            </Typography>
          </Box>
          <Box>
            <LinearProgress
              variant="determinate"
              value={server.cpu_usage}
              color={server.cpu_usage > 80 ? 'error' : 'primary'}
              sx={{ mb: 1 }}
            />
            <Typography variant="body2" color="textSecondary">
              CPU: {server.cpu_usage}%
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('Admin Dashboard')}</Typography>
        <Tooltip title={t('Refresh')}>
          <IconButton onClick={() => refetch()}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Total Users')}
            value={stats?.total_users || 0}
            icon={<PeopleIcon sx={{ color: '#1976d2' }} />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Active Servers')}
            value={stats?.active_servers || 0}
            icon={<ServerIcon sx={{ color: '#2e7d32' }} />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Total Sales')}
            value={formatNumber(stats?.total_sales || 0)}
            icon={<ShoppingCartIcon sx={{ color: '#ed6c02' }} />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Monthly Growth')}
            value={`${stats?.monthly_growth || 0}%`}
            icon={<TrendingUpIcon sx={{ color: '#9c27b0' }} />}
            color="#9c27b0"
          />
        </Grid>

        {/* Server Status */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              {t('Server Status')}
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              {stats?.servers.map((server: any) => (
                <ServerStatusCard key={server.id} server={server} />
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              {t('Recent Activity')}
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              {stats?.recent_activity.map((activity: any) => (
                <Box
                  key={activity.id}
                  display="flex"
                  alignItems="center"
                  justifyContent="space-between"
                >
                  <Box>
                    <Typography variant="body1">{activity.description}</Typography>
                    <Typography variant="body2" color="textSecondary">
                      {formatDate(activity.timestamp)}
                    </Typography>
                  </Box>
                  {activity.type === 'warning' && (
                    <WarningIcon color="warning" />
                  )}
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdminDashboard; 