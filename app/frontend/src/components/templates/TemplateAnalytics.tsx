import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  useTheme,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useTemplates } from '../../hooks/useTemplates';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`analytics-tabpanel-${index}`}
    aria-labelledby={`analytics-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const TemplateAnalytics: React.FC = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const { templates, loading, error } = useTemplates();
  const [analyticsData, setAnalyticsData] = useState<any>(null);

  useEffect(() => {
    if (templates.length > 0) {
      // Calculate analytics data
      const data = {
        usageByCategory: templates.reduce((acc: any, template) => {
          const category = template.category?.name || 'Uncategorized';
          acc[category] = (acc[category] || 0) + 1;
          return acc;
        }, {}),
        successRate: templates.reduce((acc: any, template) => {
          const category = template.category?.name || 'Uncategorized';
          acc[category] = {
            total: (acc[category]?.total || 0) + 1,
            success: (acc[category]?.success || 0) + (template.is_active ? 1 : 0),
          };
          return acc;
        }, {}),
        usageTrend: Array.from({ length: 7 }, (_, i) => {
          const date = new Date();
          date.setDate(date.getDate() - i);
          return {
            date: date.toLocaleDateString(),
            usage: Math.floor(Math.random() * 10), // Replace with actual usage data
          };
        }).reverse(),
      };
      setAnalyticsData(data);
    }
  }, [templates]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!analyticsData) return <Alert severity="info">No analytics data available</Alert>;

  const categoryData = Object.entries(analyticsData.usageByCategory).map(([name, value]) => ({
    name,
    value,
  }));

  const successRateData = Object.entries(analyticsData.successRate).map(([name, data]: [string, any]) => ({
    name,
    rate: (data.success / data.total) * 100,
  }));

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Template Usage Analytics
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Usage Overview" />
            <Tab label="Success Rates" />
            <Tab label="Usage Trends" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Usage by Category
                </Typography>
                <PieChart width={400} height={300}>
                  <Pie
                    data={categoryData}
                    cx={200}
                    cy={150}
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Success Rates by Category
                </Typography>
                <BarChart width={400} height={300} data={successRateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="rate" fill="#8884d8" />
                </BarChart>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Success Rate Trends
                </Typography>
                <LineChart width={800} height={400} data={successRateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="rate" stroke="#8884d8" />
                </LineChart>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Daily Usage Trends
                </Typography>
                <LineChart width={800} height={400} data={analyticsData.usageTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="usage" stroke="#8884d8" />
                </LineChart>
              </Grid>
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>
    </Box>
  );
}; 