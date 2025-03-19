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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { sellerApi } from '../../services/api';
import { formatNumber, formatDate } from '../../utils/formatters';
import { useTranslation } from 'react-i18next';

const CommissionHistory: React.FC = () => {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { data, refetch } = useQuery({
    queryKey: ['sellerCommissionHistory', page, rowsPerPage, searchQuery, statusFilter],
    queryFn: () =>
      sellerApi.getCommissionHistory({
        page: page + 1,
        limit: rowsPerPage,
        search: searchQuery,
        status: statusFilter === 'all' ? undefined : statusFilter,
      }),
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

  const getStatusChip = (status: string) => {
    const statusMap = {
      pending: { color: 'warning', label: t('Pending') },
      paid: { color: 'success', label: t('Paid') },
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
        <Typography variant="h4">{t('Commission History')}</Typography>
        <Tooltip title={t('Refresh')}>
          <IconButton onClick={() => refetch()}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder={t('Search by sale ID or customer')}
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
            <MenuItem value="paid">{t('Paid')}</MenuItem>
            <MenuItem value="cancelled">{t('Cancelled')}</MenuItem>
          </TextField>
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('Sale ID')}</TableCell>
              <TableCell>{t('Customer')}</TableCell>
              <TableCell>{t('Amount')}</TableCell>
              <TableCell>{t('Commission Rate')}</TableCell>
              <TableCell>{t('Commission Amount')}</TableCell>
              <TableCell>{t('Status')}</TableCell>
              <TableCell>{t('Date')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.results.map((commission: any) => (
              <TableRow key={commission.id}>
                <TableCell>{commission.sale_id}</TableCell>
                <TableCell>{commission.customer}</TableCell>
                <TableCell>{formatNumber(commission.amount)}</TableCell>
                <TableCell>{commission.rate}%</TableCell>
                <TableCell>{formatNumber(commission.commission_amount)}</TableCell>
                <TableCell>{getStatusChip(commission.status)}</TableCell>
                <TableCell>{formatDate(commission.created_at)}</TableCell>
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
    </Box>
  );
};

export default CommissionHistory; 