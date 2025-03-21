import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Divider,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import PersonIcon from '@mui/icons-material/Person';
import StorageIcon from '@mui/icons-material/Storage';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Line, LineChart } from 'recharts';

// Example data for charts
const salesData = [
  { name: '1402/01', value: 1200000 },
  { name: '1402/02', value: 1900000 },
  { name: '1402/03', value: 2500000 },
  { name: '1402/04', value: 2100000 },
  { name: '1402/05', value: 2800000 },
  { name: '1402/06', value: 2300000 },
  { name: '1402/07', value: 3000000 },
  { name: '1402/08', value: 2800000 },
  { name: '1402/09', value: 3500000 },
  { name: '1402/10', value: 3900000 },
  { name: '1402/11', value: 4200000 },
  { name: '1402/12', value: 5000000 },
];

const trafficData = [
  { name: '1402/12/01', download: 120, upload: 50 },
  { name: '1402/12/02', download: 150, upload: 60 },
  { name: '1402/12/03', download: 180, upload: 70 },
  { name: '1402/12/04', download: 140, upload: 55 },
  { name: '1402/12/05', download: 160, upload: 65 },
  { name: '1402/12/06', download: 200, upload: 80 },
  { name: '1402/12/07', download: 220, upload: 85 },
];

const AdminOverview: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();

  // Example statistics
  const stats = [
    {
      title: t('admin.overview.total_users'),
      value: '367',
      icon: <PersonIcon sx={{ fontSize: 40, color: theme.palette.primary.main }} />,
      color: theme.palette.primary.main,
    },
    {
      title: t('admin.overview.active_accounts'),
      value: '285',
      icon: <VpnKeyIcon sx={{ fontSize: 40, color: theme.palette.success.main }} />,
      color: theme.palette.success.main,
    },
    {
      title: t('admin.overview.total_servers'),
      value: '12',
      icon: <StorageIcon sx={{ fontSize: 40, color: theme.palette.info.main }} />,
      color: theme.palette.info.main,
    },
    {
      title: t('admin.overview.monthly_revenue'),
      value: '8,500,000 تومان',
      icon: <AccountBalanceWalletIcon sx={{ fontSize: 40, color: theme.palette.warning.main }} />,
      color: theme.palette.warning.main,
    },
  ];

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Typography variant="h5" sx={{ mb: 4, color: theme.palette.text.primary, fontWeight: 'bold' }}>
        {t('admin.overview.title')}
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              sx={{ 
                height: '100%',
                backgroundColor: theme.palette.background.paper,
                boxShadow: `0 0 10px 0 ${stat.color}15`,
                border: `1px solid ${stat.color}30`,
                transition: 'transform 0.3s',
                '&:hover': {
                  transform: 'translateY(-5px)',
                  boxShadow: `0 5px 15px 0 ${stat.color}25`,
                },
              }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ mr: 2 }}>{stat.icon}</Box>
                <Box>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {stat.title}
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 'bold', color: stat.color }}>
                    {stat.value}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Charts */}
      <Grid container spacing={4}>
        {/* Monthly Sales Chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ backgroundColor: theme.palette.background.paper, height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                {t('admin.overview.monthly_sales')}
              </Typography>
              <Divider sx={{ mb: 3 }} />
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={salesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                    <XAxis
                      dataKey="name"
                      stroke={theme.palette.text.secondary}
                      fontSize={12}
                    />
                    <YAxis
                      stroke={theme.palette.text.secondary}
                      fontSize={12}
                      tickFormatter={(value) => `${value / 1000000}M`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: 4,
                      }}
                      formatter={(value: any) => [`${value.toLocaleString('fa-IR')} تومان`, t('admin.overview.sales')]}
                    />
                    <Bar
                      dataKey="value"
                      name={t('admin.overview.sales')}
                      fill={theme.palette.primary.main}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Traffic Chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ backgroundColor: theme.palette.background.paper, height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                {t('admin.overview.traffic_usage')}
              </Typography>
              <Divider sx={{ mb: 3 }} />
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trafficData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                    <XAxis
                      dataKey="name"
                      stroke={theme.palette.text.secondary}
                      fontSize={12}
                    />
                    <YAxis
                      stroke={theme.palette.text.secondary}
                      fontSize={12}
                      tickFormatter={(value) => `${value}GB`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: 4,
                      }}
                      formatter={(value: any) => [`${value} GB`, '']}
                    />
                    <Legend wrapperStyle={{ paddingTop: 10 }} />
                    <Line
                      type="monotone"
                      dataKey="download"
                      name={t('admin.overview.download')}
                      stroke={theme.palette.info.main}
                      activeDot={{ r: 8 }}
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="upload"
                      name={t('admin.overview.upload')}
                      stroke={theme.palette.warning.main}
                      activeDot={{ r: 8 }}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdminOverview; 