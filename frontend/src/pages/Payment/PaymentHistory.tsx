import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
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
  InputAdornment,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  Button,
  useTheme
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Receipt as ReceiptIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

// Payment status types
type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

// Payment method types
type PaymentMethod = 'card' | 'zarinpal' | 'wallet';

// Payment transaction interface
interface PaymentTransaction {
  id: string;
  date: string;
  amount: number;
  description: string;
  status: PaymentStatus;
  method: PaymentMethod;
  transactionId?: string;
  invoiceUrl?: string;
}

// Example transaction data
const exampleTransactions: PaymentTransaction[] = [
  {
    id: 'TRX-001',
    date: '1402/06/25 14:30',
    amount: 250000,
    description: 'خرید اشتراک ماهانه',
    status: 'completed',
    method: 'zarinpal',
    transactionId: 'A123456789',
    invoiceUrl: '#'
  },
  {
    id: 'TRX-002',
    date: '1402/06/20 10:15',
    amount: 650000,
    description: 'خرید اشتراک سه ماهه',
    status: 'completed',
    method: 'card',
    transactionId: 'C987654321',
    invoiceUrl: '#'
  },
  {
    id: 'TRX-003',
    date: '1402/06/15 18:45',
    amount: 500000,
    description: 'شارژ کیف پول',
    status: 'completed',
    method: 'zarinpal',
    transactionId: 'A567891234',
    invoiceUrl: '#'
  },
  {
    id: 'TRX-004',
    date: '1402/06/10 09:30',
    amount: 1200000,
    description: 'خرید اشتراک شش ماهه',
    status: 'failed',
    method: 'card',
    transactionId: 'C543216789',
  },
  {
    id: 'TRX-005',
    date: '1402/06/05 16:20',
    amount: 250000,
    description: 'خرید اشتراک ماهانه',
    status: 'refunded',
    method: 'wallet',
    transactionId: 'W123789456',
    invoiceUrl: '#'
  },
  {
    id: 'TRX-006',
    date: '1402/06/01 12:00',
    amount: 2000000,
    description: 'خرید اشتراک سالانه',
    status: 'pending',
    method: 'card',
    transactionId: 'C789456123',
  },
  {
    id: 'TRX-007',
    date: '1402/05/25 11:10',
    amount: 500000,
    description: 'شارژ کیف پول',
    status: 'completed',
    method: 'zarinpal',
    transactionId: 'A456123789',
    invoiceUrl: '#'
  },
  {
    id: 'TRX-008',
    date: '1402/05/20 09:45',
    amount: 250000,
    description: 'خرید اشتراک ماهانه',
    status: 'completed',
    method: 'wallet',
    transactionId: 'W789123456',
    invoiceUrl: '#'
  },
  {
    id: 'TRX-009',
    date: '1402/05/15 14:30',
    amount: 650000,
    description: 'خرید اشتراک سه ماهه',
    status: 'completed',
    method: 'zarinpal',
    transactionId: 'A321654987',
    invoiceUrl: '#'
  },
  {
    id: 'TRX-010',
    date: '1402/05/10 17:15',
    amount: 100000,
    description: 'شارژ کیف پول',
    status: 'failed',
    method: 'card',
    transactionId: 'C654987321',
  }
];

const PaymentHistory: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [methodFilter, setMethodFilter] = useState<string>('');
  
  // Handle page change
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };
  
  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Handle search input change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
    setPage(0);
  };
  
  // Handle status filter change
  const handleStatusFilterChange = (event: SelectChangeEvent) => {
    setStatusFilter(event.target.value);
    setPage(0);
  };
  
  // Handle method filter change
  const handleMethodFilterChange = (event: SelectChangeEvent) => {
    setMethodFilter(event.target.value);
    setPage(0);
  };
  
  // Reset all filters
  const handleResetFilters = () => {
    setSearchQuery('');
    setStatusFilter('');
    setMethodFilter('');
    setPage(0);
  };
  
  // Get status color based on status type
  const getStatusColor = (status: PaymentStatus) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      case 'refunded':
        return 'info';
      default:
        return 'default';
    }
  };
  
  // Get payment method label
  const getMethodLabel = (method: PaymentMethod) => {
    switch (method) {
      case 'card':
        return t('کارت به کارت');
      case 'zarinpal':
        return t('زرین‌پال');
      case 'wallet':
        return t('کیف پول');
      default:
        return method;
    }
  };
  
  // Filter transactions based on search query and filters
  const filteredTransactions = exampleTransactions.filter((transaction) => {
    const matchesSearch = searchQuery === '' || 
      transaction.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      transaction.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      transaction.transactionId?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === '' || transaction.status === statusFilter;
    const matchesMethod = methodFilter === '' || transaction.method === methodFilter;
    
    return matchesSearch && matchesStatus && matchesMethod;
  });
  
  // Get current page transactions
  const currentTransactions = filteredTransactions.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {t('تاریخچه پرداخت‌ها')}
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4, bgcolor: theme.palette.background.paper }}>
        <Box sx={{ mb: 3, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          <TextField
            label={t('جستجو')}
            variant="outlined"
            size="small"
            value={searchQuery}
            onChange={handleSearchChange}
            sx={{ minWidth: 220, flexGrow: 1 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            placeholder={t('جستجو در شناسه، توضیحات یا کد پیگیری')}
          />
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel id="status-filter-label">{t('وضعیت')}</InputLabel>
            <Select
              labelId="status-filter-label"
              value={statusFilter}
              label={t('وضعیت')}
              onChange={handleStatusFilterChange}
            >
              <MenuItem value="">{t('همه')}</MenuItem>
              <MenuItem value="completed">{t('پرداخت شده')}</MenuItem>
              <MenuItem value="pending">{t('در انتظار تایید')}</MenuItem>
              <MenuItem value="failed">{t('ناموفق')}</MenuItem>
              <MenuItem value="refunded">{t('بازگشت وجه')}</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel id="method-filter-label">{t('روش پرداخت')}</InputLabel>
            <Select
              labelId="method-filter-label"
              value={methodFilter}
              label={t('روش پرداخت')}
              onChange={handleMethodFilterChange}
            >
              <MenuItem value="">{t('همه')}</MenuItem>
              <MenuItem value="card">{t('کارت به کارت')}</MenuItem>
              <MenuItem value="zarinpal">{t('زرین‌پال')}</MenuItem>
              <MenuItem value="wallet">{t('کیف پول')}</MenuItem>
            </Select>
          </FormControl>
          
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleResetFilters}
          >
            {t('حذف فیلترها')}
          </Button>
        </Box>
        
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow>
                <TableCell>{t('شناسه')}</TableCell>
                <TableCell>{t('تاریخ')}</TableCell>
                <TableCell>{t('مبلغ (تومان)')}</TableCell>
                <TableCell>{t('توضیحات')}</TableCell>
                <TableCell>{t('روش پرداخت')}</TableCell>
                <TableCell>{t('وضعیت')}</TableCell>
                <TableCell align="center">{t('عملیات')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {currentTransactions.length > 0 ? (
                currentTransactions.map((transaction) => (
                  <TableRow key={transaction.id} hover>
                    <TableCell>{transaction.id}</TableCell>
                    <TableCell>{transaction.date}</TableCell>
                    <TableCell>{transaction.amount.toLocaleString()}</TableCell>
                    <TableCell>{transaction.description}</TableCell>
                    <TableCell>{getMethodLabel(transaction.method)}</TableCell>
                    <TableCell>
                      <Chip
                        label={t(transaction.status === 'completed' ? 'پرداخت شده' : 
                                transaction.status === 'pending' ? 'در انتظار تایید' :
                                transaction.status === 'failed' ? 'ناموفق' : 'بازگشت وجه')}
                        color={getStatusColor(transaction.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title={t('مشاهده جزئیات')}>
                        <IconButton size="small">
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      
                      {transaction.invoiceUrl && (
                        <Tooltip title={t('مشاهده فاکتور')}>
                          <IconButton size="small">
                            <ReceiptIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    {t('هیچ تراکنشی یافت نشد')}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredTransactions.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage={t('تعداد در صفحه:')}
          labelDisplayedRows={({ from, to, count }) => 
            `${from}-${to} ${t('از')} ${count !== -1 ? count : `${t('بیش از')} ${to}`}`
          }
        />
      </Paper>
    </Box>
  );
};

export default PaymentHistory; 