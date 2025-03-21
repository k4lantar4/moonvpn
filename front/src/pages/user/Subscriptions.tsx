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
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  IconButton,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Refresh as RefreshIcon,
  QrCode as QrCodeIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '../../services/api';
import { useTranslation } from 'react-i18next';
import { formatNumber, formatDate } from '../../utils/formatters';

const Subscriptions: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [status, setStatus] = useState('all');
  const [selectedSubscription, setSelectedSubscription] = useState<any>(null);
  const [showConfigDialog, setShowConfigDialog] = useState(false);

  const { data: subscriptionsData, isLoading } = useQuery({
    queryKey: ['subscriptions', page, rowsPerPage, status],
    queryFn: () =>
      userApi.getSubscriptions({
        page: page + 1,
        limit: rowsPerPage,
        status: status === 'all' ? undefined : status,
      }),
  });

  const refreshMutation = useMutation({
    mutationFn: (id: string) => userApi.refreshSubscription(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleRefresh = (id: string) => {
    refreshMutation.mutate(id);
  };

  const handleShowConfig = (subscription: any) => {
    setSelectedSubscription(subscription);
    setShowConfigDialog(true);
  };

  const handleCopyConfig = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getStatusChip = (status: string) => {
    const statusMap = {
      active: { color: 'success', label: t('Active') },
      expired: { color: 'error', label: t('Expired') },
      pending: { color: 'warning', label: t('Pending') },
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
        <Typography variant="h4">{t('My Subscriptions')}</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('Status')}</InputLabel>
          <Select
            value={status}
            label={t('Status')}
            onChange={(e) => setStatus(e.target.value)}
          >
            <MenuItem value="all">{t('All')}</MenuItem>
            <MenuItem value="active">{t('Active')}</MenuItem>
            <MenuItem value="expired">{t('Expired')}</MenuItem>
            <MenuItem value="pending">{t('Pending')}</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <SpeedIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">{t('Active Subscriptions')}</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {subscriptionsData?.active_count || 0}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(subscriptionsData?.active_count / subscriptionsData?.total) * 100}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <SpeedIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="h6">{t('Expired Subscriptions')}</Typography>
              </Box>
              <Typography variant="h4" color="error">
                {subscriptionsData?.expired_count || 0}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(subscriptionsData?.expired_count / subscriptionsData?.total) * 100}
                color="error"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <SpeedIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">{t('Pending Subscriptions')}</Typography>
              </Box>
              <Typography variant="h4" color="warning.main">
                {subscriptionsData?.pending_count || 0}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(subscriptionsData?.pending_count / subscriptionsData?.total) * 100}
                color="warning"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('Plan')}</TableCell>
              <TableCell>{t('Status')}</TableCell>
              <TableCell>{t('Start Date')}</TableCell>
              <TableCell>{t('End Date')}</TableCell>
              <TableCell>{t('Usage')}</TableCell>
              <TableCell>{t('Actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {subscriptionsData?.subscriptions.map((subscription: any) => (
              <TableRow key={subscription.id}>
                <TableCell>{subscription.plan.name}</TableCell>
                <TableCell>{getStatusChip(subscription.status)}</TableCell>
                <TableCell>{formatDate(subscription.start_date)}</TableCell>
                <TableCell>{formatDate(subscription.end_date)}</TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography>
                      {formatNumber(subscription.usage)} / {formatNumber(subscription.plan.quota)}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={(subscription.usage / subscription.plan.quota) * 100}
                      sx={{ width: 100 }}
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Button
                      size="small"
                      startIcon={<RefreshIcon />}
                      onClick={() => handleRefresh(subscription.id)}
                      disabled={refreshMutation.isPending}
                    >
                      {t('Refresh')}
                    </Button>
                    <Button
                      size="small"
                      startIcon={<QrCodeIcon />}
                      onClick={() => handleShowConfig(subscription)}
                    >
                      {t('Config')}
                    </Button>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={subscriptionsData?.total || 0}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[5, 10, 25]}
      />

      <Dialog
        open={showConfigDialog}
        onClose={() => setShowConfigDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t('Subscription Configuration')}</DialogTitle>
        <DialogContent>
          {selectedSubscription && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                {t('Server')}: {selectedSubscription.server.name}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                {t('Plan')}: {selectedSubscription.plan.name}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                {t('Status')}: {getStatusChip(selectedSubscription.status)}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                {t('Start Date')}: {formatDate(selectedSubscription.start_date)}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                {t('End Date')}: {formatDate(selectedSubscription.end_date)}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                {t('Usage')}: {formatNumber(selectedSubscription.usage)} / {formatNumber(selectedSubscription.plan.quota)}
              </Typography>
              <Box mt={2}>
                <Typography variant="subtitle1" gutterBottom>
                  {t('Configuration')}:
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={selectedSubscription.config}
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <IconButton onClick={() => handleCopyConfig(selectedSubscription.config)}>
                        <ContentCopyIcon />
                      </IconButton>
                    ),
                  }}
                />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowConfigDialog(false)}>{t('Close')}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Subscriptions; 