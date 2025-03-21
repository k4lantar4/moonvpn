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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  AccountBalance as AccountBalanceIcon,
  Speed as SpeedIcon,
  History as HistoryIcon,
  Notifications as NotificationsIcon,
  QrCode as QrCodeIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { userApi } from '../../services/api';
import { formatNumber, formatDate, formatBytes } from '../../utils/formatters';
import { useTranslation } from 'react-i18next';

const UserDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [openDepositDialog, setOpenDepositDialog] = React.useState(false);
  const [depositAmount, setDepositAmount] = React.useState('');
  const [openWithdrawDialog, setOpenWithdrawDialog] = React.useState(false);
  const [withdrawAmount, setWithdrawAmount] = React.useState('');
  const [cardNumber, setCardNumber] = React.useState('');

  const { data: stats, refetch } = useQuery({
    queryKey: ['userStats'],
    queryFn: userApi.getStats,
  });

  const { data: subscriptions } = useQuery({
    queryKey: ['userSubscriptions'],
    queryFn: userApi.getSubscriptions,
  });

  const handleDeposit = async () => {
    try {
      const amount = parseInt(depositAmount);
      if (amount > 0) {
        const { payment_url } = await userApi.depositToWallet(amount);
        window.location.href = payment_url;
      }
    } catch (error) {
      console.error('Error depositing:', error);
    }
  };

  const handleWithdraw = async () => {
    try {
      const amount = parseInt(withdrawAmount);
      if (amount > 0 && cardNumber) {
        await userApi.withdrawFromWallet(amount, cardNumber);
        setOpenWithdrawDialog(false);
        refetch();
      }
    } catch (error) {
      console.error('Error withdrawing:', error);
    }
  };

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
    action?: React.ReactNode;
  }> = ({ title, value, icon, color, action }) => (
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
        {action && (
          <Box mt={2} display="flex" justifyContent="flex-end">
            {action}
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const SubscriptionCard: React.FC<{
    subscription: any;
  }> = ({ subscription }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h6">{subscription.plan_name}</Typography>
            <Typography color="textSecondary">
              {subscription.status === 'active' ? t('Active') : t('Expired')}
            </Typography>
          </Box>
          <Box>
            <LinearProgress
              variant="determinate"
              value={(subscription.used_traffic / subscription.total_traffic) * 100}
              color={subscription.used_traffic / subscription.total_traffic > 0.8 ? 'error' : 'primary'}
              sx={{ mb: 1 }}
            />
            <Typography variant="body2" color="textSecondary">
              {formatBytes(subscription.used_traffic)} / {formatBytes(subscription.total_traffic)}
            </Typography>
          </Box>
        </Box>
        <Box mt={2} display="flex" gap={1}>
          <Button
            startIcon={<QrCodeIcon />}
            variant="outlined"
            size="small"
            onClick={() => window.open(subscription.qr_code, '_blank')}
          >
            {t('QR Code')}
          </Button>
          <Button
            startIcon={<ContentCopyIcon />}
            variant="outlined"
            size="small"
            onClick={() => {
              navigator.clipboard.writeText(subscription.config_url);
              // Show success message
            }}
          >
            {t('Copy Config')}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('User Dashboard')}</Typography>
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
            title={t('Wallet Balance')}
            value={formatNumber(stats?.wallet_balance || 0)}
            icon={<AccountBalanceIcon sx={{ color: '#1976d2' }} />}
            color="#1976d2"
            action={
              <Box display="flex" gap={1}>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => setOpenDepositDialog(true)}
                >
                  {t('Deposit')}
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => setOpenWithdrawDialog(true)}
                >
                  {t('Withdraw')}
                </Button>
              </Box>
            }
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Active Subscriptions')}
            value={stats?.active_subscriptions || 0}
            icon={<SpeedIcon sx={{ color: '#2e7d32' }} />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Total Traffic')}
            value={formatBytes(stats?.total_traffic || 0)}
            icon={<HistoryIcon sx={{ color: '#ed6c02' }} />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Remaining Traffic')}
            value={formatBytes(stats?.remaining_traffic || 0)}
            icon={<SpeedIcon sx={{ color: '#9c27b0' }} />}
            color="#9c27b0"
          />
        </Grid>

        {/* Active Subscriptions */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              {t('Active Subscriptions')}
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              {subscriptions?.map((subscription) => (
                <SubscriptionCard key={subscription.id} subscription={subscription} />
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
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
                  <NotificationsIcon color="action" />
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Deposit Dialog */}
      <Dialog open={openDepositDialog} onClose={() => setOpenDepositDialog(false)}>
        <DialogTitle>{t('Deposit to Wallet')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('Amount')}
            type="number"
            fullWidth
            value={depositAmount}
            onChange={(e) => setDepositAmount(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDepositDialog(false)}>{t('Cancel')}</Button>
          <Button onClick={handleDeposit} variant="contained" color="primary">
            {t('Deposit')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Withdraw Dialog */}
      <Dialog open={openWithdrawDialog} onClose={() => setOpenWithdrawDialog(false)}>
        <DialogTitle>{t('Withdraw from Wallet')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('Amount')}
            type="number"
            fullWidth
            value={withdrawAmount}
            onChange={(e) => setWithdrawAmount(e.target.value)}
          />
          <TextField
            margin="dense"
            label={t('Card Number')}
            fullWidth
            value={cardNumber}
            onChange={(e) => setCardNumber(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenWithdrawDialog(false)}>{t('Cancel')}</Button>
          <Button onClick={handleWithdraw} variant="contained" color="primary">
            {t('Withdraw')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserDashboard; 