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
  Receipt as ReceiptIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { sellerApi } from '../../services/api';
import { formatNumber, formatDate } from '../../utils/formatters';
import { useTranslation } from 'react-i18next';

const Sales: React.FC = () => {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { data, refetch } = useQuery({
    queryKey: ['sellerSales', page, rowsPerPage, searchQuery, statusFilter],
    queryFn: () =>
      sellerApi.getSales({
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
      completed: { color: 'success', label: t('Completed') },
      failed: { color: 'error', label: t('Failed') },
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
        <Typography variant="h4">{t('Sales History')}</Typography>
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
            placeholder={t('Search by customer or order ID')}
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
            <MenuItem value="completed">{t('Completed')}</MenuItem>
            <MenuItem value="failed">{t('Failed')}</MenuItem>
            <MenuItem value="cancelled">{t('Cancelled')}</MenuItem>
          </TextField>
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('Order ID')}</TableCell>
              <TableCell>{t('Customer')}</TableCell>
              <TableCell>{t('Amount')}</TableCell>
              <TableCell>{t('Commission')}</TableCell>
              <TableCell>{t('Status')}</TableCell>
              <TableCell>{t('Date')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.results.map((sale: any) => (
              <TableRow key={sale.id}>
                <TableCell>{sale.order_id}</TableCell>
                <TableCell>{sale.customer}</TableCell>
                <TableCell>{formatNumber(sale.amount)}</TableCell>
                <TableCell>{formatNumber(sale.commission)}</TableCell>
                <TableCell>{getStatusChip(sale.status)}</TableCell>
                <TableCell>{formatDate(sale.created_at)}</TableCell>
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

export default Sales; 