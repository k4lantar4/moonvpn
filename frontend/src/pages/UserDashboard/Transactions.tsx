import React, { useState } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
} from '@mui/material';
import {
  AccountBalance as AccountBalanceIcon,
  ShoppingCart as ShoppingCartIcon,
  Receipt as ReceiptIcon,
  Payment as PaymentIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { userApi } from '../../services/api';
import { useTranslation } from 'react-i18next';
import { formatNumber, formatDate } from '../../utils/formatters';

const Transactions: React.FC = () => {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [type, setType] = useState('all');

  const { data: transactionsData, isLoading } = useQuery({
    queryKey: ['transactions', page, rowsPerPage, type],
    queryFn: () =>
      userApi.getTransactions({
        page: page + 1,
        limit: rowsPerPage,
        type: type === 'all' ? undefined : type,
      }),
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'deposit':
        return <AccountBalanceIcon color="primary" />;
      case 'withdrawal':
        return <PaymentIcon color="error" />;
      case 'purchase':
        return <ShoppingCartIcon color="success" />;
      case 'refund':
        return <ReceiptIcon color="warning" />;
      default:
        return null;
    }
  };

  const getStatusChip = (status: string) => {
    const statusMap = {
      pending: { color: 'warning', label: t('Pending') },
      completed: { color: 'success', label: t('Completed') },
      failed: { color: 'error', label: t('Failed') },
    };

    const statusInfo = statusMap[status as keyof typeof statusMap] || {
      color: 'default',
      label: status,
    };

    return (
      <Chip
        label={statusInfo.label}
        color={statusInfo.color as any}
        size="small"
      />
    );
  };

  if (isLoading) {
    return <Typography>{t('Loading...')}</Typography>;
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('Transaction History')}</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('Type')}</InputLabel>
          <Select
            value={type}
            label={t('Type')}
            onChange={(e) => setType(e.target.value)}
          >
            <MenuItem value="all">{t('All')}</MenuItem>
            <MenuItem value="deposit">{t('Deposit')}</MenuItem>
            <MenuItem value="withdrawal">{t('Withdrawal')}</MenuItem>
            <MenuItem value="purchase">{t('Purchase')}</MenuItem>
            <MenuItem value="refund">{t('Refund')}</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('Date')}</TableCell>
              <TableCell>{t('Type')}</TableCell>
              <TableCell>{t('Amount')}</TableCell>
              <TableCell>{t('Description')}</TableCell>
              <TableCell>{t('Status')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {transactionsData?.transactions.map((transaction: any) => (
              <TableRow key={transaction.id}>
                <TableCell>{formatDate(transaction.timestamp)}</TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getTransactionIcon(transaction.type)}
                    <Typography>{t(transaction.type)}</Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography
                    color={
                      transaction.type === 'deposit' || transaction.type === 'refund'
                        ? 'success.main'
                        : transaction.type === 'withdrawal'
                        ? 'error.main'
                        : 'text.primary'
                    }
                  >
                    {formatNumber(transaction.amount)}
                  </Typography>
                </TableCell>
                <TableCell>{transaction.description}</TableCell>
                <TableCell>{getStatusChip(transaction.status)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={transactionsData?.total || 0}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[5, 10, 25]}
      />
    </Box>
  );
};

export default Transactions; 