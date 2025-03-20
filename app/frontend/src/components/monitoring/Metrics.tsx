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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { monitoringService } from '../../services/monitoring';

interface MetricData {
  timestamp: number;
  value: number;
}

interface Metric {
  name: string;
  description: string;
  unit: string;
  data: MetricData[];
}

interface SystemMetrics {
  cpu: Metric;
  memory: Metric;
  disk: Metric;
  network: Metric;
  response_time: Metric;
  error_rate: Metric;
}

const timeRanges = [
  { label: 'Last Hour', value: '1h' },
  { label: 'Last 6 Hours', value: '6h' },
  { label: 'Last 24 Hours', value: '24h' },
  { label: 'Last 7 Days', value: '7d' }
];

export const Metrics: React.FC = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const [activeTab, setActiveTab] = useState(0);

  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['metrics', timeRange],
    queryFn: () => monitoringService.getMetrics(timeRange),
    refetchInterval: 60000 // Refresh every minute
  });

  const handleTimeRangeChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setTimeRange(event.target.value as string);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
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
        Error loading metrics. Please try again later.
      </Alert>
    );
  }

  if (!metrics) {
    return null;
  }

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const renderMetricChart = (metric: typeof metrics.cpu) => (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={metric.data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTimestamp}
        />
        <YAxis />
        <Tooltip
          labelFormatter={formatTimestamp}
          formatter={(value: number) => [`${value} ${metric.unit}`, metric.name]}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="value"
          name={metric.name}
          stroke="#8884d8"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderMetricCard = (metric: typeof metrics.cpu) => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {metric.name}
        </Typography>
        <Typography color="textSecondary" gutterBottom>
          {metric.description}
        </Typography>
        {renderMetricChart(metric)}
      </CardContent>
    </Card>
  );

  const renderSystemMetrics = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        {renderMetricCard(metrics.cpu)}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderMetricCard(metrics.memory)}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderMetricCard(metrics.disk)}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderMetricCard(metrics.network)}
      </Grid>
    </Grid>
  );

  const renderPerformanceMetrics = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        {renderMetricCard(metrics.response_time)}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderMetricCard(metrics.error_rate)}
      </Grid>
    </Grid>
  );

  return (
    <Box p={3}>
      {/* Controls */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={timeRange}
            onChange={handleTimeRangeChange}
            label="Time Range"
          >
            {timeRanges.map(range => (
              <MenuItem key={range.value} value={range.value}>
                {range.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="System Metrics" />
          <Tab label="Performance Metrics" />
        </Tabs>
      </Box>

      {/* Metrics Content */}
      <Box mt={3}>
        {activeTab === 0 ? renderSystemMetrics() : renderPerformanceMetrics()}
      </Box>
    </Box>
  );
}; 