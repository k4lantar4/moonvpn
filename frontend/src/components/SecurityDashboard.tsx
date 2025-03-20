import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../services/api';

interface SecurityEvent {
  id: number;
  type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  ip: string;
  user_id?: number;
  metadata: any;
  timestamp: string;
}

interface SecurityStats {
  event_counts: {
    high: number;
    medium: number;
    low: number;
  };
  blocked_ips: number;
  recent_high_events: SecurityEvent[];
}

const severityColors = {
  high: 'error',
  medium: 'warning',
  low: 'info'
} as const;

export const SecurityDashboard: React.FC = () => {
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);

  // WebSocket connection for real-time updates
  const { lastMessage } = useWebSocket('ws://localhost:8000/api/v1/ws/security');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsResponse, eventsResponse] = await Promise.all([
          api.get('/api/v1/security/stats'),
          api.get('/api/v1/security/events')
        ]);
        setStats(statsResponse.data);
        setEvents(eventsResponse.data);
      } catch (err) {
        setError('Failed to fetch security data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Update data when new WebSocket message arrives
  useEffect(() => {
    if (lastMessage) {
      const event = JSON.parse(lastMessage);
      setEvents(prev => [event, ...prev]);
      // Update stats if needed
      if (stats) {
        setStats(prev => ({
          ...prev!,
          event_counts: {
            ...prev!.event_counts,
            [event.severity]: prev!.event_counts[event.severity] + 1
          }
        }));
      }
    }
  }, [lastMessage]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box m={2}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Security Dashboard
      </Typography>

      {/* Stats Overview */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Event Counts (24h)
            </Typography>
            <Box display="flex" gap={1}>
              <Chip
                label={`High: ${stats?.event_counts.high || 0}`}
                color="error"
                size="small"
              />
              <Chip
                label={`Medium: ${stats?.event_counts.medium || 0}`}
                color="warning"
                size="small"
              />
              <Chip
                label={`Low: ${stats?.event_counts.low || 0}`}
                color="info"
                size="small"
              />
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Blocked IPs
            </Typography>
            <Typography variant="h4">
              {stats?.blocked_ips || 0}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent High Severity Events
            </Typography>
            <Typography variant="h4">
              {stats?.recent_high_events.length || 0}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Events Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>IP</TableCell>
                <TableCell>User ID</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {events.map((event) => (
                <TableRow key={event.id}>
                  <TableCell>
                    {new Date(event.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>{event.type}</TableCell>
                  <TableCell>
                    <Chip
                      label={event.severity}
                      color={severityColors[event.severity]}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{event.description}</TableCell>
                  <TableCell>{event.ip}</TableCell>
                  <TableCell>{event.user_id || 'N/A'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}; 