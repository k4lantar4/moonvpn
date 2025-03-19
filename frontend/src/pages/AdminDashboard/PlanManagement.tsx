import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  IconButton,
  Tooltip,
  Grid,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  InputAdornment,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ToggleOnIcon from '@mui/icons-material/ToggleOn';
import ToggleOffIcon from '@mui/icons-material/ToggleOff';

// Example data
const plans = [
  {
    id: 1,
    name: 'Basic',
    description: 'Basic plan with 50GB traffic',
    traffic: 50,
    days: 30,
    price: 100000,
    serverIds: [1, 2],
    active: true,
    isPopular: false,
    protocol: 'vmess',
    accounts: 45,
  },
  {
    id: 2,
    name: 'Premium',
    description: 'Premium plan with 100GB traffic',
    traffic: 100,
    days: 30,
    price: 180000,
    serverIds: [1, 2, 3],
    active: true,
    isPopular: true,
    protocol: 'vmess',
    accounts: 87,
  },
  {
    id: 3,
    name: 'Ultimate',
    description: 'Ultimate plan with 200GB traffic',
    traffic: 200,
    days: 30,
    price: 300000,
    serverIds: [1, 2, 3],
    active: true,
    isPopular: false,
    protocol: 'trojan',
    accounts: 32,
  },
  {
    id: 4,
    name: 'Basic Quarterly',
    description: 'Basic plan with 150GB traffic for 90 days',
    traffic: 150,
    days: 90,
    price: 270000,
    serverIds: [1, 2],
    active: false,
    isPopular: false,
    protocol: 'vmess',
    accounts: 0,
  },
];

// Server data for selection
const servers = [
  { id: 1, name: 'Server 1', location: 'US' },
  { id: 2, name: 'Server 2', location: 'DE' },
  { id: 3, name: 'Server 3', location: 'SG' },
];

// Protocol options
const protocols = [
  { value: 'vmess', label: 'VMess' },
  { value: 'vless', label: 'VLESS' },
  { value: 'trojan', label: 'Trojan' },
  { value: 'shadowsocks', label: 'Shadowsocks' },
];

const PlanManagement: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    traffic: 50,
    days: 30,
    price: 100000,
    serverIds: [] as number[],
    active: true,
    isPopular: false,
    protocol: 'vmess',
  });

  const handleOpenAddDialog = () => {
    setFormData({
      name: '',
      description: '',
      traffic: 50,
      days: 30,
      price: 100000,
      serverIds: [],
      active: true,
      isPopular: false,
      protocol: 'vmess',
    });
    setOpenAddDialog(true);
  };

  const handleCloseAddDialog = () => {
    setOpenAddDialog(false);
  };

  const handleOpenEditDialog = (plan: any) => {
    setSelectedPlan(plan);
    setFormData({
      name: plan.name,
      description: plan.description,
      traffic: plan.traffic,
      days: plan.days,
      price: plan.price,
      serverIds: plan.serverIds,
      active: plan.active,
      isPopular: plan.isPopular,
      protocol: plan.protocol,
    });
    setOpenEditDialog(true);
  };

  const handleCloseEditDialog = () => {
    setOpenEditDialog(false);
  };

  const handleOpenDeleteDialog = (plan: any) => {
    setSelectedPlan(plan);
    setOpenDeleteDialog(true);
  };

  const handleCloseDeleteDialog = () => {
    setOpenDeleteDialog(false);
  };

  const handleDuplicatePlan = (plan: any) => {
    setFormData({
      name: `${plan.name} (Copy)`,
      description: plan.description,
      traffic: plan.traffic,
      days: plan.days,
      price: plan.price,
      serverIds: [...plan.serverIds],
      active: true,
      isPopular: false,
      protocol: plan.protocol,
    });
    setOpenAddDialog(true);
  };

  const handleToggleActive = (plan: any) => {
    // TODO: Implement API call to toggle plan active status
    console.log('Toggle active:', plan);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleNumberInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: Number(value),
    }));
  };

  const handleSelectChange = (e: any) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: checked,
    }));
  };

  const handleAddPlan = () => {
    // TODO: Implement API call to add plan
    console.log('Add plan:', formData);
    setOpenAddDialog(false);
  };

  const handleEditPlan = () => {
    // TODO: Implement API call to edit plan
    console.log('Edit plan:', formData);
    setOpenEditDialog(false);
  };

  const handleDeletePlan = () => {
    // TODO: Implement API call to delete plan
    console.log('Delete plan:', selectedPlan);
    setOpenDeleteDialog(false);
  };

  const getProtocolLabel = (protocolValue: string) => {
    const protocol = protocols.find((p) => p.value === protocolValue);
    return protocol ? protocol.label : protocolValue;
  };

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ color: theme.palette.text.primary, fontWeight: 'bold' }}>
          {t('admin.plans.title')}
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenAddDialog}>
          {t('admin.plans.add_plan')}
        </Button>
      </Box>

      {/* Plans Grid */}
      <TableContainer component={Paper} sx={{ backgroundColor: theme.palette.background.paper }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('admin.plans.name')}</TableCell>
              <TableCell>{t('admin.plans.traffic')}</TableCell>
              <TableCell>{t('admin.plans.duration')}</TableCell>
              <TableCell>{t('admin.plans.protocol')}</TableCell>
              <TableCell>{t('admin.plans.servers')}</TableCell>
              <TableCell align="right">{t('admin.plans.price')}</TableCell>
              <TableCell>{t('admin.plans.accounts')}</TableCell>
              <TableCell>{t('admin.plans.status')}</TableCell>
              <TableCell>{t('admin.plans.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {plans.map((plan) => (
              <TableRow key={plan.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                      {plan.name}
                    </Typography>
                    {plan.isPopular && (
                      <Chip
                        label={t('admin.plans.popular')}
                        size="small"
                        color="primary"
                        sx={{ ml: 1, fontSize: '0.7rem' }}
                      />
                    )}
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {plan.description}
                  </Typography>
                </TableCell>
                <TableCell>{plan.traffic} GB</TableCell>
                <TableCell>{plan.days} {t('admin.plans.days')}</TableCell>
                <TableCell>{getProtocolLabel(plan.protocol)}</TableCell>
                <TableCell>
                  {plan.serverIds.map((serverId) => {
                    const server = servers.find((s) => s.id === serverId);
                    return server ? (
                      <Chip
                        key={serverId}
                        label={`${server.name} (${server.location})`}
                        size="small"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ) : null;
                  })}
                </TableCell>
                <TableCell align="right">
                  {plan.price.toLocaleString('fa-IR')} {t('common.currency')}
                </TableCell>
                <TableCell>{plan.accounts}</TableCell>
                <TableCell>
                  {plan.active ? (
                    <Chip
                      label={t('admin.plans.active')}
                      size="small"
                      color="success"
                      sx={{
                        backgroundColor: `${theme.palette.success.main}20`,
                        color: theme.palette.success.main,
                        fontWeight: 'medium',
                      }}
                    />
                  ) : (
                    <Chip
                      label={t('admin.plans.inactive')}
                      size="small"
                      sx={{
                        backgroundColor: `${theme.palette.text.secondary}20`,
                        color: theme.palette.text.secondary,
                        fontWeight: 'medium',
                      }}
                    />
                  )}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex' }}>
                    <Tooltip title={plan.active ? t('admin.plans.deactivate') : t('admin.plans.activate')}>
                      <IconButton size="small" onClick={() => handleToggleActive(plan)}>
                        {plan.active ? (
                          <ToggleOnIcon color="success" />
                        ) : (
                          <ToggleOffIcon color="disabled" />
                        )}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('admin.plans.duplicate')}>
                      <IconButton size="small" onClick={() => handleDuplicatePlan(plan)}>
                        <ContentCopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('admin.plans.edit')}>
                      <IconButton size="small" onClick={() => handleOpenEditDialog(plan)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('admin.plans.delete')}>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDeleteDialog(plan)}
                        disabled={plan.accounts > 0}
                      >
                        <DeleteIcon fontSize="small" color={plan.accounts > 0 ? 'disabled' : 'error'} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add Plan Dialog */}
      <Dialog open={openAddDialog} onClose={handleCloseAddDialog} maxWidth="md" fullWidth>
        <DialogTitle>{t('admin.plans.add_plan')}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.plans.name')}
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.plans.protocol')}</InputLabel>
                <Select
                  name="protocol"
                  value={formData.protocol}
                  onChange={handleSelectChange}
                  label={t('admin.plans.protocol')}
                >
                  {protocols.map((protocol) => (
                    <MenuItem key={protocol.value} value={protocol.value}>
                      {protocol.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('admin.plans.description')}
                name="description"
                multiline
                rows={2}
                value={formData.description}
                onChange={handleInputChange}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>{t('admin.plans.details')}</Divider>
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label={t('admin.plans.traffic')}
                name="traffic"
                type="number"
                value={formData.traffic}
                onChange={handleNumberInputChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">GB</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label={t('admin.plans.duration')}
                name="days"
                type="number"
                value={formData.days}
                onChange={handleNumberInputChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">{t('admin.plans.days')}</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label={t('admin.plans.price')}
                name="price"
                type="number"
                value={formData.price}
                onChange={handleNumberInputChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">{t('common.currency')}</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>{t('admin.plans.servers')}</Divider>
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.plans.available_servers')}</InputLabel>
                <Select
                  multiple
                  name="serverIds"
                  value={formData.serverIds}
                  onChange={handleSelectChange}
                  label={t('admin.plans.available_servers')}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as number[]).map((value) => {
                        const server = servers.find(s => s.id === value);
                        return server ? (
                          <Chip 
                            key={value} 
                            label={`${server.name} (${server.location})`}
                            size="small"
                          />
                        ) : null;
                      })}
                    </Box>
                  )}
                >
                  {servers.map((server) => (
                    <MenuItem key={server.id} value={server.id}>
                      {server.name} ({server.location})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>{t('admin.plans.options')}</Divider>
            </Grid>

            <Grid item xs={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.active}
                    onChange={handleSwitchChange}
                    name="active"
                    color="primary"
                  />
                }
                label={t('admin.plans.active')}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.isPopular}
                    onChange={handleSwitchChange}
                    name="isPopular"
                    color="primary"
                  />
                }
                label={t('admin.plans.mark_as_popular')}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAddDialog}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleAddPlan} 
            variant="contained"
            disabled={
              !formData.name ||
              !formData.traffic ||
              !formData.days ||
              !formData.price ||
              formData.serverIds.length === 0
            }
          >
            {t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Plan Dialog */}
      <Dialog open={openEditDialog} onClose={handleCloseEditDialog} maxWidth="md" fullWidth>
        <DialogTitle>{t('admin.plans.edit_plan')}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('admin.plans.name')}
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.plans.protocol')}</InputLabel>
                <Select
                  name="protocol"
                  value={formData.protocol}
                  onChange={handleSelectChange}
                  label={t('admin.plans.protocol')}
                >
                  {protocols.map((protocol) => (
                    <MenuItem key={protocol.value} value={protocol.value}>
                      {protocol.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('admin.plans.description')}
                name="description"
                multiline
                rows={2}
                value={formData.description}
                onChange={handleInputChange}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>{t('admin.plans.details')}</Divider>
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label={t('admin.plans.traffic')}
                name="traffic"
                type="number"
                value={formData.traffic}
                onChange={handleNumberInputChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">GB</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label={t('admin.plans.duration')}
                name="days"
                type="number"
                value={formData.days}
                onChange={handleNumberInputChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">{t('admin.plans.days')}</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label={t('admin.plans.price')}
                name="price"
                type="number"
                value={formData.price}
                onChange={handleNumberInputChange}
                InputProps={{
                  endAdornment: <InputAdornment position="end">{t('common.currency')}</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>{t('admin.plans.servers')}</Divider>
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>{t('admin.plans.available_servers')}</InputLabel>
                <Select
                  multiple
                  name="serverIds"
                  value={formData.serverIds}
                  onChange={handleSelectChange}
                  label={t('admin.plans.available_servers')}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as number[]).map((value) => {
                        const server = servers.find(s => s.id === value);
                        return server ? (
                          <Chip 
                            key={value} 
                            label={`${server.name} (${server.location})`}
                            size="small"
                          />
                        ) : null;
                      })}
                    </Box>
                  )}
                >
                  {servers.map((server) => (
                    <MenuItem key={server.id} value={server.id}>
                      {server.name} ({server.location})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>{t('admin.plans.options')}</Divider>
            </Grid>

            <Grid item xs={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.active}
                    onChange={handleSwitchChange}
                    name="active"
                    color="primary"
                  />
                }
                label={t('admin.plans.active')}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.isPopular}
                    onChange={handleSwitchChange}
                    name="isPopular"
                    color="primary"
                  />
                }
                label={t('admin.plans.mark_as_popular')}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleEditPlan} 
            variant="contained"
            disabled={
              !formData.name ||
              !formData.traffic ||
              !formData.days ||
              !formData.price ||
              formData.serverIds.length === 0
            }
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Plan Dialog */}
      <Dialog open={openDeleteDialog} onClose={handleCloseDeleteDialog}>
        <DialogTitle>{t('admin.plans.delete_plan')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('admin.plans.delete_confirm', { name: selectedPlan?.name })}
          </Typography>
          {selectedPlan?.accounts > 0 && (
            <Typography color="error" sx={{ mt: 2 }}>
              {t('admin.plans.delete_warning', { count: selectedPlan?.accounts })}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleDeletePlan} 
            color="error" 
            variant="contained"
            disabled={selectedPlan?.accounts > 0}
          >
            {t('common.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PlanManagement; 