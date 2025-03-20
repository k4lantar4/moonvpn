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
  Menu,
  MenuItem,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Search as SearchIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { monitoringService } from '../../services/monitoring';

export const Alerts: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filters, setFilters] = useState<{
    status?: string;
    severity?: string;
    search?: string;
  }>({});
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedAlert, setSelectedAlert] = useState<number | null>(null);

  const queryClient = useQueryClient();

  const { data: alerts, isLoading, error } = useQuery({
    queryKey: ['alerts', filters],
    queryFn: () => monitoringService.getAlerts(filters),
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  const updateAlertStatus = useMutation({
    mutationFn: ({ alertId, status }: { alertId: number; status: string }) =>
      monitoringService.updateAlertStatus(alertId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      setAnchorEl(null);
    }
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, alertId: number) => {
    setAnchorEl(event.currentTarget);
    setSelectedAlert(alertId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedAlert(null);
  };

  const handleStatusUpdate = (status: string) => {
    if (selectedAlert) {
      updateAlertStatus.mutate({
        alertId: selectedAlert,
        status
      });
    }
    handleMenuClose();
  };

  const handleFilterChange = (field: keyof typeof filters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
    setPage(0);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Error loading alerts. Please try again later.
      </Alert>
    );
  }

  if (!alerts) {
    return null;
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'error';
      case 'resolved':
        return 'success';
      case 'acknowledged':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <Box p={3}>
      {/* Filters */}
      <Box mb={3} display="flex" gap={2}>
        <TextField
          label="Search"
          variant="outlined"
          size="small"
          value={filters.search || ''}
          onChange={(e) => handleFilterChange('search', e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            )
          }}
        />
        <TextField
          select
          label="Status"
          variant="outlined"
          size="small"
          value={filters.status || ''}
          onChange={(e) => handleFilterChange('status', e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <FilterIcon />
              </InputAdornment>
            )
          }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="active">Active</MenuItem>
          <MenuItem value="resolved">Resolved</MenuItem>
          <MenuItem value="acknowledged">Acknowledged</MenuItem>
        </TextField>
        <TextField
          select
          label="Severity"
          variant="outlined"
          size="small"
          value={filters.severity || ''}
          onChange={(e) => handleFilterChange('severity', e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <FilterIcon />
              </InputAdornment>
            )
          }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="critical">Critical</MenuItem>
          <MenuItem value="high">High</MenuItem>
          <MenuItem value="medium">Medium</MenuItem>
          <MenuItem value="low">Low</MenuItem>
        </TextField>
      </Box>

      {/* Alerts Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Resolved</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((alert) => (
                <TableRow key={alert.id}>
                  <TableCell>{alert.name}</TableCell>
                  <TableCell>{alert.description}</TableCell>
                  <TableCell>
                    <Chip
                      label={alert.severity.toUpperCase()}
                      color={getSeverityColor(alert.severity)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={alert.status.toUpperCase()}
                      color={getStatusColor(alert.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatTimestamp(alert.created_at)}</TableCell>
                  <TableCell>
                    {alert.resolved_at ? formatTimestamp(alert.resolved_at) : '-'}
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuClick(e, alert.id)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <TablePagination
        component="div"
        count={alerts.length}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[5, 10, 25]}
      />

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {selectedAlert && alerts.find(a => a.id === selectedAlert)?.status === 'active' && (
          <>
            <MenuItem onClick={() => handleStatusUpdate('acknowledged')}>
              Acknowledge
            </MenuItem>
            <MenuItem onClick={() => handleStatusUpdate('resolved')}>
              Resolve
            </MenuItem>
          </>
        )}
        {selectedAlert && alerts.find(a => a.id === selectedAlert)?.status === 'acknowledged' && (
          <MenuItem onClick={() => handleStatusUpdate('resolved')}>
            Resolve
          </MenuItem>
        )}
      </Menu>
    </Box>
  );
}; 