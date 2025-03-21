import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

// Example data - replace with actual API data
const transactions = [
  {
    id: 1,
    type: 'deposit',
    amount: 100000,
    description: 'Card Payment',
    date: '2024-03-13 14:30',
    status: 'completed',
  },
  {
    id: 2,
    type: 'withdrawal',
    amount: 50000,
    description: 'Withdrawal to Bank',
    date: '2024-03-12 09:15',
    status: 'completed',
  },
  {
    id: 3,
    type: 'purchase',
    amount: 75000,
    description: 'Premium Plan Purchase',
    date: '2024-03-11 16:45',
    status: 'completed',
  },
];

const RecentTransactions: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'deposit':
        return <TrendingUpIcon sx={{ color: theme.palette.success.main }} />;
      case 'withdrawal':
        return <TrendingDownIcon sx={{ color: theme.palette.error.main }} />;
      default:
        return null;
    }
  };

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

  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{t('dashboard.transaction.type')}</TableCell>
            <TableCell align="right">{t('dashboard.transaction.amount')}</TableCell>
            <TableCell>{t('dashboard.transaction.description')}</TableCell>
            <TableCell>{t('dashboard.transaction.date')}</TableCell>
            <TableCell>{t('dashboard.transaction.status')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {transactions.map((transaction) => (
            <TableRow key={transaction.id}>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {getTransactionIcon(transaction.type)}
                  <Typography sx={{ ml: 1 }}>
                    {t(`dashboard.transaction.types.${transaction.type}`)}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell align="right">
                <Typography
                  sx={{
                    color:
                      transaction.type === 'deposit'
                        ? theme.palette.success.main
                        : theme.palette.error.main,
                  }}
                >
                  {transaction.type === 'deposit' ? '+' : '-'}
                  {new Intl.NumberFormat('fa-IR').format(transaction.amount)}{' '}
                  {t('currency.toman')}
                </Typography>
              </TableCell>
              <TableCell>{transaction.description}</TableCell>
              <TableCell>
                {new Date(transaction.date).toLocaleString('fa-IR')}
              </TableCell>
              <TableCell>
                <Typography
                  sx={{
                    color: getStatusColor(transaction.status),
                    display: 'inline-block',
                    px: 1,
                    py: 0.5,
                    borderRadius: 1,
                    backgroundColor: `${getStatusColor(transaction.status)}20`,
                  }}
                >
                  {t(`dashboard.transaction.status.${transaction.status}`)}
                </Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default RecentTransactions; 