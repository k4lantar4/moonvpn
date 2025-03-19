import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  Card,
  CardContent,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  InputAdornment,
  Divider,
  Alert,
  AlertTitle,
  Collapse,
  IconButton,
  Stack,
  useTheme
} from '@mui/material';
import {
  CreditCard as CardIcon,
  AccountBalanceWallet as WalletIcon,
  Payment as PaymentIcon,
  Close as CloseIcon,
  CheckCircleOutline as CheckIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Predefined amounts for quick selection
const predefinedAmounts = [
  { value: 100000, label: '۱۰۰,۰۰۰ تومان' },
  { value: 200000, label: '۲۰۰,۰۰۰ تومان' },
  { value: 500000, label: '۵۰۰,۰۰۰ تومان' },
  { value: 1000000, label: '۱,۰۰۰,۰۰۰ تومان' }
];

const WalletTopup: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // State
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<string>('card');
  const [alertOpen, setAlertOpen] = useState(false);
  const [step, setStep] = useState<number>(1);
  
  // Handle amount selection
  const handleAmountSelect = (amount: number) => {
    setSelectedAmount(amount);
    setCustomAmount('');
  };
  
  // Handle custom amount change
  const handleCustomAmountChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCustomAmount(event.target.value);
    setSelectedAmount(null);
  };
  
  // Handle payment method change
  const handlePaymentMethodChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPaymentMethod(event.target.value);
  };
  
  // Handle proceed to payment
  const handleProceedToPayment = () => {
    // In a real implementation, this would navigate to the appropriate payment method
    setStep(2);
    setAlertOpen(true);
  };
  
  // Handle close alert
  const handleCloseAlert = () => {
    setAlertOpen(false);
  };
  
  // Get the final amount to charge
  const getFinalAmount = (): number => {
    if (selectedAmount) {
      return selectedAmount;
    } else if (customAmount) {
      return parseInt(customAmount, 10) || 0;
    }
    return 0;
  };
  
  // Render step 1: Amount selection
  const renderAmountSelection = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('انتخاب مبلغ شارژ')}
      </Typography>
      
      <Divider sx={{ mb: 3 }} />
      
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {predefinedAmounts.map((amount) => (
          <Grid item xs={6} sm={3} key={amount.value}>
            <Card 
              sx={{ 
                cursor: 'pointer',
                border: selectedAmount === amount.value ? `2px solid ${theme.palette.primary.main}` : undefined,
                bgcolor: selectedAmount === amount.value ? `${theme.palette.primary.main}10` : undefined,
                '&:hover': {
                  boxShadow: 3
                },
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                p: 2
              }}
              onClick={() => handleAmountSelect(amount.value)}
            >
              <Typography variant="h6" align="center">
                {amount.label}
              </Typography>
              {selectedAmount === amount.value && (
                <CheckIcon color="primary" sx={{ mt: 1 }} />
              )}
            </Card>
          </Grid>
        ))}
      </Grid>
      
      <Typography variant="subtitle1" gutterBottom>
        {t('یا مبلغ دلخواه را وارد کنید:')}
      </Typography>
      
      <TextField
        label={t('مبلغ دلخواه (تومان)')}
        fullWidth
        value={customAmount}
        onChange={handleCustomAmountChange}
        sx={{ mb: 4 }}
        InputProps={{
          startAdornment: <InputAdornment position="start"><WalletIcon /></InputAdornment>,
        }}
        placeholder="مثال: 350000"
      />
      
      <Typography variant="subtitle1" gutterBottom>
        {t('انتخاب روش پرداخت:')}
      </Typography>
      
      <FormControl component="fieldset" sx={{ mb: 4 }}>
        <RadioGroup
          value={paymentMethod}
          onChange={handlePaymentMethodChange}
        >
          <Paper sx={{ mb: 2, p: 2, bgcolor: paymentMethod === 'card' ? `${theme.palette.primary.main}10` : undefined }}>
            <FormControlLabel 
              value="card" 
              control={<Radio />} 
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CardIcon sx={{ mr: 1 }} />
                  <Typography>{t('پرداخت کارت به کارت')}</Typography>
                </Box>
              } 
            />
          </Paper>
          
          <Paper sx={{ mb: 2, p: 2, bgcolor: paymentMethod === 'zarinpal' ? `${theme.palette.primary.main}10` : undefined }}>
            <FormControlLabel 
              value="zarinpal" 
              control={<Radio />} 
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <PaymentIcon sx={{ mr: 1 }} />
                  <Typography>{t('پرداخت آنلاین با زرین‌پال')}</Typography>
                </Box>
              } 
            />
          </Paper>
        </RadioGroup>
      </FormControl>
      
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleProceedToPayment}
          disabled={!((selectedAmount || customAmount) && paymentMethod)}
          startIcon={<ArrowForwardIcon />}
        >
          {t('ادامه')}
        </Button>
      </Box>
    </Box>
  );
  
  // Render step 2: Payment details (card payment as an example)
  const renderCardPaymentDetails = () => (
    <Box>
      <Collapse in={alertOpen}>
        <Alert 
          severity="info"
          action={
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={handleCloseAlert}
            >
              <CloseIcon fontSize="inherit" />
            </IconButton>
          }
          sx={{ mb: 3 }}
        >
          <AlertTitle>{t('تغییر روش پرداخت')}</AlertTitle>
          {t('برای تغییر روش پرداخت، می‌توانید به مرحله قبل بازگردید.')}
        </Alert>
      </Collapse>
      
      <Typography variant="h6" gutterBottom>
        {t('پرداخت کارت به کارت')}
      </Typography>
      
      <Divider sx={{ mb: 3 }} />
      
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>{t('راهنمای پرداخت')}</AlertTitle>
        {t('لطفاً مبلغ را به شماره کارت زیر واریز نموده و سپس اطلاعات پرداخت و تصویر رسید را وارد کنید.')}
      </Alert>
      
      <Paper sx={{ p: 3, mb: 3, bgcolor: theme.palette.background.default }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={9}>
            <Typography variant="body1" gutterBottom>
              {t('شماره کارت')}:
            </Typography>
            <Typography 
              variant="h5" 
              sx={{ 
                direction: 'ltr',
                display: 'inline-block'
              }}
            >
              6037-9975-9874-3611
            </Typography>
          </Grid>
          <Grid item xs={12} md={3} sx={{ textAlign: { xs: 'left', md: 'right' } }}>
            <Button
              variant="outlined"
              startIcon={<CardIcon />}
              onClick={() => navigator.clipboard.writeText('6037997598743611')}
            >
              {t('کپی شماره کارت')}
            </Button>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 2 }} />
        
        <Typography variant="body2">
          {t('بانک')}: ملی
        </Typography>
        <Typography variant="body2">
          {t('به نام')}: علی حسینی
        </Typography>
        <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
          {t('مبلغ قابل پرداخت')}: {getFinalAmount().toLocaleString()} {t('تومان')}
        </Typography>
      </Paper>
      
      <Stack direction="row" spacing={2} justifyContent="center">
        <Button
          variant="outlined"
          onClick={() => setStep(1)}
        >
          {t('بازگشت')}
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={() => window.location.href = '/payment/card'}
        >
          {t('ادامه با روش کارت به کارت')}
        </Button>
      </Stack>
    </Box>
  );
  
  return (
    <Box>
      {step === 1 && renderAmountSelection()}
      {step === 2 && renderCardPaymentDetails()}
    </Box>
  );
};

export default WalletTopup; 