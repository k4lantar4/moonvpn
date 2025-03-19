import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Checkbox,
  FormControlLabel,
  Paper,
  Link,
  Divider,
  InputAdornment,
  IconButton,
  Alert,
  useTheme,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Login as LoginIcon,
  Lock as LockIcon,
  Email as EmailIcon,
  Google as GoogleIcon,
  GitHub as GitHubIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink, useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Handle input changes
  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setError(null);
  };
  
  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
    setError(null);
  };
  
  const handleRememberMeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRememberMe(e.target.checked);
  };
  
  // Toggle password visibility
  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!email || !password) {
      setError(t('لطفاً ایمیل و رمز عبور را وارد کنید'));
      return;
    }
    
    setLoading(true);
    
    try {
      // This would be replaced with an actual API call
      // For now, we're simulating an API request
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate authentication (in a real app, we would check credentials)
      if (email === 'test@example.com' && password === 'password123') {
        // Log the successful login
        console.log('User logged in:', email, 'Remember me:', rememberMe);
        
        // Redirect to dashboard
        navigate('/dashboard');
      } else {
        // Simulate authentication failure
        throw new Error('Invalid credentials');
      }
    } catch (err) {
      setError(t('ایمیل یا رمز عبور اشتباه است'));
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle social login
  const handleSocialLogin = (provider: string) => {
    console.log(`Login with ${provider}`);
    // In a real app, this would initiate OAuth flow with the provider
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
          maxWidth: '450px',
          width: '100%',
          bgcolor: theme.palette.background.paper,
          borderRadius: 2
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            {t('ورود به حساب کاربری')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('خوش آمدید! لطفاً اطلاعات خود را وارد کنید')}
          </Typography>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            label={t('ایمیل')}
            type="email"
            value={email}
            onChange={handleEmailChange}
            fullWidth
            margin="normal"
            variant="outlined"
            autoComplete="email"
            autoFocus
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
            onChange={handlePasswordChange}
            fullWidth
            margin="normal"
            variant="outlined"
            autoComplete="current-password"
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
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', my: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={rememberMe}
                  onChange={handleRememberMeChange}
                  color="primary"
                />
              }
              label={<Typography variant="body2">{t('مرا به خاطر بسپار')}</Typography>}
            />
            
            <Link
              component={RouterLink}
              to="/auth/forgot-password"
              variant="body2"
              underline="hover"
              color="primary"
            >
              {t('فراموشی رمز عبور')}
            </Link>
          </Box>
          
          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            size="large"
            disabled={loading}
            startIcon={<LoginIcon />}
            sx={{ mt: 2, mb: 3 }}
          >
            {loading ? t('در حال ورود...') : t('ورود')}
          </Button>
        </Box>
        
        <Divider sx={{ my: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {t('یا')}
          </Typography>
        </Divider>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 3 }}>
          <Button
            variant="outlined"
            onClick={() => handleSocialLogin('Google')}
            startIcon={<GoogleIcon />}
            sx={{ flex: 1 }}
          >
            {t('گوگل')}
          </Button>
          
          <Button
            variant="outlined"
            onClick={() => handleSocialLogin('GitHub')}
            startIcon={<GitHubIcon />}
            sx={{ flex: 1 }}
          >
            {t('گیت‌هاب')}
          </Button>
        </Box>
        
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2">
            {t('حساب کاربری ندارید؟')}{' '}
            <Link
              component={RouterLink}
              to="/auth/register"
              variant="body2"
              underline="hover"
              color="primary"
            >
              {t('ثبت نام')}
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default Login; 