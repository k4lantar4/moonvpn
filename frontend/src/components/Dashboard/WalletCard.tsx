import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import AddIcon from '@mui/icons-material/Add';
import SendIcon from '@mui/icons-material/Send';

const WalletCard: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();

  // TODO: Replace with actual wallet data from API
  const walletBalance = 100000; // Example balance in Tomans

  return (
    <Paper
      sx={{
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        height: 240,
        background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
        color: theme.palette.primary.contrastText,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <AccountBalanceWalletIcon sx={{ mr: 1 }} />
        <Typography variant="h6">
          {t('dashboard.wallet')}
        </Typography>
      </Box>

      <Typography variant="h4" sx={{ mb: 2 }}>
        {new Intl.NumberFormat('fa-IR').format(walletBalance)} {t('currency.toman')}
      </Typography>

      <Stack direction="row" spacing={1} sx={{ mt: 'auto' }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.3)',
            },
          }}
        >
          {t('dashboard.add_funds')}
        </Button>
        <Button
          variant="contained"
          startIcon={<SendIcon />}
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.3)',
            },
          }}
        >
          {t('dashboard.withdraw')}
        </Button>
      </Stack>
    </Paper>
  );
};

export default WalletCard; 