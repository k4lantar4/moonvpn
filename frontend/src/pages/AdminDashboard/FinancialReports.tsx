import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Chip,
  Divider,
  useTheme
} from '@mui/material';
import {
  DatePicker,
  LocalizationProvider
} from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { AdapterJalaali } from '@mui/x-date-pickers/AdapterJalaali';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useTranslation } from 'react-i18next';

// Example data for revenue chart
const monthlyRevenueData = [
  { name: 'فروردین', revenue: 12500000 },
  { name: 'اردیبهشت', revenue: 15800000 },
  { name: 'خرداد', revenue: 18200000 },
  { name: 'تیر', revenue: 22000000 },
  { name: 'مرداد', revenue: 19500000 },
  { name: 'شهریور', revenue: 25000000 }
];

// Example data for revenue by plan type
const revenueByPlanData = [
  { name: 'ماهانه', value: 35000000 },
  { name: 'سه ماهه', value: 48000000 },
  { name: 'شش ماهه', value: 30000000 },
  { name: 'سالانه', value: 15000000 }
];

// Example data for transactions
const transactionsData = [
  {
    id: 1,
    date: '1402/06/25',
    user: 'user1',
    type: 'subscription',
    plan: 'پلن ماهانه',
    amount: 250000,
    paymentMethod: 'wallet',
    status: 'completed'
  },
  {
    id: 2,
    date: '1402/06/24',
    user: 'user2',
    type: 'wallet',
    plan: '-',
    amount: 500000,
    paymentMethod: 'zarinpal',
    status: 'completed'
  },
  {
    id: 3,
    date: '1402/06/23',
    user: 'user3',
    type: 'subscription',
    plan: 'پلن سه ماهه',
    amount: 650000,
    paymentMethod: 'wallet',
    status: 'completed'
  },
  {
    id: 4,
    date: '1402/06/22',
    user: 'user4',
    type: 'wallet',
    plan: '-',
    amount: 1000000,
    paymentMethod: 'card',
    status: 'pending'
  },
  {
    id: 5,
    date: '1402/06/21',
    user: 'user5',
    type: 'subscription',
    plan: 'پلن سالانه',
    amount: 1800000,
    paymentMethod: 'wallet',
    status: 'completed'
  },
  {
    id: 6,
    date: '1402/06/20',
    user: 'user1',
    type: 'wallet',
    plan: '-',
    amount: 300000,
    paymentMethod: 'zarinpal',
    status: 'failed'
  }
];

// Colors for pie chart
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

// TabPanel component
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`financial-tabpanel-${index}`}
      aria-labelledby={`financial-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const FinancialReports: React.FC = () => {
  const theme = useTheme();
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'fa';
  
  // State for tabs
  const [tabValue, setTabValue] = useState(0);
  
  // State for date filters
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  
  // State for other filters
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // Get status chip color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };
  
  // Get type chip color
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'subscription':
        return 'primary';
      case 'wallet':
        return 'info';
      default:
        return 'default';
    }
  };
  
  // Filter transactions based on filters
  const filteredTransactions = transactionsData.filter(transaction => {
    const matchesType = typeFilter === 'all' || transaction.type === typeFilter;
    const matchesStatus = statusFilter === 'all' || transaction.status === statusFilter;
    
    // Date filtering would go here if we had actual Date objects
    
    return matchesType && matchesStatus;
  });
  
  // Calculate total revenue
  const totalRevenue = monthlyRevenueData.reduce((sum, item) => sum + item.revenue, 0);
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {t('گزارش‌های مالی')}
      </Typography>
      
      {/* Revenue Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                {t('درآمد کل')}
              </Typography>
              <Typography variant="h4" sx={{ mt: 1 }}>
                {totalRevenue.toLocaleString()} {t('تومان')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                {t('تراکنش‌های موفق')}
              </Typography>
              <Typography variant="h4" sx={{ mt: 1, color: theme.palette.success.main }}>
                {transactionsData.filter(t => t.status === 'completed').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                {t('تراکنش‌های در انتظار')}
              </Typography>
              <Typography variant="h4" sx={{ mt: 1, color: theme.palette.warning.main }}>
                {transactionsData.filter(t => t.status === 'pending').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: theme.palette.background.paper }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                {t('تراکنش‌های ناموفق')}
              </Typography>
              <Typography variant="h4" sx={{ mt: 1, color: theme.palette.error.main }}>
                {transactionsData.filter(t => t.status === 'failed').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label={t('نمودارها')} />
          <Tab label={t('تراکنش‌ها')} />
        </Tabs>
        
        {/* Charts Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {/* Monthly Revenue Chart */}
            <Grid item xs={12} md={8}>
              <Card sx={{ p: 2, bgcolor: theme.palette.background.paper }}>
                <Typography variant="h6" gutterBottom>
                  {t('درآمد ماهانه')}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={monthlyRevenueData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis 
                        tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`} 
                      />
                      <Tooltip 
                        formatter={(value: any) => [`${Number(value).toLocaleString()} ${t('تومان')}`, t('درآمد')]}
                      />
                      <Legend />
                      <Bar dataKey="revenue" name={t('درآمد')} fill={theme.palette.primary.main} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </Card>
            </Grid>
            
            {/* Revenue by Plan Type */}
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 2, bgcolor: theme.palette.background.paper }}>
                <Typography variant="h6" gutterBottom>
                  {t('درآمد بر اساس نوع پلن')}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={revenueByPlanData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {revenueByPlanData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value: any) => [`${Number(value).toLocaleString()} ${t('تومان')}`, t('درآمد')]}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Transactions Tab */}
        <TabPanel value={tabValue} index={1}>
          {/* Filters */}
          <Box sx={{ mb: 3, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <LocalizationProvider dateAdapter={isRTL ? AdapterJalaali : AdapterDateFns}>
              <DatePicker
                label={t('از تاریخ')}
                value={startDate}
                onChange={(newValue) => setStartDate(newValue)}
                slotProps={{ textField: { size: 'small' } }}
              />
              <DatePicker
                label={t('تا تاریخ')}
                value={endDate}
                onChange={(newValue) => setEndDate(newValue)}
                slotProps={{ textField: { size: 'small' } }}
              />
            </LocalizationProvider>
            
            <FormControl size="small" sx={{ minWidth: '150px' }}>
              <InputLabel>{t('نوع تراکنش')}</InputLabel>
              <Select
                value={typeFilter}
                label={t('نوع تراکنش')}
                onChange={(e) => setTypeFilter(e.target.value as string)}
              >
                <MenuItem value="all">{t('همه')}</MenuItem>
                <MenuItem value="subscription">{t('خرید اشتراک')}</MenuItem>
                <MenuItem value="wallet">{t('شارژ کیف پول')}</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: '150px' }}>
              <InputLabel>{t('وضعیت')}</InputLabel>
              <Select
                value={statusFilter}
                label={t('وضعیت')}
                onChange={(e) => setStatusFilter(e.target.value as string)}
              >
                <MenuItem value="all">{t('همه')}</MenuItem>
                <MenuItem value="completed">{t('موفق')}</MenuItem>
                <MenuItem value="pending">{t('در انتظار')}</MenuItem>
                <MenuItem value="failed">{t('ناموفق')}</MenuItem>
              </Select>
            </FormControl>
            
            <Button variant="contained" color="primary">
              {t('اعمال فیلتر')}
            </Button>
            
            <Button variant="outlined">
              {t('پاک کردن فیلتر')}
            </Button>
          </Box>
          
          {/* Transactions Table */}
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('شناسه')}</TableCell>
                  <TableCell>{t('تاریخ')}</TableCell>
                  <TableCell>{t('کاربر')}</TableCell>
                  <TableCell>{t('نوع')}</TableCell>
                  <TableCell>{t('پلن')}</TableCell>
                  <TableCell>{t('مبلغ')}</TableCell>
                  <TableCell>{t('روش پرداخت')}</TableCell>
                  <TableCell>{t('وضعیت')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTransactions.map((transaction) => (
                  <TableRow key={transaction.id}>
                    <TableCell>{transaction.id}</TableCell>
                    <TableCell>{transaction.date}</TableCell>
                    <TableCell>{transaction.user}</TableCell>
                    <TableCell>
                      <Chip 
                        label={transaction.type === 'subscription' ? t('خرید اشتراک') : t('شارژ کیف پول')} 
                        color={getTypeColor(transaction.type) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{transaction.plan}</TableCell>
                    <TableCell>{transaction.amount.toLocaleString()} {t('تومان')}</TableCell>
                    <TableCell>
                      {transaction.paymentMethod === 'wallet' && t('کیف پول')}
                      {transaction.paymentMethod === 'zarinpal' && t('زرین‌پال')}
                      {transaction.paymentMethod === 'card' && t('کارت به کارت')}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={
                          transaction.status === 'completed' ? t('موفق') : 
                          transaction.status === 'pending' ? t('در انتظار') : 
                          t('ناموفق')
                        } 
                        color={getStatusColor(transaction.status) as any}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default FinancialReports; 