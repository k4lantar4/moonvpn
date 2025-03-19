import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Link,
  Divider,
  InputAdornment,
  IconButton,
  Alert,
  Stepper,
  Step,
  StepLabel,
  useTheme
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Lock as LockIcon,
  Email as EmailIcon,
  Key as KeyIcon,
  ArrowBack as ArrowBackIcon,
  Check as CheckIcon,
  MarkEmailRead as MarkEmailReadIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';

// Define step labels
const steps = ['درخواست بازیابی', 'تأیید کد', 'رمز عبور جدید'];

const ForgotPassword: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // Form state
  const [activeStep, setActiveStep] = useState(0);
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Handle input changes
  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setError(null);
  };
  
  const handleVerificationCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setVerificationCode(e.target.value);
    setError(null);
  };
  
  const handleNewPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewPassword(e.target.value);
    setError(null);
  };
  
  const handleConfirmPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(e.target.value);
    setError(null);
  };
  
  // Toggle password visibility
  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };
  
  // Handle request reset password
  const handleRequestReset = async () => {
    // Basic validation
    if (!email) {
      setError(t('لطفاً ایمیل خود را وارد کنید'));
      return;
    }
    
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError(t('فرمت ایمیل نامعتبر است'));
      return;
    }
    
    setLoading(true);
    
    try {
      // This would be replaced with an actual API call
      // For now, we're simulating an API request
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Log the action (in a real app, this would be an API call)
      console.log('Reset password requested for:', email);
      
      // Move to the next step
      setActiveStep(1);
      setError(null);
    } catch (err) {
      setError(t('خطا در ارسال درخواست. لطفاً دوباره تلاش کنید'));
      console.error('Request reset error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle verify code
  const handleVerifyCode = async () => {
    // Basic validation
    if (!verificationCode) {
      setError(t('لطفاً کد تأیید را وارد کنید'));
      return;
    }
    
    if (verificationCode.length !== 6) {
      setError(t('کد تأیید باید ۶ رقم باشد'));
      return;
    }
    
    setLoading(true);
    
    try {
      // This would be replaced with an actual API call
      // For now, we're simulating an API request
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Log the action (in a real app, this would be an API call)
      console.log('Verifying code:', verificationCode, 'for email:', email);
      
      // Simulate verification success (in a real app, we would check the response)
      if (verificationCode === '123456') {
        // Move to the next step
        setActiveStep(2);
        setError(null);
      } else {
        setError(t('کد تأیید نامعتبر است'));
      }
    } catch (err) {
      setError(t('خطا در تأیید کد. لطفاً دوباره تلاش کنید'));
      console.error('Verify code error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle reset password
  const handleResetPassword = async () => {
    // Basic validation
    if (!newPassword) {
      setError(t('لطفاً رمز عبور جدید را وارد کنید'));
      return;
    }
    
    if (newPassword.length < 8) {
      setError(t('رمز عبور باید حداقل ۸ کاراکتر باشد'));
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setError(t('تکرار رمز عبور مطابقت ندارد'));
      return;
    }
    
    setLoading(true);
    
    try {
      // This would be replaced with an actual API call
      // For now, we're simulating an API request
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Log the action (in a real app, this would be an API call)
      console.log('Resetting password for email:', email);
      
      // Move to the success step
      setActiveStep(3);
      setError(null);
    } catch (err) {
      setError(t('خطا در بازنشانی رمز عبور. لطفاً دوباره تلاش کنید'));
      console.error('Reset password error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle back step
  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
    setError(null);
  };
  
  // Handle next step (based on current step)
  const handleNext = () => {
    switch (activeStep) {
      case 0:
        handleRequestReset();
        break;
      case 1:
        handleVerifyCode();
        break;
      case 2:
        handleResetPassword();
        break;
    }
  };
  
  // Render step one content (request reset)
  const renderRequestReset = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('درخواست بازیابی رمز عبور')}
      </Typography>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        {t('ایمیل خود را وارد کنید تا کد بازیابی برای شما ارسال شود.')}
      </Typography>
      
      <TextField
        label={t('ایمیل')}
        type="email"
        value={email}
        onChange={handleEmailChange}
        fullWidth
        margin="normal"
        variant="outlined"
        autoComplete="email"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <EmailIcon />
            </InputAdornment>
          ),
        }}
      />
    </Box>
  );
  
  // Render step two content (verify code)
  const renderVerifyCode = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('تأیید کد')}
      </Typography>
      
      <Typography variant="body2" paragraph>
        {t('کد ارسال شده به ایمیل زیر را وارد کنید:')}
      </Typography>
      
      <Typography variant="body1" fontWeight="bold" paragraph>
        {email}
      </Typography>
      
      <TextField
        label={t('کد تأیید')}
        value={verificationCode}
        onChange={handleVerificationCodeChange}
        fullWidth
        margin="normal"
        variant="outlined"
        autoComplete="one-time-code"
        inputProps={{ maxLength: 6 }}
        placeholder="123456"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <KeyIcon />
            </InputAdornment>
          ),
        }}
      />
      
      <Typography variant="body2" sx={{ mt: 2 }}>
        {t('کد را دریافت نکردید؟')}{' '}
        <Link
          href="#"
          underline="hover"
          onClick={(e) => {
            e.preventDefault();
            console.log('Resending verification code to:', email);
          }}
        >
          {t('ارسال مجدد')}
        </Link>
      </Typography>
    </Box>
  );
  
  // Render step three content (reset password)
  const renderResetPassword = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('تعیین رمز عبور جدید')}
      </Typography>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        {t('رمز عبور جدید را وارد کنید.')}
      </Typography>
      
      <TextField
        label={t('رمز عبور جدید')}
        type={showPassword ? 'text' : 'password'}
        value={newPassword}
        onChange={handleNewPasswordChange}
        fullWidth
        margin="normal"
        variant="outlined"
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
        label={t('تکرار رمز عبور جدید')}
        type={showPassword ? 'text' : 'password'}
        value={confirmPassword}
        onChange={handleConfirmPasswordChange}
        fullWidth
        margin="normal"
        variant="outlined"
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
  
  // Render success content
  const renderSuccess = () => (
    <Box sx={{ textAlign: 'center' }}>
      <CheckIcon 
        color="success" 
        sx={{ fontSize: 60, mb: 2 }}
      />
      
      <Typography variant="h5" gutterBottom>
        {t('رمز عبور با موفقیت بازنشانی شد')}
      </Typography>
      
      <Typography variant="body1" paragraph>
        {t('اکنون می‌توانید با رمز عبور جدید وارد حساب کاربری خود شوید.')}
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
        return renderRequestReset();
      case 1:
        return renderVerifyCode();
      case 2:
        return renderResetPassword();
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
          maxWidth: '500px',
          width: '100%',
          bgcolor: theme.palette.background.paper,
          borderRadius: 2
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            {activeStep === 3 ? t('بازنشانی موفق') : t('بازیابی رمز عبور')}
          </Typography>
          {activeStep < 3 && (
            <Typography variant="body2" color="text.secondary">
              {t('در چند مرحله ساده رمز عبور خود را بازیابی کنید')}
            </Typography>
          )}
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
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
              startIcon={<ArrowBackIcon />}
              sx={{ visibility: activeStep === 0 ? 'hidden' : 'visible' }}
            >
              {t('بازگشت')}
            </Button>
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleNext}
              disabled={loading}
              startIcon={activeStep === 0 ? <MarkEmailReadIcon /> : undefined}
            >
              {loading
                ? t('لطفاً صبر کنید...')
                : (activeStep === 0
                  ? t('ارسال کد')
                  : (activeStep === 1
                    ? t('تأیید کد')
                    : t('بازنشانی رمز عبور')))}
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
                {t('رمز عبور خود را به یاد آوردید؟')}{' '}
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

export default ForgotPassword; 