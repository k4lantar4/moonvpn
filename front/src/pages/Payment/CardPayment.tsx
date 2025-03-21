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
  useTheme
} from '@mui/material';
import {
  CreditCard as CardIcon,
  CloudUpload as UploadIcon,
  Check as CheckIcon,
  FileCopy as CopyIcon,
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
const steps = ['انتخاب اشتراک', 'اطلاعات پرداخت', 'آپلود رسید', 'تایید پرداخت'];

const CardPayment: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // State for stepper
  const [activeStep, setActiveStep] = useState(0);
  
  // State for form data
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null);
  const [cardNumber, setCardNumber] = useState('');
  const [cardHolder, setCardHolder] = useState('');
  const [amount, setAmount] = useState('');
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [receiptPreview, setReceiptPreview] = useState<string | null>(null);
  const [transactionId, setTransactionId] = useState('');
  const [paymentDate, setPaymentDate] = useState('');
  const [notes, setNotes] = useState('');
  
  // Handle plan selection
  const handlePlanSelect = (planId: number) => {
    setSelectedPlan(planId);
    const plan = plansData.find(p => p.id === planId);
    if (plan) {
      setAmount(plan.price.toString());
    }
  };
  
  // Handle file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setReceiptFile(file);
      
      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        setReceiptPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };
  
  // Handle form submission
  const handleSubmit = () => {
    // Logic to submit payment would go here
    console.log('Submitting payment:', {
      selectedPlan,
      cardNumber,
      cardHolder,
      amount,
      transactionId,
      paymentDate,
      notes,
      receiptFile
    });
    
    // Move to the next step
    handleNext();
  };
  
  // Copy card number to clipboard
  const handleCopyCardNumber = () => {
    navigator.clipboard.writeText('6037997598743611');
  };
  
  // Handle back/next navigation
  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };
  
  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
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
      
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleNext}
          disabled={!selectedPlan}
        >
          {t('ادامه')}
        </Button>
      </Box>
    </Box>
  );
  
  // Step 2: Payment Information
  const renderPaymentInfo = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('اطلاعات پرداخت')}
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
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
              startIcon={<CopyIcon />}
              onClick={handleCopyCardNumber}
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
          {t('مبلغ قابل پرداخت')}: {Number(amount).toLocaleString()} {t('تومان')}
        </Typography>
      </Paper>
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            label={t('شماره کارت پرداخت‌کننده')}
            fullWidth
            value={cardNumber}
            onChange={(e) => setCardNumber(e.target.value)}
            placeholder="مثال: 6037-9975-9874-1234"
            sx={{ mb: 2 }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            label={t('نام پرداخت‌کننده')}
            fullWidth
            value={cardHolder}
            onChange={(e) => setCardHolder(e.target.value)}
            placeholder="مثال: محمد محمدی"
            sx={{ mb: 2 }}
          />
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={handleBack}>
          {t('بازگشت')}
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={handleNext}
          disabled={!cardNumber || !cardHolder}
        >
          {t('ادامه و آپلود رسید')}
        </Button>
      </Box>
    </Box>
  );
  
  // Step 3: Receipt Upload
  const renderReceiptUpload = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('آپلود رسید پرداخت')}
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      <Alert severity="warning" sx={{ mb: 3 }}>
        <AlertTitle>{t('توجه')}</AlertTitle>
        {t('تصویر رسید باید واضح و خوانا باشد. لطفاً تصویری آپلود کنید که تمام اطلاعات پرداخت در آن مشخص باشد.')}
      </Alert>
      
      <Paper
        sx={{
          p: 3,
          mb: 3,
          bgcolor: theme.palette.background.default,
          border: '2px dashed',
          borderColor: 'divider',
          textAlign: 'center'
        }}
      >
        <input
          accept="image/*"
          style={{ display: 'none' }}
          id="receipt-upload"
          type="file"
          onChange={handleFileUpload}
        />
        <label htmlFor="receipt-upload">
          <Button
            variant="contained"
            component="span"
            startIcon={<UploadIcon />}
            sx={{ mb: 2 }}
          >
            {t('انتخاب تصویر رسید')}
          </Button>
        </label>
        
        <Box sx={{ mt: 2 }}>
          {receiptPreview ? (
            <Box>
              <Typography variant="body2" gutterBottom>
                {t('پیش‌نمایش تصویر رسید')}:
              </Typography>
              <Box
                component="img"
                src={receiptPreview}
                alt="Receipt Preview"
                sx={{
                  maxWidth: '100%',
                  maxHeight: '200px',
                  objectFit: 'contain',
                  mt: 1
                }}
              />
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t('هیچ تصویری انتخاب نشده است.')}
            </Typography>
          )}
        </Box>
      </Paper>
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            label={t('شناسه پیگیری تراکنش')}
            fullWidth
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            placeholder="مثال: 123456789"
            sx={{ mb: 2 }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            label={t('تاریخ و زمان پرداخت')}
            fullWidth
            value={paymentDate}
            onChange={(e) => setPaymentDate(e.target.value)}
            placeholder="مثال: 1402/06/25 14:30"
            sx={{ mb: 2 }}
          />
        </Grid>
      </Grid>
      
      <TextField
        label={t('توضیحات (اختیاری)')}
        fullWidth
        multiline
        rows={3}
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        sx={{ mb: 2 }}
      />
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={handleBack}>
          {t('بازگشت')}
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={!receiptFile || !transactionId || !paymentDate}
        >
          {t('ثبت پرداخت')}
        </Button>
      </Box>
    </Box>
  );
  
  // Step 4: Payment Confirmation
  const renderPaymentConfirmation = () => (
    <Box sx={{ textAlign: 'center' }}>
      <CheckIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
      
      <Typography variant="h5" gutterBottom>
        {t('پرداخت شما با موفقیت ثبت شد')}
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        {t('پرداخت شما به زودی بررسی و تایید خواهد شد. روند بررسی معمولاً بین 10 دقیقه تا 1 ساعت طول می‌کشد.')}
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3, textAlign: 'left' }}>
        <AlertTitle>{t('اطلاعات پرداخت')}</AlertTitle>
        <Typography variant="body2">
          {t('مبلغ')}: {Number(amount).toLocaleString()} {t('تومان')}
        </Typography>
        <Typography variant="body2">
          {t('شناسه پیگیری')}: {transactionId}
        </Typography>
        <Typography variant="body2">
          {t('تاریخ و زمان')}: {paymentDate}
        </Typography>
      </Alert>
      
      <Button
        variant="contained"
        color="primary"
        startIcon={<ReceiptIcon />}
      >
        {t('مشاهده فاکتور')}
      </Button>
    </Box>
  );
  
  // Render the current step
  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return renderPlanSelection();
      case 1:
        return renderPaymentInfo();
      case 2:
        return renderReceiptUpload();
      case 3:
        return renderPaymentConfirmation();
      default:
        return 'Unknown step';
    }
  };
  
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {t('پرداخت کارت به کارت')}
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

export default CardPayment; 