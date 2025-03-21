import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  Link,
  Divider,
  InputAdornment,
  IconButton,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Checkbox,
  FormControlLabel,
  useTheme
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Lock as LockIcon,
  Email as EmailIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  Check as CheckIcon,
  HowToReg as HowToRegIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';

// Define step labels
const steps = ['اطلاعات حساب', 'اطلاعات شخصی', 'تأیید'];

const Register: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // Form state
  const [activeStep, setActiveStep] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  
  // Handle input changes
  const handleInputChange = (field: string, value: string) => {
    // Clear error for this field
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
    
    // Update the appropriate state
    switch (field) {
      case 'email':
        setEmail(value);
        break;
      case 'password':
        setPassword(value);
        break;
      case 'confirmPassword':
        setConfirmPassword(value);
        break;
      case 'fullName':
        setFullName(value);
        break;
      case 'phone':
        setPhone(value);
        break;
      case 'verificationCode':
        setVerificationCode(value);
        break;
    }
  };
  
  // Toggle password visibility
  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };
  
  // Handle terms checkbox
  const handleAgreeToTermsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAgreeToTerms(e.target.checked);
  };
  
  // Validate step one (account information)
  const validateStepOne = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Email validation
    if (!email) {
      newErrors.email = t('ایمیل الزامی است');
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = t('فرمت ایمیل نامعتبر است');
    }
    
    // Password validation
    if (!password) {
      newErrors.password = t('رمز عبور الزامی است');
    } else if (password.length < 8) {
      newErrors.password = t('رمز عبور باید حداقل ۸ کاراکتر باشد');
    }
    
    // Confirm password validation
    if (password !== confirmPassword) {
      newErrors.confirmPassword = t('تکرار رمز عبور مطابقت ندارد');
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // Validate step two (personal information)
  const validateStepTwo = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Full name validation
    if (!fullName) {
      newErrors.fullName = t('نام و نام خانوادگی الزامی است');
    }
    
    // Phone validation
    if (!phone) {
      newErrors.phone = t('شماره موبایل الزامی است');
    } else if (!/^(0|0098|\+98)9\d{9}$/.test(phone.replace(/\s+/g, ''))) {
      newErrors.phone = t('فرمت شماره موبایل نامعتبر است');
    }
    
    // Terms agreement validation
    if (!agreeToTerms) {
      newErrors.agreeToTerms = t('پذیرش قوانین و مقررات الزامی است');
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // Validate step three (verification)
  const validateStepThree = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Verification code validation
    if (!verificationCode) {
      newErrors.verificationCode = t('کد تأیید الزامی است');
    } else if (verificationCode.length !== 6) {
      newErrors.verificationCode = t('کد تأیید باید ۶ رقم باشد');
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // Handle next step
  const handleNext = () => {
    let isValid = false;
    
    switch (activeStep) {
      case 0:
        isValid = validateStepOne();
        break;
      case 1:
        isValid = validateStepTwo();
        if (isValid) {
          // In a real app, we would send a verification code here
          console.log('Sending verification code to:', phone);
        }
        break;
      case 2:
        isValid = validateStepThree();
        if (isValid) {
          handleRegister();
          return;
        }
        break;
    }
    
    if (isValid) {
      setActiveStep((prevStep) => prevStep + 1);
      setGeneralError(null);
    }
  };
  
  // Handle back step
  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
    setGeneralError(null);
  };
  
  // Handle registration submission
  const handleRegister = async () => {
    setLoading(true);
    
    try {
      // This would be replaced with an actual API call
      // For now, we're simulating a registration request
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // In a real app, we would send the registration data to the server
      console.log('Registration data:', {
        email,
        password,
        fullName,
        phone,
        agreeToTerms
      });
      
      // Navigate to success page or login
      // For this demo, we'll just move to a success view
      setActiveStep(3);
      
    } catch (err) {
      setGeneralError(t('خطا در ثبت‌نام. لطفاً دوباره تلاش کنید'));
      console.error('Registration error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Render step one content (account information)
  const renderStepOne = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('اطلاعات حساب کاربری')}
      </Typography>
      
      <TextField
        label={t('ایمیل')}
        type="email"
        value={email}
        onChange={(e) => handleInputChange('email', e.target.value)}
        fullWidth
        margin="normal"
        variant="outlined"
        error={!!errors.email}
        helperText={errors.email}
        autoComplete="email"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <EmailIcon />
            </InputAdornment>
          ),
        }}
      />
      
      <TextField
        label={t('رمز عبور')}
        type={showPassword ? 'text' : 'password'}
        value={password}
        onChange={(e) => handleInputChange('password', e.target.value)}
        fullWidth
        margin="normal"
        variant="outlined"
        error={!!errors.password}
        helperText={errors.password}
        autoComplete="new-password"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <LockIcon />
            </InputAdornment>
          ),
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                onClick={handleTogglePasswordVisibility}
                edge="end"
              >
                {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
      
      <TextField
        label={t('تکرار رمز عبور')}
        type={showPassword ? 'text' : 'password'}
        value={confirmPassword}
        onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
        fullWidth
        margin="normal"
        variant="outlined"
        error={!!errors.confirmPassword}
        helperText={errors.confirmPassword}
        autoComplete="new-password"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <LockIcon />
            </InputAdornment>
          ),
        }}
      />
    </Box>
  );
  
  // Render step two content (personal information)
  const renderStepTwo = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('اطلاعات شخصی')}
      </Typography>
      
      <TextField
        label={t('نام و نام خانوادگی')}
        value={fullName}
        onChange={(e) => handleInputChange('fullName', e.target.value)}
        fullWidth
        margin="normal"
        variant="outlined"
        error={!!errors.fullName}
        helperText={errors.fullName}
        autoComplete="name"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <PersonIcon />
            </InputAdornment>
          ),
        }}
      />
      
      <TextField
        label={t('شماره موبایل')}
        value={phone}
        onChange={(e) => handleInputChange('phone', e.target.value)}
        fullWidth
        margin="normal"
        variant="outlined"
        error={!!errors.phone}
        helperText={errors.phone}
        autoComplete="tel"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <PhoneIcon />
            </InputAdornment>
          ),
        }}
        placeholder="09..."
      />
      
      <FormControlLabel
        control={
          <Checkbox 
            checked={agreeToTerms}
            onChange={handleAgreeToTermsChange}
            color="primary"
          />
        }
        label={
          <Box component="span">
            {t('با ')}
            <Link href="/terms" target="_blank" underline="hover">
              {t('قوانین و مقررات')}
            </Link>
            {t(' موافقم')}
          </Box>
        }
        sx={{ mt: 2 }}
      />
      {errors.agreeToTerms && (
        <Typography color="error" variant="caption" paragraph>
          {errors.agreeToTerms}
        </Typography>
      )}
    </Box>
  );
  
  // Render step three content (verification)
  const renderStepThree = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('تأیید شماره موبایل')}
      </Typography>
      
      <Typography variant="body2" paragraph>
        {t('کد تأیید به شماره موبایل زیر ارسال شد:')}
      </Typography>
      
      <Typography variant="body1" fontWeight="bold" paragraph>
        {phone}
      </Typography>
      
      <TextField
        label={t('کد تأیید')}
        value={verificationCode}
        onChange={(e) => handleInputChange('verificationCode', e.target.value)}
        fullWidth
        margin="normal"
        variant="outlined"
        error={!!errors.verificationCode}
        helperText={errors.verificationCode}
        autoComplete="one-time-code"
        inputProps={{ maxLength: 6 }}
        placeholder="123456"
        sx={{ maxWidth: 250, mx: 'auto', display: 'block' }}
      />
      
      <Typography variant="body2" textAlign="center" sx={{ mt: 2 }}>
        {t('کد را دریافت نکردید؟')}{' '}
        <Link
          href="#"
          underline="hover"
          onClick={(e) => {
            e.preventDefault();
            console.log('Resending verification code to:', phone);
          }}
        >
          {t('ارسال مجدد')}
        </Link>
      </Typography>
    </Box>
  );
  
  // Render success content
  const renderSuccess = () => (
    <Box sx={{ textAlign: 'center' }}>
      <CheckIcon 
        color="success" 
        sx={{ fontSize: 60, mb: 2 }}
      />
      
      <Typography variant="h5" gutterBottom>
        {t('ثبت‌نام با موفقیت انجام شد')}
      </Typography>
      
      <Typography variant="body1" paragraph>
        {t('اکنون می‌توانید وارد حساب کاربری خود شوید و از خدمات سیستم استفاده کنید.')}
      </Typography>
      
      <Button
        variant="contained"
        color="primary"
        component={RouterLink}
        to="/auth/login"
        sx={{ mt: 2 }}
      >
        {t('ورود به حساب')}
      </Button>
    </Box>
  );
  
  // Get step content based on active step
  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return renderStepOne();
      case 1:
        return renderStepTwo();
      case 2:
        return renderStepThree();
      case 3:
        return renderSuccess();
      default:
        return 'Unknown step';
    }
  };
  
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        p: 2,
        bgcolor: theme.palette.background.default
      }}
    >
      <Paper
        elevation={4}
        sx={{
          p: 4,
          maxWidth: '550px',
          width: '100%',
          bgcolor: theme.palette.background.paper,
          borderRadius: 2
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            {activeStep === 3 ? t('ثبت‌نام موفق') : t('ایجاد حساب کاربری')}
          </Typography>
          {activeStep < 3 && (
            <Typography variant="body2" color="text.secondary">
              {t('برای استفاده از خدمات، حساب کاربری ایجاد کنید')}
            </Typography>
          )}
        </Box>
        
        {generalError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {generalError}
          </Alert>
        )}
        
        {activeStep < 3 && (
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{t(label)}</StepLabel>
              </Step>
            ))}
          </Stepper>
        )}
        
        {getStepContent(activeStep)}
        
        {activeStep < 3 && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button
              variant="outlined"
              disabled={activeStep === 0}
              onClick={handleBack}
              sx={{ visibility: activeStep === 0 ? 'hidden' : 'visible' }}
            >
              {t('بازگشت')}
            </Button>
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleNext}
              disabled={loading}
              startIcon={activeStep === 2 ? <HowToRegIcon /> : undefined}
            >
              {activeStep === 2
                ? (loading ? t('در حال ثبت‌نام...') : t('تأیید و ثبت‌نام'))
                : t('ادامه')}
            </Button>
          </Box>
        )}
        
        {activeStep < 3 && (
          <>
            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                {t('یا')}
              </Typography>
            </Divider>
            
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2">
                {t('قبلاً ثبت‌نام کرده‌اید؟')}{' '}
                <Link
                  component={RouterLink}
                  to="/auth/login"
                  variant="body2"
                  underline="hover"
                  color="primary"
                >
                  {t('ورود')}
                </Link>
              </Typography>
            </Box>
          </>
        )}
      </Paper>
    </Box>
  );
};

export default Register; 