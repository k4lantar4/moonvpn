import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { monitoringService } from '../../services/monitoring';

export const Dashboard: React.FC = () => {
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['metrics', '1h'],
    queryFn: () => monitoringService.getMetrics('1h'),
    refetchInterval: 60000 // Refresh every minute
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => monitoringService.getAlerts({ status: 'active' }),
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  if (isLoading || alertsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Error loading dashboard data. Please try again later.
      </Alert>
    );
  }

  if (!metrics || !alerts) {
    return null;
  }

  const activeAlerts = alerts.filter(alert => alert.status === 'active');
  const criticalAlerts = activeAlerts.filter(alert => alert.severity === 'critical');
  const highAlerts = activeAlerts.filter(alert => alert.severity === 'high');

  return (
    <Box p={3}>
      <Grid container spacing={3}>
        {/* System Health */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Typography color="textSecondary" gutterBottom>
                Active Alerts: {activeAlerts.length}
              </Typography>
              <Typography color="error" gutterBottom>
                Critical: {criticalAlerts.length}
              </Typography>
              <Typography color="warning.main" gutterBottom>
                High: {highAlerts.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* CPU Usage */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                CPU Usage
              </Typography>
              <Typography color="textSecondary" gutterBottom>
                Current: {metrics.cpu.data[metrics.cpu.data.length - 1].value}%
              </Typography>
              <Typography color="textSecondary">
                Average: {(metrics.cpu.data.reduce((acc, curr) => acc + curr.value, 0) / metrics.cpu.data.length).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Memory Usage */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Memory Usage
              </Typography>
              <Typography color="textSecondary" gutterBottom>
                Current: {metrics.memory.data[metrics.memory.data.length - 1].value}%
              </Typography>
              <Typography color="textSecondary">
                Average: {(metrics.memory.data.reduce((acc, curr) => acc + curr.value, 0) / metrics.memory.data.length).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Response Time */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Response Time
              </Typography>
              <Typography color="textSecondary" gutterBottom>
                Current: {metrics.response_time.data[metrics.response_time.data.length - 1].value}ms
              </Typography>
              <Typography color="textSecondary">
                Average: {(metrics.response_time.data.reduce((acc, curr) => acc + curr.value, 0) / metrics.response_time.data.length).toFixed(1)}ms
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Error Rate */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Error Rate
              </Typography>
              <Typography color="textSecondary" gutterBottom>
                Current: {metrics.error_rate.data[metrics.error_rate.data.length - 1].value}%
              </Typography>
              <Typography color="textSecondary">
                Average: {(metrics.error_rate.data.reduce((acc, curr) => acc + curr.value, 0) / metrics.error_rate.data.length).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}; 