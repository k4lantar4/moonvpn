import React from 'react';
import { Box, Grid, Paper, Typography, useTheme } from '@mui/material';
import { useTranslation } from 'react-i18next';
import AccountCard from './AccountCard';
import WalletCard from './WalletCard';
import TrafficChart from './TrafficChart';
import RecentTransactions from './RecentTransactions';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ color: theme.palette.text.primary }}>
        {t('dashboard.title')}
      </Typography>

      <Grid container spacing={3}>
        {/* Wallet Card */}
        <Grid item xs={12} md={4}>
          <WalletCard />
        </Grid>

        {/* Traffic Usage */}
        <Grid item xs={12} md={8}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 240,
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography variant="h6" gutterBottom sx={{ color: theme.palette.text.primary }}>
              {t('dashboard.traffic_usage')}
            </Typography>
            <TrafficChart />
          </Paper>
        </Grid>

        {/* Active Accounts */}
        <Grid item xs={12}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography variant="h6" gutterBottom sx={{ color: theme.palette.text.primary }}>
              {t('dashboard.active_accounts')}
            </Typography>
            <AccountCard />
          </Paper>
        </Grid>

        {/* Recent Transactions */}
        <Grid item xs={12}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography variant="h6" gutterBottom sx={{ color: theme.palette.text.primary }}>
              {t('dashboard.recent_transactions')}
            </Typography>
            <RecentTransactions />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 