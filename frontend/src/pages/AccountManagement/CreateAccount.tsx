import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';

// Example data - replace with actual API data
const servers = [
  { id: 1, name: 'Server 1', location: 'US' },
  { id: 2, name: 'Server 2', location: 'UK' },
  { id: 3, name: 'Server 3', location: 'DE' },
];

const plans = [
  { id: 1, name: 'Basic', duration: 30, traffic: 50, price: 100000 },
  { id: 2, name: 'Premium', duration: 30, traffic: 100, price: 180000 },
  { id: 3, name: 'Ultimate', duration: 30, traffic: 200, price: 300000 },
];

const CreateAccount: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    server: '',
    plan: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name as string]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement API call to create account
    console.log('Form submitted:', formData);
  };

  const selectedPlan = plans.find((plan) => plan.id.toString() === formData.plan);

  return (
    <Box>
      <Card
        sx={{
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
        }}
      >
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3, color: theme.palette.text.primary }}>
            {t('account_management.create_new_account')}
          </Typography>

          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  label={t('account_management.account_name')}
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  helperText={t('account_management.account_name_help')}
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth required>
                  <InputLabel>{t('account_management.select_server')}</InputLabel>
                  <Select
                    name="server"
                    value={formData.server}
                    onChange={handleInputChange}
                    label={t('account_management.select_server')}
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
                <FormControl fullWidth required>
                  <InputLabel>{t('account_management.select_plan')}</InputLabel>
                  <Select
                    name="plan"
                    value={formData.plan}
                    onChange={handleInputChange}
                    label={t('account_management.select_plan')}
                  >
                    {plans.map((plan) => (
                      <MenuItem key={plan.id} value={plan.id}>
                        {plan.name} - {plan.traffic}GB - {plan.price.toLocaleString('fa-IR')} تومان
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {selectedPlan && (
                <Grid item xs={12}>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 1,
                      backgroundColor: theme.palette.background.default,
                    }}
                  >
                    <Typography variant="subtitle1" sx={{ mb: 1 }}>
                      {t('account_management.plan_details')}
                    </Typography>
                    <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                      {t('account_management.duration')}: {selectedPlan.duration} {t('account_management.days')}
                    </Typography>
                    <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                      {t('account_management.traffic_limit')}: {selectedPlan.traffic}GB
                    </Typography>
                    <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                      {t('account_management.price')}: {selectedPlan.price.toLocaleString('fa-IR')} تومان
                    </Typography>
                  </Box>
                </Grid>
              )}

              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  size="large"
                  disabled={!formData.name || !formData.server || !formData.plan}
                >
                  {t('account_management.create_account')}
                </Button>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default CreateAccount; 