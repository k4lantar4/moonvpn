import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  IconButton,
  Tooltip,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  InputAdornment,
  useTheme,
  Grid,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';

// Example data
const users = [
  {
    id: 1,
    username: 'user1',
    name: 'کاربر اول',
    email: 'user1@example.com',
    telegramId: '123456789',
    status: 'active',
    role: 'user',
    createdAt: '2023-12-01',
    balance: 250000,
  },
  {
    id: 2,
    username: 'user2',
    name: 'کاربر دوم',
    email: 'user2@example.com',
    telegramId: '987654321',
    status: 'active',
    role: 'user',
    createdAt: '2023-12-05',
    balance: 120000,
  },
  {
    id: 3,
    username: 'admin1',
    name: 'مدیر سیستم',
    email: 'admin@example.com',
    telegramId: '555555555',
    status: 'active',
    role: 'admin',
    createdAt: '2023-11-15',
    balance: 500000,
  },
  {
    id: 4,
    username: 'user3',
    name: 'کاربر سوم',
    email: 'user3@example.com',
    telegramId: '111222333',
    status: 'blocked',
    role: 'user',
    createdAt: '2023-12-10',
    balance: 0,
  },
  {
    id: 5,
    username: 'user4',
    name: 'کاربر چهارم',
    email: 'user4@example.com',
    telegramId: '444555666',
    status: 'active',
    role: 'user',
    createdAt: '2023-12-15',
    balance: 375000,
  },
];

const UserManagement: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [formData, setFormData] = useState({
    username: '',
    name: '',
    email: '',
    telegramId: '',
    status: 'active',
    role: 'user',
    balance: 0,
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
    setPage(0);
  };

  const handleStatusFilterChange = (event: any) => {
    setStatusFilter(event.target.value);
    setPage(0);
  };

  const handleRoleFilterChange = (event: any) => {
    setRoleFilter(event.target.value);
    setPage(0);
  };

  const handleOpenAddDialog = () => {
    setFormData({
      username: '',
      name: '',
      email: '',
      telegramId: '',
      status: 'active',
      role: 'user',
      balance: 0,
    });
    setOpenAddDialog(true);
  };

  const handleCloseAddDialog = () => {
    setOpenAddDialog(false);
  };

  const handleOpenEditDialog = (user: any) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      name: user.name,
      email: user.email,
      telegramId: user.telegramId,
      status: user.status,
      role: user.role,
      balance: user.balance,
    });
    setOpenEditDialog(true);
  };

  const handleCloseEditDialog = () => {
    setOpenEditDialog(false);
  };

  const handleOpenDeleteDialog = (user: any) => {
    setSelectedUser(user);
    setOpenDeleteDialog(true);
  };

  const handleCloseDeleteDialog = () => {
    setOpenDeleteDialog(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSelectChange = (e: any) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddUser = () => {
    // TODO: Implement API call to add user
    console.log('Add user:', formData);
    setOpenAddDialog(false);
  };

  const handleEditUser = () => {
    // TODO: Implement API call to edit user
    console.log('Edit user:', formData);
    setOpenEditDialog(false);
  };

  const handleDeleteUser = () => {
    // TODO: Implement API call to delete user
    console.log('Delete user:', selectedUser);
    setOpenDeleteDialog(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.palette.success.main;
      case 'blocked':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return theme.palette.primary.main;
      case 'user':
        return theme.palette.info.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  // Filter users based on search query and filters
  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      searchQuery === '' ||
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.telegramId.includes(searchQuery);

    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;

    return matchesSearch && matchesStatus && matchesRole;
  });

  // Apply pagination
  const paginatedUsers = filteredUsers.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ color: theme.palette.text.primary, fontWeight: 'bold' }}>
          {t('admin.users.title')}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenAddDialog}
        >
          {t('admin.users.add_user')}
        </Button>
      </Box>

      <Card sx={{ mb: 4, backgroundColor: theme.palette.background.paper }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder={t('admin.users.search_placeholder')}
                value={searchQuery}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>{t('admin.users.status_filter')}</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={handleStatusFilterChange}
                  label={t('admin.users.status_filter')}
                >
                  <MenuItem value="all">{t('admin.filters.all')}</MenuItem>
                  <MenuItem value="active">{t('admin.users.status.active')}</MenuItem>
                  <MenuItem value="blocked">{t('admin.users.status.blocked')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>{t('admin.users.role_filter')}</InputLabel>
                <Select
                  value={roleFilter}
                  onChange={handleRoleFilterChange}
                  label={t('admin.users.role_filter')}
                >
                  <MenuItem value="all">{t('admin.filters.all')}</MenuItem>
                  <MenuItem value="admin">{t('admin.users.roles.admin')}</MenuItem>
                  <MenuItem value="user">{t('admin.users.roles.user')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <TableContainer component={Paper} sx={{ backgroundColor: theme.palette.background.paper }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>#</TableCell>
              <TableCell>{t('admin.users.username')}</TableCell>
              <TableCell>{t('admin.users.name')}</TableCell>
              <TableCell>{t('admin.users.email')}</TableCell>
              <TableCell>{t('admin.users.telegram_id')}</TableCell>
              <TableCell>{t('admin.users.status')}</TableCell>
              <TableCell>{t('admin.users.role')}</TableCell>
              <TableCell align="right">{t('admin.users.balance')}</TableCell>
              <TableCell>{t('admin.users.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedUsers.map((user, index) => (
              <TableRow key={user.id}>
                <TableCell>{page * rowsPerPage + index + 1}</TableCell>
                <TableCell>{user.username}</TableCell>
                <TableCell>{user.name}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>{user.telegramId}</TableCell>
                <TableCell>
                  <Chip
                    label={t(`admin.users.status.${user.status}`)}
                    size="small"
                    sx={{
                      backgroundColor: `${getStatusColor(user.status)}20`,
                      color: getStatusColor(user.status),
                      fontWeight: 'medium',
                    }}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={t(`admin.users.roles.${user.role}`)}
                    size="small"
                    sx={{
                      backgroundColor: `${getRoleColor(user.role)}20`,
                      color: getRoleColor(user.role),
                      fontWeight: 'medium',
                    }}
                  />
                </TableCell>
                <TableCell align="right">
                  {user.balance.toLocaleString('fa-IR')} {t('common.currency')}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex' }}>
                    <Tooltip title={t('admin.users.edit')}>
                      <IconButton size="small" onClick={() => handleOpenEditDialog(user)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={user.status === 'active' ? t('admin.users.block') : t('admin.users.unblock')}>
                      <IconButton size="small">
                        {user.status === 'active' ? (
                          <BlockIcon fontSize="small" color="error" />
                        ) : (
                          <CheckCircleIcon fontSize="small" color="success" />
                        )}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('admin.users.delete')}>
                      <IconButton size="small" onClick={() => handleOpenDeleteDialog(user)}>
                        <DeleteIcon fontSize="small" color="error" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredUsers.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage={t('admin.table.rows_per_page')}
        />
      </TableContainer>

      {/* Add User Dialog */}
      <Dialog open={openAddDialog} onClose={handleCloseAddDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{t('admin.users.add_user')}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.users.username')}
                name="username"
                value={formData.username}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.users.name')}
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.users.email')}
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.users.telegram_id')}
                name="telegramId"
                value={formData.telegramId}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.users.status')}</InputLabel>
                <Select
                  name="status"
                  value={formData.status}
                  onChange={handleSelectChange}
                  label={t('admin.users.status')}
                >
                  <MenuItem value="active">{t('admin.users.status.active')}</MenuItem>
                  <MenuItem value="blocked">{t('admin.users.status.blocked')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.users.role')}</InputLabel>
                <Select
                  name="role"
                  value={formData.role}
                  onChange={handleSelectChange}
                  label={t('admin.users.role')}
                >
                  <MenuItem value="admin">{t('admin.users.roles.admin')}</MenuItem>
                  <MenuItem value="user">{t('admin.users.roles.user')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('admin.users.initial_balance')}
                name="balance"
                type="number"
                value={formData.balance}
                onChange={handleInputChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">{t('common.currency')}</InputAdornment>,
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAddDialog}>{t('common.cancel')}</Button>
          <Button onClick={handleAddUser} variant="contained">
            {t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={openEditDialog} onClose={handleCloseEditDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{t('admin.users.edit_user')}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.users.username')}
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                disabled
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.users.name')}
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.users.email')}
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.users.telegram_id')}
                name="telegramId"
                value={formData.telegramId}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.users.status')}</InputLabel>
                <Select
                  name="status"
                  value={formData.status}
                  onChange={handleSelectChange}
                  label={t('admin.users.status')}
                >
                  <MenuItem value="active">{t('admin.users.status.active')}</MenuItem>
                  <MenuItem value="blocked">{t('admin.users.status.blocked')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.users.role')}</InputLabel>
                <Select
                  name="role"
                  value={formData.role}
                  onChange={handleSelectChange}
                  label={t('admin.users.role')}
                >
                  <MenuItem value="admin">{t('admin.users.roles.admin')}</MenuItem>
                  <MenuItem value="user">{t('admin.users.roles.user')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('admin.users.balance')}
                name="balance"
                type="number"
                value={formData.balance}
                onChange={handleInputChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">{t('common.currency')}</InputAdornment>,
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>{t('common.cancel')}</Button>
          <Button onClick={handleEditUser} variant="contained">
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={openDeleteDialog} onClose={handleCloseDeleteDialog}>
        <DialogTitle>{t('admin.users.delete_user')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('admin.users.delete_confirm', { username: selectedUser?.username })}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>{t('common.cancel')}</Button>
          <Button onClick={handleDeleteUser} color="error" variant="contained">
            {t('common.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement; 