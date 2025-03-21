import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  Stepper,
  Step,
  StepLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Alert,
  AlertTitle,
  Divider,
  CircularProgress,
  useTheme
} from '@mui/material';
import {
  Payment as PaymentIcon,
  ShoppingCart as CartIcon,
  Check as CheckIcon,
  MonetizationOn as MoneyIcon,
  Receipt as ReceiptIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Example plans data for subscription selection
const plansData = [
  { id: 1, name: 'اشتراک ماهانه', price: 250000, duration: '1 ماه', traffic: '50 گیگابایت' },
  { id: 2, name: 'اشتراک سه ماهه', price: 650000, duration: '3 ماه', traffic: '150 گیگابایت' },
  { id: 3, name: 'اشتراک شش ماهه', price: 1200000, duration: '6 ماه', traffic: '300 گیگابایت' },
  { id: 4, name: 'اشتراک سالانه', price: 2000000, duration: '12 ماه', traffic: '600 گیگابایت' }
];

// Steps for the payment process
const steps = ['انتخاب اشتراک', 'پرداخت آنلاین', 'تکمیل خرید'];

const ZarinpalPayment: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // State for stepper
  const [activeStep, setActiveStep] = useState(0);
  
  // State for form data
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null);
  const [email, setEmail] = useState('');
  const [mobile, setMobile] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [paymentUrl, setPaymentUrl] = useState('');
  const [transactionId, setTransactionId] = useState('');
  const [paymentComplete, setPaymentComplete] = useState(false);
  
  // Handle plan selection
  const handlePlanSelect = (planId: number) => {
    setSelectedPlan(planId);
    const plan = plansData.find(p => p.id === planId);
    if (plan) {
      setAmount(plan.price.toString());
      setDescription(`خرید ${plan.name} - ${plan.traffic} - ${plan.duration}`);
    }
  };
  
  // Initialize payment with Zarinpal
  const handleInitiatePayment = () => {
    setLoading(true);
    
    // Simulate API call to get payment URL from Zarinpal
    setTimeout(() => {
      // Normally this would be an API call to your backend, which would then call Zarinpal API
      // Example request to Zarinpal:
      // POST https://api.zarinpal.com/pg/v4/payment/request.json
      // {
      //   "merchant_id": "YOUR_MERCHANT_ID",
      //   "amount": amount,
      //   "callback_url": "https://www.yourwebsite.com/verify",
      //   "description": description,
      //   "metadata": { "mobile": mobile, "email": email }
      // }
      
      setPaymentUrl('https://www.zarinpal.com/pg/StartPay/00000000-0000-0000-0000-000000000000');
      setTransactionId('A' + Math.floor(Math.random() * 1000000000));
      setLoading(false);
      
      // In a real implementation, you would redirect to the payment URL
      setActiveStep(1);
    }, 2000);
  };
  
  // Verify payment (this would be called when the user is redirected back from Zarinpal)
  const handleVerifyPayment = () => {
    setLoading(true);
    
    // Simulate API call to verify payment
    setTimeout(() => {
      // Normally this would be an API call to your backend, which would then call Zarinpal API
      // Example request to Zarinpal:
      // POST https://api.zarinpal.com/pg/v4/payment/verify.json
      // {
      //   "merchant_id": "YOUR_MERCHANT_ID",
      //   "amount": amount,
      //   "authority": "AUTHORITY_FROM_QUERY_STRING"
      // }
      
      setPaymentComplete(true);
      setLoading(false);
      setActiveStep(2);
    }, 2000);
  };
  
  // Step 1: Plan Selection
  const renderPlanSelection = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('انتخاب اشتراک')}
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      <Grid container spacing={2}>
        {plansData.map((plan) => (
          <Grid item xs={12} sm={6} md={3} key={plan.id}>
            <Card 
              sx={{ 
                cursor: 'pointer',
                border: selectedPlan === plan.id ? `2px solid ${theme.palette.primary.main}` : undefined,
                bgcolor: selectedPlan === plan.id ? `${theme.palette.primary.main}10` : undefined,
                '&:hover': {
                  boxShadow: 3
                }
              }}
              onClick={() => handlePlanSelect(plan.id)}
            >
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {plan.name}
                </Typography>
                <Typography variant="h5" color="primary" gutterBottom>
                  {plan.price.toLocaleString()} {t('تومان')}
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2">
                  {t('مدت')}: {plan.duration}
                </Typography>
                <Typography variant="body2">
                  {t('ترافیک')}: {plan.traffic}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      <Alert severity="info" sx={{ mt: 3, mb: 3 }}>
        <AlertTitle>{t('اطلاعات پرداخت')}</AlertTitle>
        {t('لطفاً برای انجام پرداخت از طریق درگاه زرین‌پال، اطلاعات زیر را تکمیل کنید.')}
      </Alert>
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            label={t('ایمیل (اختیاری)')}
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="example@example.com"
            sx={{ mb: 2 }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            label={t('شماره موبایل')}
            fullWidth
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            placeholder="09123456789"
            sx={{ mb: 2 }}
          />
        </Grid>
      </Grid>
      
      <TextField
        label={t('توضیحات (اختیاری)')}
        fullWidth
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        sx={{ mb: 3 }}
      />
      
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleInitiatePayment}
          disabled={!selectedPlan || !mobile || loading}
          startIcon={loading ? <CircularProgress size={20} /> : <PaymentIcon />}
        >
          {loading ? t('در حال اتصال به درگاه...') : t('پرداخت با زرین‌پال')}
        </Button>
      </Box>
    </Box>
  );
  
  // Step 2: Payment Gateway
  const renderPaymentGateway = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('پرداخت آنلاین')}
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>{t('هدایت به درگاه پرداخت')}</AlertTitle>
        {t('در حالت واقعی، شما به صورت خودکار به درگاه زرین‌پال هدایت می‌شوید. برای شبیه‌سازی فرآیند، لطفاً روی دکمه زیر کلیک کنید.')}
      </Alert>
      
      <Paper sx={{ p: 3, mb: 3, bgcolor: theme.palette.background.default }}>
        <Typography variant="body1" gutterBottom>
          {t('مبلغ قابل پرداخت')}: <strong>{Number(amount).toLocaleString()} {t('تومان')}</strong>
        </Typography>
        <Typography variant="body1" gutterBottom>
          {t('کد پیگیری')}: <strong>{transactionId}</strong>
        </Typography>
        <Typography variant="body1" sx={{ direction: 'ltr', textAlign: 'left' }}>
          {t('آدرس پرداخت')}: <a href={paymentUrl} target="_blank" rel="noopener noreferrer">{paymentUrl}</a>
        </Typography>
      </Paper>
      
      <Box sx={{ textAlign: 'center' }}>
        <img 
          src="https://www.zarinpal.com/assets/images/logo-white.svg" 
          alt="Zarinpal" 
          style={{ 
            width: 150, 
            height: 'auto',
            filter: 'brightness(0.8)',
            marginBottom: 16
          }} 
        />
        
        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={handleVerifyPayment}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <CartIcon />}
            sx={{ mr: 2 }}
          >
            {loading ? t('در حال بررسی...') : t('شبیه‌سازی تکمیل پرداخت')}
          </Button>
          <Button 
            variant="outlined" 
            onClick={() => setActiveStep(0)}
          >
            {t('انصراف')}
          </Button>
        </Box>
      </Box>
    </Box>
  );
  
  // Step 3: Payment Confirmation
  const renderPaymentConfirmation = () => (
    <Box sx={{ textAlign: 'center' }}>
      <CheckIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
      
      <Typography variant="h5" gutterBottom>
        {t('پرداخت شما با موفقیت انجام شد')}
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        {t('اشتراک شما با موفقیت فعال شد و می‌توانید هم‌اکنون از خدمات استفاده کنید.')}
      </Typography>
      
      <Alert severity="success" sx={{ mb: 3, textAlign: 'left' }}>
        <AlertTitle>{t('اطلاعات پرداخت')}</AlertTitle>
        <Typography variant="body2">
          {t('مبلغ')}: {Number(amount).toLocaleString()} {t('تومان')}
        </Typography>
        <Typography variant="body2">
          {t('کد پیگیری زرین‌پال')}: {transactionId}
        </Typography>
        <Typography variant="body2">
          {t('وضعیت')}: {t('پرداخت شده')}
        </Typography>
      </Alert>
      
      <Grid container spacing={2} justifyContent="center">
        <Grid item>
          <Button
            variant="contained"
            color="primary"
            startIcon={<ReceiptIcon />}
          >
            {t('مشاهده فاکتور')}
          </Button>
        </Grid>
        <Grid item>
          <Button
            variant="outlined"
            startIcon={<MoneyIcon />}
            onClick={() => {
              setActiveStep(0);
              setSelectedPlan(null);
              setEmail('');
              setMobile('');
              setDescription('');
              setAmount('');
              setPaymentComplete(false);
              setTransactionId('');
            }}
          >
            {t('پرداخت جدید')}
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
  
  // Render the current step
  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return renderPlanSelection();
      case 1:
        return renderPaymentGateway();
      case 2:
        return renderPaymentConfirmation();
      default:
        return 'Unknown step';
    }
  };
  
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {t('پرداخت آنلاین با زرین‌پال')}
      </Typography>
      
      <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{t(label)}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      <Paper sx={{ p: 3, bgcolor: theme.palette.background.paper }}>
        {getStepContent(activeStep)}
      </Paper>
    </Box>
  );
};

export default ZarinpalPayment; 