import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Grid,
  Paper,
  Typography,
  useTheme,
  CircularProgress,
  Card,
  CardContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  AccountCircle as AccountIcon,
  VpnKey as VpnIcon,
  Payment as PaymentIcon,
} from '@mui/icons-material';
import { RootState } from '../store';
import { useGetVpnAccountsQuery, useGetPaymentsQuery } from '../store/api';
import { setActivePage } from '../store/slices/uiSlice';
import { formatCurrency } from '../utils/formatters';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const { data: vpnAccounts, isLoading: isLoadingVpn } = useGetVpnAccountsQuery();
  const { data: payments, isLoading: isLoadingPayments } = useGetPaymentsQuery();
  const { statistics } = useSelector((state: RootState) => state.payment);

  useEffect(() => {
    dispatch(setActivePage('dashboard'));
  }, [dispatch]);

  const stats = [
    {
      title: 'Total Users',
      value: vpnAccounts?.length || 0,
      icon: <AccountIcon sx={{ fontSize: 40, color: theme.palette.primary.main }} />,
    },
    {
      title: 'Active VPNs',
      value: vpnAccounts?.filter(account => account.status === 'active').length || 0,
      icon: <VpnIcon sx={{ fontSize: 40, color: theme.palette.success.main }} />,
    },
    {
      title: 'Total Revenue',
      value: formatCurrency(statistics.totalAmount),
      icon: <PaymentIcon sx={{ fontSize: 40, color: theme.palette.warning.main }} />,
    },
    {
      title: 'Monthly Growth',
      value: '+12.5%',
      icon: <TrendingUpIcon sx={{ fontSize: 40, color: theme.palette.info.main }} />,
    },
  ];

  if (isLoadingVpn || isLoadingPayments) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="80vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Tooltip title="Refresh Data">
          <IconButton>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Grid container spacing={3}>
        {/* Stats Cards */}
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h5" component="div">
                      {stat.value}
                    </Typography>
                  </Box>
                  {stat.icon}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent VPN Accounts
            </Typography>
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Name</th>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Status</th>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Plan</th>
                  </tr>
                </thead>
                <tbody>
                  {vpnAccounts?.slice(0, 5).map((account) => (
                    <tr key={account.id}>
                      <td style={{ padding: '8px' }}>{account.name}</td>
                      <td style={{ padding: '8px' }}>
                        <Typography
                          component="span"
                          sx={{
                            color: account.status === 'active' ? 'success.main' : 'error.main',
                          }}
                        >
                          {account.status}
                        </Typography>
                      </td>
                      <td style={{ padding: '8px' }}>{account.plan}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Payments */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Payments
            </Typography>
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px' }}>ID</th>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Amount</th>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {payments?.slice(0, 5).map((payment) => (
                    <tr key={payment.id}>
                      <td style={{ padding: '8px' }}>{payment.id}</td>
                      <td style={{ padding: '8px' }}>{formatCurrency(payment.amount)}</td>
                      <td style={{ padding: '8px' }}>
                        <Typography
                          component="span"
                          sx={{
                            color:
                              payment.status === 'completed'
                                ? 'success.main'
                                : payment.status === 'pending'
                                ? 'warning.main'
                                : 'error.main',
                          }}
                        >
                          {payment.status}
                        </Typography>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 