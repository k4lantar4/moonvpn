import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Chip,
  LinearProgress,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import SyncIcon from '@mui/icons-material/Sync';
import StorageIcon from '@mui/icons-material/Storage';

// Example data
const servers = [
  {
    id: 1,
    name: 'Server 1',
    address: 'server1.example.com',
    location: 'US',
    type: '3x-ui',
    status: 'online',
    version: '2.0.1',
    port: 443,
    username: 'admin',
    password: '********',
    trafficUsed: 500,
    trafficCapacity: 1000,
    users: 42,
    nodes: 3,
  },
  {
    id: 2,
    name: 'Server 2',
    address: 'server2.example.com',
    location: 'DE',
    type: '3x-ui',
    status: 'online',
    version: '2.0.1',
    port: 443,
    username: 'admin',
    password: '********',
    trafficUsed: 350,
    trafficCapacity: 1000,
    users: 28,
    nodes: 2,
  },
  {
    id: 3,
    name: 'Server 3',
    address: 'server3.example.com',
    location: 'SG',
    type: '3x-ui',
    status: 'offline',
    version: '2.0.0',
    port: 443,
    username: 'admin',
    password: '********',
    trafficUsed: 0,
    trafficCapacity: 1000,
    users: 0,
    nodes: 0,
  },
];

// Server locations
const locations = [
  { code: 'US', name: 'United States' },
  { code: 'DE', name: 'Germany' },
  { code: 'SG', name: 'Singapore' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'FR', name: 'France' },
  { code: 'UK', name: 'United Kingdom' },
];

const ServerManagement: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [selectedServer, setSelectedServer] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    location: '',
    port: 443,
    username: '',
    password: '',
    type: '3x-ui',
  });

  const handleOpenAddDialog = () => {
    setFormData({
      name: '',
      address: '',
      location: '',
      port: 443,
      username: '',
      password: '',
      type: '3x-ui',
    });
    setOpenAddDialog(true);
  };

  const handleCloseAddDialog = () => {
    setOpenAddDialog(false);
  };

  const handleOpenEditDialog = (server: any) => {
    setSelectedServer(server);
    setFormData({
      name: server.name,
      address: server.address,
      location: server.location,
      port: server.port,
      username: server.username,
      password: '',
      type: server.type,
    });
    setOpenEditDialog(true);
  };

  const handleCloseEditDialog = () => {
    setOpenEditDialog(false);
  };

  const handleOpenDeleteDialog = (server: any) => {
    setSelectedServer(server);
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

  const handleAddServer = () => {
    // TODO: Implement API call to add server
    console.log('Add server:', formData);
    setOpenAddDialog(false);
  };

  const handleEditServer = () => {
    // TODO: Implement API call to edit server
    console.log('Edit server:', formData);
    setOpenEditDialog(false);
  };

  const handleDeleteServer = () => {
    // TODO: Implement API call to delete server
    console.log('Delete server:', selectedServer);
    setOpenDeleteDialog(false);
  };

  const handleSyncServer = (server: any) => {
    // TODO: Implement API call to sync server
    console.log('Sync server:', server);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return theme.palette.success.main;
      case 'offline':
        return theme.palette.error.main;
      default:
        return theme.palette.warning.main;
    }
  };

  const formatTraffic = (gb: number) => {
    if (gb >= 1000) {
      return `${(gb / 1000).toFixed(2)} TB`;
    }
    return `${gb} GB`;
  };

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ color: theme.palette.text.primary, fontWeight: 'bold' }}>
          {t('admin.servers.title')}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenAddDialog}
        >
          {t('admin.servers.add_server')}
        </Button>
      </Box>

      {/* Server Stats Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card 
            sx={{ 
              backgroundColor: theme.palette.background.paper,
              borderTop: `4px solid ${theme.palette.primary.main}`,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <StorageIcon sx={{ fontSize: 48, color: theme.palette.primary.main, mr: 2 }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {t('admin.servers.total_servers')}
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {servers.length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card 
            sx={{ 
              backgroundColor: theme.palette.background.paper,
              borderTop: `4px solid ${theme.palette.success.main}`,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircleIcon sx={{ fontSize: 48, color: theme.palette.success.main, mr: 2 }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {t('admin.servers.online_servers')}
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {servers.filter(server => server.status === 'online').length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card 
            sx={{ 
              backgroundColor: theme.palette.background.paper,
              borderTop: `4px solid ${theme.palette.info.main}`,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ fontSize: 48, color: theme.palette.info.main, mr: 2 }}>
                  <Typography variant="h3" sx={{ fontWeight: 'bold' }}>Σ</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {t('admin.servers.total_users')}
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {servers.reduce((sum, server) => sum + server.users, 0)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Servers Table */}
      <TableContainer component={Paper} sx={{ backgroundColor: theme.palette.background.paper }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('admin.servers.name')}</TableCell>
              <TableCell>{t('admin.servers.address')}</TableCell>
              <TableCell>{t('admin.servers.location')}</TableCell>
              <TableCell>{t('admin.servers.status')}</TableCell>
              <TableCell>{t('admin.servers.traffic')}</TableCell>
              <TableCell>{t('admin.servers.users')}</TableCell>
              <TableCell>{t('admin.servers.nodes')}</TableCell>
              <TableCell>{t('admin.servers.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {servers.map((server) => (
              <TableRow key={server.id}>
                <TableCell>{server.name}</TableCell>
                <TableCell>{server.address}</TableCell>
                <TableCell>{server.location}</TableCell>
                <TableCell>
                  <Chip
                    label={t(`admin.servers.status.${server.status}`)}
                    size="small"
                    sx={{
                      backgroundColor: `${getStatusColor(server.status)}20`,
                      color: getStatusColor(server.status),
                      fontWeight: 'medium',
                    }}
                    icon={
                      server.status === 'online' ? (
                        <CheckCircleIcon style={{ color: getStatusColor(server.status) }} />
                      ) : (
                        <ErrorIcon style={{ color: getStatusColor(server.status) }} />
                      )
                    }
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ width: '100%', maxWidth: 150 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {formatTraffic(server.trafficUsed)} / {formatTraffic(server.trafficCapacity)}
                      </Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {Math.round((server.trafficUsed / server.trafficCapacity) * 100)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(server.trafficUsed / server.trafficCapacity) * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                      }}
                    />
                  </Box>
                </TableCell>
                <TableCell>{server.users}</TableCell>
                <TableCell>{server.nodes}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex' }}>
                    <Tooltip title={t('admin.servers.sync')}>
                      <IconButton
                        size="small"
                        onClick={() => handleSyncServer(server)}
                        disabled={server.status !== 'online'}
                      >
                        <SyncIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('admin.servers.edit')}>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenEditDialog(server)}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('admin.servers.delete')}>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDeleteDialog(server)}
                      >
                        <DeleteIcon fontSize="small" color="error" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add Server Dialog */}
      <Dialog open={openAddDialog} onClose={handleCloseAddDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{t('admin.servers.add_server')}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.servers.name')}
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.servers.address')}
                name="address"
                value={formData.address}
                onChange={handleInputChange}
                placeholder="example.com"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.servers.location')}</InputLabel>
                <Select
                  name="location"
                  value={formData.location}
                  onChange={handleSelectChange}
                  label={t('admin.servers.location')}
                >
                  {locations.map((location) => (
                    <MenuItem key={location.code} value={location.code}>
                      {location.name} ({location.code})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.servers.port')}
                name="port"
                type="number"
                value={formData.port}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.servers.type')}</InputLabel>
                <Select
                  name="type"
                  value={formData.type}
                  onChange={handleSelectChange}
                  label={t('admin.servers.type')}
                >
                  <MenuItem value="3x-ui">3x-UI</MenuItem>
                  <MenuItem value="x-ui">X-UI</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.servers.username')}
                name="username"
                value={formData.username}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('admin.servers.password')}
                name="password"
                type="password"
                value={formData.password}
                onChange={handleInputChange}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAddDialog}>{t('common.cancel')}</Button>
          <Button
            onClick={handleAddServer}
            variant="contained"
            disabled={
              !formData.name ||
              !formData.address ||
              !formData.location ||
              !formData.username ||
              !formData.password
            }
          >
            {t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Server Dialog */}
      <Dialog open={openEditDialog} onClose={handleCloseEditDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{t('admin.servers.edit_server')}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.servers.name')}
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.servers.address')}
                name="address"
                value={formData.address}
                onChange={handleInputChange}
                placeholder="example.com"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.servers.location')}</InputLabel>
                <Select
                  name="location"
                  value={formData.location}
                  onChange={handleSelectChange}
                  label={t('admin.servers.location')}
                >
                  {locations.map((location) => (
                    <MenuItem key={location.code} value={location.code}>
                      {location.name} ({location.code})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.servers.port')}
                name="port"
                type="number"
                value={formData.port}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.servers.type')}</InputLabel>
                <Select
                  name="type"
                  value={formData.type}
                  onChange={handleSelectChange}
                  label={t('admin.servers.type')}
                >
                  <MenuItem value="3x-ui">3x-UI</MenuItem>
                  <MenuItem value="x-ui">X-UI</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.servers.username')}
                name="username"
                value={formData.username}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('admin.servers.password')}
                name="password"
                type="password"
                value={formData.password}
                onChange={handleInputChange}
                helperText={t('admin.servers.leave_empty')}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>{t('common.cancel')}</Button>
          <Button
            onClick={handleEditServer}
            variant="contained"
            disabled={
              !formData.name ||
              !formData.address ||
              !formData.location ||
              !formData.username
            }
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Server Dialog */}
      <Dialog open={openDeleteDialog} onClose={handleCloseDeleteDialog}>
        <DialogTitle>{t('admin.servers.delete_server')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('admin.servers.delete_confirm', { name: selectedServer?.name })}
          </Typography>
          {selectedServer?.users > 0 && (
            <Typography color="error" sx={{ mt: 2 }}>
              {t('admin.servers.delete_warning', { count: selectedServer?.users })}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>{t('common.cancel')}</Button>
          <Button onClick={handleDeleteServer} color="error" variant="contained">
            {t('common.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ServerManagement; 