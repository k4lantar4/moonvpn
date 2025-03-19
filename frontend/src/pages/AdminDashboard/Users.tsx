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
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  MenuItem,
  Typography,
  Chip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../services/api';
import { useTranslation } from 'react-i18next';
import { formatDate } from '../../utils/formatters';

const Users: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [openDialog, setOpenDialog] = useState(false);

  const { data: usersData, isLoading } = useQuery({
    queryKey: ['users', page, rowsPerPage, search],
    queryFn: () =>
      adminApi.getUsers({
        page: page + 1,
        limit: rowsPerPage,
        search,
      }),
  });

  const updateUserMutation = useMutation({
    mutationFn: (data: any) => adminApi.updateUser(selectedUser.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setOpenDialog(false);
    },
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleEditUser = (user: any) => {
    setSelectedUser(user);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedUser(null);
  };

  const handleSaveUser = (event: React.FormEvent) => {
    event.preventDefault();
    if (selectedUser) {
      updateUserMutation.mutate(selectedUser);
    }
  };

  const getStatusChip = (status: string) => {
    const statusMap = {
      active: { color: 'success', label: t('Active') },
      blocked: { color: 'error', label: t('Blocked') },
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
        <Typography variant="h4">{t('User Management')}</Typography>
        <TextField
          label={t('Search')}
          variant="outlined"
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('ID')}</TableCell>
              <TableCell>{t('Username')}</TableCell>
              <TableCell>{t('Email')}</TableCell>
              <TableCell>{t('Role')}</TableCell>
              <TableCell>{t('Status')}</TableCell>
              <TableCell>{t('Created At')}</TableCell>
              <TableCell>{t('Actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {usersData?.users.map((user: any) => (
              <TableRow key={user.id}>
                <TableCell>{user.id}</TableCell>
                <TableCell>{user.username}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>{t(user.role)}</TableCell>
                <TableCell>{getStatusChip(user.status)}</TableCell>
                <TableCell>{formatDate(user.created_at)}</TableCell>
                <TableCell>
                  <Tooltip title={t('Edit')}>
                    <IconButton onClick={() => handleEditUser(user)}>
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={user.status === 'active' ? t('Block') : t('Unblock')}>
                    <IconButton>
                      {user.status === 'active' ? <BlockIcon /> : <CheckCircleIcon />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('Delete')}>
                    <IconButton>
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={usersData?.total || 0}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[5, 10, 25]}
      />

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <form onSubmit={handleSaveUser}>
          <DialogTitle>{t('Edit User')}</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label={t('Username')}
              value={selectedUser?.username || ''}
              onChange={(e) =>
                setSelectedUser({ ...selectedUser, username: e.target.value })
              }
              margin="normal"
            />
            <TextField
              fullWidth
              label={t('Email')}
              value={selectedUser?.email || ''}
              onChange={(e) =>
                setSelectedUser({ ...selectedUser, email: e.target.value })
              }
              margin="normal"
            />
            <TextField
              fullWidth
              select
              label={t('Role')}
              value={selectedUser?.role || ''}
              onChange={(e) =>
                setSelectedUser({ ...selectedUser, role: e.target.value })
              }
              margin="normal"
            >
              <MenuItem value="admin">{t('Admin')}</MenuItem>
              <MenuItem value="seller">{t('Seller')}</MenuItem>
              <MenuItem value="user">{t('User')}</MenuItem>
            </TextField>
            <TextField
              fullWidth
              select
              label={t('Status')}
              value={selectedUser?.status || ''}
              onChange={(e) =>
                setSelectedUser({ ...selectedUser, status: e.target.value })
              }
              margin="normal"
            >
              <MenuItem value="active">{t('Active')}</MenuItem>
              <MenuItem value="blocked">{t('Blocked')}</MenuItem>
              <MenuItem value="pending">{t('Pending')}</MenuItem>
            </TextField>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>{t('Cancel')}</Button>
            <Button type="submit" variant="contained" color="primary">
              {t('Save')}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};

export default Users; 