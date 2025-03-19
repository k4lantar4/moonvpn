import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  MenuItem,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Payment as PaymentIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sellerApi } from '../../services/api';
import { formatNumber, formatDate } from '../../utils/formatters';
import { useTranslation } from 'react-i18next';

const Withdrawals: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [openWithdrawDialog, setOpenWithdrawDialog] = useState(false);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [cardNumber, setCardNumber] = useState('');

  const { data, refetch } = useQuery({
    queryKey: ['sellerWithdrawals', page, rowsPerPage, searchQuery, statusFilter],
    queryFn: () =>
      sellerApi.getWithdrawalRequests({
        page: page + 1,
        limit: rowsPerPage,
        search: searchQuery,
        status: statusFilter === 'all' ? undefined : statusFilter,
      }),
  });

  const withdrawMutation = useMutation({
    mutationFn: () => sellerApi.requestWithdrawal(parseInt(withdrawAmount), cardNumber),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sellerWithdrawals'] });
      setOpenWithdrawDialog(false);
      setWithdrawAmount('');
      setCardNumber('');
    },
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleWithdraw = () => {
    if (withdrawAmount && cardNumber) {
      withdrawMutation.mutate();
    }
  };

  const getStatusChip = (status: string) => {
    const statusMap = {
      pending: { color: 'warning', label: t('Pending') },
      approved: { color: 'success', label: t('Approved') },
      rejected: { color: 'error', label: t('Rejected') },
      completed: { color: 'success', label: t('Completed') },
      cancelled: { color: 'error', label: t('Cancelled') },
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

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('Withdrawal Requests')}</Typography>
        <Box>
          <Tooltip title={t('New Withdrawal Request')}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<PaymentIcon />}
              onClick={() => setOpenWithdrawDialog(true)}
              sx={{ mr: 2 }}
            >
              {t('New Withdrawal')}
            </Button>
          </Tooltip>
          <Tooltip title={t('Refresh')}>
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder={t('Search by request ID or card number')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            select
            variant="outlined"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <MenuItem value="all">{t('All Statuses')}</MenuItem>
            <MenuItem value="pending">{t('Pending')}</MenuItem>
            <MenuItem value="approved">{t('Approved')}</MenuItem>
            <MenuItem value="rejected">{t('Rejected')}</MenuItem>
            <MenuItem value="completed">{t('Completed')}</MenuItem>
            <MenuItem value="cancelled">{t('Cancelled')}</MenuItem>
          </TextField>
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('Request ID')}</TableCell>
              <TableCell>{t('Amount')}</TableCell>
              <TableCell>{t('Card Number')}</TableCell>
              <TableCell>{t('Status')}</TableCell>
              <TableCell>{t('Created At')}</TableCell>
              <TableCell>{t('Updated At')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.results.map((withdrawal: any) => (
              <TableRow key={withdrawal.id}>
                <TableCell>{withdrawal.id}</TableCell>
                <TableCell>{formatNumber(withdrawal.amount)}</TableCell>
                <TableCell>{withdrawal.card_number}</TableCell>
                <TableCell>{getStatusChip(withdrawal.status)}</TableCell>
                <TableCell>{formatDate(withdrawal.created_at)}</TableCell>
                <TableCell>{formatDate(withdrawal.updated_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={data?.total || 0}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[5, 10, 25, 50]}
      />

      {/* Withdraw Dialog */}
      <Dialog open={openWithdrawDialog} onClose={() => setOpenWithdrawDialog(false)}>
        <DialogTitle>{t('New Withdrawal Request')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('Amount')}
            type="number"
            fullWidth
            value={withdrawAmount}
            onChange={(e) => setWithdrawAmount(e.target.value)}
          />
          <TextField
            margin="dense"
            label={t('Card Number')}
            fullWidth
            value={cardNumber}
            onChange={(e) => setCardNumber(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenWithdrawDialog(false)}>{t('Cancel')}</Button>
          <Button
            onClick={handleWithdraw}
            variant="contained"
            color="primary"
            disabled={!withdrawAmount || !cardNumber || withdrawMutation.isPending}
          >
            {withdrawMutation.isPending ? t('Submitting...') : t('Submit')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Withdrawals; 