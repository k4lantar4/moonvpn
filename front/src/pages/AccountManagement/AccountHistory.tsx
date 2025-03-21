import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';

// Example data - replace with actual API data
const history = [
  {
    id: 1,
    date: '2024-03-15',
    type: 'create',
    accountName: 'Account 1',
    plan: 'Basic',
    amount: 100000,
    status: 'completed',
  },
  {
    id: 2,
    date: '2024-03-10',
    type: 'renew',
    accountName: 'Account 2',
    plan: 'Premium',
    amount: 180000,
    status: 'completed',
  },
  {
    id: 3,
    date: '2024-03-05',
    type: 'delete',
    accountName: 'Account 3',
    plan: 'Basic',
    amount: 0,
    status: 'completed',
  },
];

const AccountHistory: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return theme.palette.success.main;
      case 'pending':
        return theme.palette.warning.main;
      case 'failed':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const getTypeText = (type: string) => {
    switch (type) {
      case 'create':
        return t('account_management.history.create');
      case 'renew':
        return t('account_management.history.renew');
      case 'delete':
        return t('account_management.history.delete');
      default:
        return type;
    }
  };

  return (
    <Box>
      <Card
        sx={{
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
        }}
      >
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3, color: theme.palette.text.primary }}>
            {t('account_management.account_history')}
          </Typography>

          <TableContainer component={Paper} sx={{ backgroundColor: 'transparent' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('account_management.history.date')}</TableCell>
                  <TableCell>{t('account_management.history.type')}</TableCell>
                  <TableCell>{t('account_management.history.account')}</TableCell>
                  <TableCell>{t('account_management.history.plan')}</TableCell>
                  <TableCell align="right">{t('account_management.history.amount')}</TableCell>
                  <TableCell>{t('account_management.history.status')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      {new Date(item.date).toLocaleDateString('fa-IR')}
                    </TableCell>
                    <TableCell>{getTypeText(item.type)}</TableCell>
                    <TableCell>{item.accountName}</TableCell>
                    <TableCell>{item.plan}</TableCell>
                    <TableCell align="right">
                      {item.amount > 0 ? `${item.amount.toLocaleString('fa-IR')} تومان` : '-'}
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{
                          color: getStatusColor(item.status),
                          display: 'inline-block',
                          px: 1,
                          py: 0.5,
                          borderRadius: 1,
                          backgroundColor: `${getStatusColor(item.status)}20`,
                        }}
                      >
                        {t(`account_management.history.status.${item.status}`)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {history.length === 0 && (
            <Box
              sx={{
                py: 4,
                textAlign: 'center',
                color: theme.palette.text.secondary,
              }}
            >
              <Typography>{t('account_management.history.no_records')}</Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default AccountHistory; 