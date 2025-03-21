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
  Grid,
  Card,
  CardContent,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  ShoppingCart as ShoppingCartIcon,
  AccountBalance as AccountBalanceIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../../services/api';
import { useTranslation } from 'react-i18next';
import { formatNumber, formatDate } from '../../utils/formatters';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const Sales: React.FC = () => {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [dateRange, setDateRange] = useState('week');
  const [sellerId, setSellerId] = useState('all');

  const { data: salesData, isLoading } = useQuery({
    queryKey: ['sales', page, rowsPerPage, dateRange, sellerId],
    queryFn: () =>
      adminApi.getSales({
        page: page + 1,
        limit: rowsPerPage,
        date_range: dateRange,
        seller_id: sellerId === 'all' ? undefined : parseInt(sellerId),
      }),
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, icon, color }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4">{value}</Typography>
          </Box>
          <Box
            sx={{
              backgroundColor: `${color}20`,
              borderRadius: '50%',
              p: 1,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (isLoading) {
    return <Typography>{t('Loading...')}</Typography>;
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('Sales Reports')}</Typography>
        <Box display="flex" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>{t('Date Range')}</InputLabel>
            <Select
              value={dateRange}
              label={t('Date Range')}
              onChange={(e) => setDateRange(e.target.value)}
            >
              <MenuItem value="day">{t('Today')}</MenuItem>
              <MenuItem value="week">{t('This Week')}</MenuItem>
              <MenuItem value="month">{t('This Month')}</MenuItem>
              <MenuItem value="year">{t('This Year')}</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>{t('Seller')}</InputLabel>
            <Select
              value={sellerId}
              label={t('Seller')}
              onChange={(e) => setSellerId(e.target.value)}
            >
              <MenuItem value="all">{t('All Sellers')}</MenuItem>
              {salesData?.sellers.map((seller: any) => (
                <MenuItem key={seller.id} value={seller.id}>
                  {seller.username}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Box>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Total Sales')}
            value={formatNumber(salesData?.total_sales || 0)}
            icon={<ShoppingCartIcon sx={{ color: '#1976d2' }} />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Total Commissions')}
            value={formatNumber(salesData?.total_commissions || 0)}
            icon={<AccountBalanceIcon sx={{ color: '#2e7d32' }} />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Active Sellers')}
            value={salesData?.active_sellers || 0}
            icon={<PeopleIcon sx={{ color: '#ed6c02' }} />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={t('Growth')}
            value={`${salesData?.growth || 0}%`}
            icon={<TrendingUpIcon sx={{ color: '#9c27b0' }} />}
            color="#9c27b0"
          />
        </Grid>
      </Grid>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          {t('Sales Trend')}
        </Typography>
        <Box height={300}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={salesData?.sales_trend || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="sales"
                stroke="#1976d2"
                name={t('Sales')}
              />
              <Line
                type="monotone"
                dataKey="commissions"
                stroke="#2e7d32"
                name={t('Commissions')}
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('Date')}</TableCell>
              <TableCell>{t('Seller')}</TableCell>
              <TableCell>{t('Product')}</TableCell>
              <TableCell>{t('Amount')}</TableCell>
              <TableCell>{t('Commission')}</TableCell>
              <TableCell>{t('Status')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {salesData?.sales.map((sale: any) => (
              <TableRow key={sale.id}>
                <TableCell>{formatDate(sale.date)}</TableCell>
                <TableCell>{sale.seller_username}</TableCell>
                <TableCell>{sale.product_name}</TableCell>
                <TableCell>{formatNumber(sale.amount)}</TableCell>
                <TableCell>{formatNumber(sale.commission)}</TableCell>
                <TableCell>{sale.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={salesData?.total || 0}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[5, 10, 25]}
      />
    </Box>
  );
};

export default Sales; 