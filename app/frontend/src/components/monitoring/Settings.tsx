import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { monitoringService } from '../../services/monitoring';

const metricOptions = [
  { value: 'cpu', label: 'CPU Usage' },
  { value: 'memory', label: 'Memory Usage' },
  { value: 'disk', label: 'Disk Usage' },
  { value: 'response_time', label: 'Response Time' },
  { value: 'error_rate', label: 'Error Rate' }
];

const operatorOptions = [
  { value: '>', label: 'Greater Than' },
  { value: '<', label: 'Less Than' },
  { value: '>=', label: 'Greater Than or Equal' },
  { value: '<=', label: 'Less Than or Equal' },
  { value: '==', label: 'Equal To' }
];

const severityOptions = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' }
];

const channelTypeOptions = [
  { value: 'email', label: 'Email' },
  { value: 'slack', label: 'Slack' },
  { value: 'telegram', label: 'Telegram' },
  { value: 'webhook', label: 'Webhook' }
];

export const Settings: React.FC = () => {
  const [selectedRule, setSelectedRule] = useState<number | null>(null);
  const [selectedChannel, setSelectedChannel] = useState<number | null>(null);
  const [isRuleDialogOpen, setIsRuleDialogOpen] = useState(false);
  const [isChannelDialogOpen, setIsChannelDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<typeof monitoringService.AlertRule | typeof monitoringService.NotificationChannel>>({});

  const queryClient = useQueryClient();

  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['monitoringSettings'],
    queryFn: () => monitoringService.getSettings()
  });

  const updateSettings = useMutation({
    mutationFn: (data: Partial<typeof monitoringService.MonitoringSettings>) =>
      monitoringService.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoringSettings'] });
    }
  });

  const handleRuleDialogOpen = (rule?: typeof monitoringService.AlertRule) => {
    setSelectedRule(rule?.id || null);
    setFormData(rule || {});
    setIsRuleDialogOpen(true);
  };

  const handleChannelDialogOpen = (channel?: typeof monitoringService.NotificationChannel) => {
    setSelectedChannel(channel?.id || null);
    setFormData(channel || {});
    setIsChannelDialogOpen(true);
  };

  const handleDialogClose = () => {
    setIsRuleDialogOpen(false);
    setIsChannelDialogOpen(false);
    setSelectedRule(null);
    setSelectedChannel(null);
    setFormData({});
  };

  const handleRuleSubmit = () => {
    if (!settings) return;

    const updatedRules = selectedRule
      ? settings.alertRules.map(rule =>
          rule.id === selectedRule ? formData as typeof monitoringService.AlertRule : rule
        )
      : [...settings.alertRules, formData as typeof monitoringService.AlertRule];

    updateSettings.mutate({ alertRules: updatedRules });
    handleDialogClose();
  };

  const handleChannelSubmit = () => {
    if (!settings) return;

    const updatedChannels = selectedChannel
      ? settings.notificationChannels.map(channel =>
          channel.id === selectedChannel ? formData as typeof monitoringService.NotificationChannel : channel
        )
      : [...settings.notificationChannels, formData as typeof monitoringService.NotificationChannel];

    updateSettings.mutate({ notificationChannels: updatedChannels });
    handleDialogClose();
  };

  const handleRuleDelete = (ruleId: number) => {
    if (!settings) return;

    const updatedRules = settings.alertRules.filter(rule => rule.id !== ruleId);
    updateSettings.mutate({ alertRules: updatedRules });
  };

  const handleChannelDelete = (channelId: number) => {
    if (!settings) return;

    const updatedChannels = settings.notificationChannels.filter(
      channel => channel.id !== channelId
    );
    updateSettings.mutate({ notificationChannels: updatedChannels });
  };

  const handleSettingChange = (key: string, value: any) => {
    if (!settings) return;

    updateSettings.mutate({
      [key]: value
    });
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
        Error loading settings. Please try again later.
      </Alert>
    );
  }

  if (!settings) {
    return null;
  }

  return (
    <Box p={3}>
      <Grid container spacing={3}>
        {/* General Settings */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                General Settings
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Data Retention Period (days)"
                    type="number"
                    value={settings.retentionPeriod}
                    onChange={(e) =>
                      handleSettingChange('retentionPeriod', parseInt(e.target.value))
                    }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Sampling Rate (%)"
                    type="number"
                    value={settings.samplingRate}
                    onChange={(e) =>
                      handleSettingChange('samplingRate', parseInt(e.target.value))
                    }
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Auto Scaling Settings */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Auto Scaling Settings
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoScaling.enabled}
                    onChange={(e) =>
                      handleSettingChange('autoScaling', {
                        ...settings.autoScaling,
                        enabled: e.target.checked
                      })
                    }
                  />
                }
                label="Enable Auto Scaling"
              />
              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Minimum Instances"
                    type="number"
                    value={settings.autoScaling.minInstances}
                    onChange={(e) =>
                      handleSettingChange('autoScaling', {
                        ...settings.autoScaling,
                        minInstances: parseInt(e.target.value)
                      })
                    }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Maximum Instances"
                    type="number"
                    value={settings.autoScaling.maxInstances}
                    onChange={(e) =>
                      handleSettingChange('autoScaling', {
                        ...settings.autoScaling,
                        maxInstances: parseInt(e.target.value)
                      })
                    }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Scale Up Threshold (%)"
                    type="number"
                    value={settings.autoScaling.scaleUpThreshold}
                    onChange={(e) =>
                      handleSettingChange('autoScaling', {
                        ...settings.autoScaling,
                        scaleUpThreshold: parseInt(e.target.value)
                      })
                    }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Scale Down Threshold (%)"
                    type="number"
                    value={settings.autoScaling.scaleDownThreshold}
                    onChange={(e) =>
                      handleSettingChange('autoScaling', {
                        ...settings.autoScaling,
                        scaleDownThreshold: parseInt(e.target.value)
                      })
                    }
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Alert Rules */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Alert Rules</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={() => handleRuleDialogOpen()}
                >
                  Add Rule
                </Button>
              </Box>
              <List>
                {settings.alertRules.map((rule) => (
                  <ListItem key={rule.id}>
                    <ListItemText
                      primary={rule.name}
                      secondary={`${rule.metric} ${rule.operator} ${rule.threshold} (${rule.severity})`}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => handleRuleDialogOpen(rule)}
                        sx={{ mr: 1 }}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        edge="end"
                        onClick={() => handleRuleDelete(rule.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Channels */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Notification Channels</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={() => handleChannelDialogOpen()}
                >
                  Add Channel
                </Button>
              </Box>
              <List>
                {settings.notificationChannels.map((channel) => (
                  <ListItem key={channel.id}>
                    <ListItemText
                      primary={channel.name}
                      secondary={channel.type}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => handleChannelDialogOpen(channel)}
                        sx={{ mr: 1 }}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        edge="end"
                        onClick={() => handleChannelDelete(channel.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alert Rule Dialog */}
      <Dialog open={isRuleDialogOpen} onClose={handleDialogClose}>
        <DialogTitle>
          {selectedRule ? 'Edit Alert Rule' : 'Add Alert Rule'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Name"
              value={formData.name || ''}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
            />
            <FormControl fullWidth>
              <InputLabel>Metric</InputLabel>
              <Select
                value={formData.metric || ''}
                onChange={(e) =>
                  setFormData({ ...formData, metric: e.target.value })
                }
                label="Metric"
              >
                {metricOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Operator</InputLabel>
              <Select
                value={formData.operator || ''}
                onChange={(e) =>
                  setFormData({ ...formData, operator: e.target.value })
                }
                label="Operator"
              >
                {operatorOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Threshold"
              type="number"
              value={formData.threshold || ''}
              onChange={(e) =>
                setFormData({ ...formData, threshold: parseFloat(e.target.value) })
              }
            />
            <FormControl fullWidth>
              <InputLabel>Severity</InputLabel>
              <Select
                value={formData.severity || ''}
                onChange={(e) =>
                  setFormData({ ...formData, severity: e.target.value })
                }
                label="Severity"
              >
                {severityOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.enabled || false}
                  onChange={(e) =>
                    setFormData({ ...formData, enabled: e.target.checked })
                  }
                />
              }
              label="Enabled"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          <Button onClick={handleRuleSubmit} variant="contained" color="primary">
            {selectedRule ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Channel Dialog */}
      <Dialog open={isChannelDialogOpen} onClose={handleDialogClose}>
        <DialogTitle>
          {selectedChannel ? 'Edit Notification Channel' : 'Add Notification Channel'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Name"
              value={formData.name || ''}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
            />
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={formData.type || ''}
                onChange={(e) =>
                  setFormData({ ...formData, type: e.target.value })
                }
                label="Type"
              >
                {channelTypeOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.enabled || false}
                  onChange={(e) =>
                    setFormData({ ...formData, enabled: e.target.checked })
                  }
                />
              }
              label="Enabled"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          <Button onClick={handleChannelSubmit} variant="contained" color="primary">
            {selectedChannel ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 