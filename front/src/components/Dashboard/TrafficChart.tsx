import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '@mui/material';
import { useTranslation } from 'react-i18next';

// Example data - replace with actual API data
const data = [
  { date: '2024-03-01', upload: 4000, download: 2400 },
  { date: '2024-03-02', upload: 3000, download: 1398 },
  { date: '2024-03-03', upload: 2000, download: 9800 },
  { date: '2024-03-04', upload: 2780, download: 3908 },
  { date: '2024-03-05', upload: 1890, download: 4800 },
  { date: '2024-03-06', upload: 2390, download: 3800 },
  { date: '2024-03-07', upload: 3490, download: 4300 },
];

const TrafficChart: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();

  const formatYAxis = (value: number) => {
    return `${(value / 1024 / 1024).toFixed(1)} GB`;
  };

  const formatTooltip = (value: number) => {
    return `${(value / 1024 / 1024).toFixed(1)} GB`;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={data}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
        <XAxis
          dataKey="date"
          stroke={theme.palette.text.secondary}
          tickFormatter={(value) => new Date(value).toLocaleDateString('fa-IR')}
        />
        <YAxis
          stroke={theme.palette.text.secondary}
          tickFormatter={formatYAxis}
        />
        <Tooltip
          formatter={formatTooltip}
          labelFormatter={(value) => new Date(value).toLocaleDateString('fa-IR')}
        />
        <Line
          type="monotone"
          dataKey="upload"
          stroke={theme.palette.primary.main}
          name={t('dashboard.upload')}
        />
        <Line
          type="monotone"
          dataKey="download"
          stroke={theme.palette.secondary.main}
          name={t('dashboard.download')}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default TrafficChart; 