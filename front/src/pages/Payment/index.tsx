import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  Card,
  CardContent,
  Grid,
  Button,
  Divider,
  useTheme
} from '@mui/material';
import {
  AccountBalanceWallet as WalletIcon,
  CreditCard as CardIcon,
  Payment as PaymentIcon,
  Receipt as ReceiptIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Import payment components
import WalletTopup from './WalletTopup';
import CardPayment from './CardPayment';
import ZarinpalPayment from './ZarinpalPayment';
import PaymentHistory from './PaymentHistory';

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
      id={`payment-tabpanel-${index}`}
      aria-labelledby={`payment-tab-${index}`}
      {...other}
      style={{ width: '100%' }}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

// Wallet summary component
const WalletSummary = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // Example wallet data
  const walletData = {
    balance: 250000,
    lastDeposit: {
      amount: 100000,
      date: '1402/06/20',
      method: 'zarinpal'
    },
    pendingTransactions: 1
  };
  
  return (
    <Card sx={{ mb: 3, bgcolor: theme.palette.background.paper }}>
      <CardContent>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <WalletIcon sx={{ fontSize: 40, color: theme.palette.primary.main }} />
          </Grid>
          <Grid item xs>
            <Typography variant="h5" gutterBottom>
              {t('کیف پول شما')}
            </Typography>
            <Typography variant="h4" sx={{ color: theme.palette.primary.main }}>
              {walletData.balance.toLocaleString()} {t('تومان')}
            </Typography>
          </Grid>
          <Grid item>
            <Button 
              variant="contained" 
              color="primary"
              startIcon={<WalletIcon />}
            >
              {t('افزایش موجودی')}
            </Button>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 2 }} />
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              {t('آخرین واریز')}:
            </Typography>
            <Typography variant="body1">
              {walletData.lastDeposit.amount.toLocaleString()} {t('تومان')} - {walletData.lastDeposit.date}
              {walletData.lastDeposit.method === 'zarinpal' && ` (${t('زرین‌پال')})`}
              {walletData.lastDeposit.method === 'card' && ` (${t('کارت به کارت')})`}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              {t('تراکنش‌های در انتظار')}:
            </Typography>
            <Typography variant="body1">
              {walletData.pendingTransactions} {t('مورد')}
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// Main Payment component
const Payment: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {t('پرداخت و کیف پول')}
      </Typography>
      
      {/* Wallet Summary */}
      <WalletSummary />
      
      {/* Payment Tabs */}
      <Paper sx={{ mb: 3, bgcolor: theme.palette.background.paper }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<WalletIcon />} label={t('افزایش موجودی')} iconPosition="start" />
          <Tab icon={<CardIcon />} label={t('پرداخت کارت به کارت')} iconPosition="start" />
          <Tab icon={<PaymentIcon />} label={t('پرداخت آنلاین')} iconPosition="start" />
          <Tab icon={<HistoryIcon />} label={t('تاریخچه پرداخت‌ها')} iconPosition="start" />
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          <WalletTopup />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <CardPayment />
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <ZarinpalPayment />
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          <PaymentHistory />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Payment; 