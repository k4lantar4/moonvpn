import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  useTheme,
  Alert,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  ManageAccounts as ManageAccountsIcon,
  AdminPanelSettings as AdminIcon,
  Person as UserIcon,
  Store as ResellerIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { UserRole } from '../../contexts/AuthContext';

// Define sample data for demonstration
const sampleUsers = [
  { 
    id: '1', 
    fullName: 'علی محمدی', 
    email: 'ali@example.com', 
    role: UserRole.ADMIN,
    isActive: true,
    lastLogin: '2025-03-01T10:30:00',
  },
  { 
    id: '2', 
    fullName: 'مریم احمدی', 
    email: 'maryam@example.com', 
    role: UserRole.RESELLER,
    isActive: true,
    lastLogin: '2025-03-05T14:20:00',
  },
  { 
    id: '3', 
    fullName: 'رضا کریمی', 
    email: 'reza@example.com', 
    role: UserRole.USER,
    isActive: true,
    lastLogin: '2025-03-10T09:15:00',
  },
  { 
    id: '4', 
    fullName: 'سارا رضایی', 
    email: 'sara@example.com', 
    role: UserRole.USER,
    isActive: false,
    lastLogin: '2025-02-20T16:45:00',
  },
  { 
    id: '5', 
    fullName: 'محمد حسینی', 
    email: 'mohammad@example.com', 
    role: UserRole.RESELLER,
    isActive: true,
    lastLogin: '2025-03-08T11:30:00',
  },
];

// Get icon for role
const getRoleIcon = (role: UserRole) => {
  switch (role) {
    case UserRole.ADMIN:
      return <AdminIcon />;
    case UserRole.RESELLER:
      return <ResellerIcon />;
    case UserRole.USER:
    default:
      return <UserIcon />;
  }
};

// Get color for role
const getRoleColor = (role: UserRole): 'primary' | 'secondary' | 'default' => {
  switch (role) {
    case UserRole.ADMIN:
      return 'primary';
    case UserRole.RESELLER:
      return 'secondary';
    case UserRole.USER:
    default:
      return 'default';
  }
};

// Get text for role
const getRoleText = (role: UserRole, t: any): string => {
  switch (role) {
    case UserRole.ADMIN:
      return t('مدیر');
    case UserRole.RESELLER:
      return t('فروشنده');
    case UserRole.USER:
    default:
      return t('کاربر');
  }
};

// Main component
const RoleManager: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  
  // State
  const [users, setUsers] = useState(sampleUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [selectedRole, setSelectedRole] = useState<UserRole | ''>('');
  const [alertMessage, setAlertMessage] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  
  // Filter users by search term
  const filteredUsers = users.filter(user => 
    user.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };
  
  // Handle edit button click
  const handleEditClick = (user: any) => {
    setSelectedUser(user);
    setSelectedRole(user.role);
    setEditDialogOpen(true);
  };
  
  // Handle delete button click
  const handleDeleteClick = (user: any) => {
    setSelectedUser(user);
    setDeleteDialogOpen(true);
  };
  
  // Handle role change
  const handleRoleChange = (e: any) => {
    setSelectedRole(e.target.value);
  };
  
  // Handle edit dialog save
  const handleEditSave = () => {
    if (selectedUser && selectedRole) {
      // Update user role
      const updatedUsers = users.map(user => 
        user.id === selectedUser.id ? { ...user, role: selectedRole } : user
      );
      
      setUsers(updatedUsers);
      setAlertMessage({
        type: 'success',
        message: `نقش کاربر ${selectedUser.fullName} با موفقیت به ${getRoleText(selectedRole as UserRole, t)} تغییر یافت`
      });
      
      // Close dialog
      setEditDialogOpen(false);
      setSelectedUser(null);
      setSelectedRole('');
      
      // Clear alert after 5 seconds
      setTimeout(() => {
        setAlertMessage(null);
      }, 5000);
    }
  };
  
  // Handle delete dialog confirm
  const handleDeleteConfirm = () => {
    if (selectedUser) {
      // Remove user
      const updatedUsers = users.filter(user => user.id !== selectedUser.id);
      
      setUsers(updatedUsers);
      setAlertMessage({
        type: 'success',
        message: `کاربر ${selectedUser.fullName} با موفقیت حذف شد`
      });
      
      // Close dialog
      setDeleteDialogOpen(false);
      setSelectedUser(null);
      
      // Clear alert after 5 seconds
      setTimeout(() => {
        setAlertMessage(null);
      }, 5000);
    }
  };
  
  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fa-IR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };
  
  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h2">
          <ManageAccountsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          {t('مدیریت نقش‌ها')}
        </Typography>
      </Box>
      
      {/* Alert message */}
      {alertMessage && (
        <Alert 
          severity={alertMessage.type} 
          sx={{ mb: 3 }}
          onClose={() => setAlertMessage(null)}
        >
          {alertMessage.message}
        </Alert>
      )}
      
      {/* Search Box */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            placeholder={t('جستجو بر اساس نام یا ایمیل')}
            value={searchTerm}
            onChange={handleSearchChange}
            variant="outlined"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </CardContent>
      </Card>
      
      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('نام کاربر')}</TableCell>
              <TableCell>{t('ایمیل')}</TableCell>
              <TableCell>{t('نقش کاربری')}</TableCell>
              <TableCell>{t('وضعیت')}</TableCell>
              <TableCell>{t('آخرین ورود')}</TableCell>
              <TableCell align="center">{t('عملیات')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredUsers.length > 0 ? (
              filteredUsers.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{user.fullName}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <Chip
                      icon={getRoleIcon(user.role)}
                      label={getRoleText(user.role, t)}
                      color={getRoleColor(user.role)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.isActive ? t('فعال') : t('غیرفعال')}
                      color={user.isActive ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatDate(user.lastLogin)}</TableCell>
                  <TableCell align="center">
                    <IconButton 
                      color="primary" 
                      onClick={() => handleEditClick(user)}
                      title={t('تغییر نقش')}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      color="error" 
                      onClick={() => handleDeleteClick(user)}
                      title={t('حذف کاربر')}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  {t('هیچ کاربری یافت نشد')}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Edit Role Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)}>
        <DialogTitle>
          {t('تغییر نقش کاربری')}
        </DialogTitle>
        <Divider />
        <DialogContent sx={{ pt: 2 }}>
          {selectedUser && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                <strong>{t('نام کاربر')}:</strong> {selectedUser.fullName}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                <strong>{t('ایمیل')}:</strong> {selectedUser.email}
              </Typography>
              <FormControl fullWidth margin="normal">
                <InputLabel id="role-select-label">{t('نقش کاربری')}</InputLabel>
                <Select
                  labelId="role-select-label"
                  value={selectedRole}
                  onChange={handleRoleChange}
                  label={t('نقش کاربری')}
                >
                  <MenuItem value={UserRole.USER}>{t('کاربر')}</MenuItem>
                  <MenuItem value={UserRole.RESELLER}>{t('فروشنده')}</MenuItem>
                  <MenuItem value={UserRole.ADMIN}>{t('مدیر')}</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setEditDialogOpen(false)}
          >
            {t('انصراف')}
          </Button>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleEditSave}
            disabled={!selectedRole}
          >
            {t('ذخیره')}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete User Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>
          {t('حذف کاربر')}
        </DialogTitle>
        <Divider />
        <DialogContent>
          {selectedUser && (
            <Typography>
              {t('آیا از حذف کاربر زیر اطمینان دارید؟')}
              <Box component="div" sx={{ mt: 2, mb: 1 }}>
                <strong>{t('نام')}:</strong> {selectedUser.fullName}
              </Box>
              <Box component="div">
                <strong>{t('ایمیل')}:</strong> {selectedUser.email}
              </Box>
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setDeleteDialogOpen(false)}
          >
            {t('انصراف')}
          </Button>
          <Button 
            variant="contained" 
            color="error" 
            onClick={handleDeleteConfirm}
          >
            {t('حذف')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RoleManager; 