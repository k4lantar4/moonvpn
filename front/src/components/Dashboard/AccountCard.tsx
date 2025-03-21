import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  IconButton,
  Tooltip,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import QrCodeIcon from '@mui/icons-material/QrCode';

// Example data - replace with actual API data
const accounts = [
  {
    id: 1,
    name: 'Account 1',
    status: 'active',
    expiryDate: '2024-04-01',
    trafficUsed: 25,
    trafficLimit: 50,
    configUrl: 'vmess://example.com',
  },
  {
    id: 2,
    name: 'Account 2',
    status: 'active',
    expiryDate: '2024-04-15',
    trafficUsed: 75,
    trafficLimit: 100,
    configUrl: 'vmess://example.com',
  },
];

const AccountCard: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.palette.success.main;
      case 'expired':
        return theme.palette.error.main;
      case 'suspended':
        return theme.palette.warning.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  return (
    <Grid container spacing={2}>
      {accounts.map((account) => (
        <Grid item xs={12} md={6} key={account.id}>
          <Card
            sx={{
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" sx={{ color: theme.palette.text.primary }}>
                  {account.name}
                </Typography>
                <Box>
                  <Tooltip title={t('dashboard.copy_config')}>
                    <IconButton
                      size="small"
                      onClick={() => copyToClipboard(account.configUrl)}
                    >
                      <ContentCopyIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('dashboard.show_qr')}>
                    <IconButton size="small">
                      <QrCodeIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('dashboard.refresh')}>
                    <IconButton size="small">
                      <RefreshIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: getStatusColor(account.status),
                    display: 'inline-block',
                    px: 1,
                    py: 0.5,
                    borderRadius: 1,
                    backgroundColor: `${getStatusColor(account.status)}20`,
                  }}
                >
                  {t(`dashboard.status.${account.status}`)}
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                  {t('dashboard.expiry_date')}: {new Date(account.expiryDate).toLocaleDateString('fa-IR')}
                </Typography>
              </Box>

              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                  {t('dashboard.traffic_usage')}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(account.trafficUsed / account.trafficLimit) * 100}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: theme.palette.background.default,
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: theme.palette.primary.main,
                    },
                  }}
                />
              </Box>

              <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                {account.trafficUsed} / {account.trafficLimit} GB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default AccountCard; 