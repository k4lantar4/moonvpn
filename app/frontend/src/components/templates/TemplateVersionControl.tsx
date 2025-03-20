import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  History as HistoryIcon,
  Compare as CompareIcon,
  Restore as RestoreIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useTemplates } from '../../hooks/useTemplates';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { Template } from '../../types/template';

interface Version {
  id: number;
  template_id: number;
  version: number;
  name: string;
  description: string;
  strategy: string;
  parameters: Record<string, any>;
  created_at: string;
  created_by: string;
}

interface VersionControlProps {
  template: Template;
}

export const TemplateVersionControl: React.FC<VersionControlProps> = ({ template }) => {
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<Version | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [compareVersion, setCompareVersion] = useState<Version | null>(null);

  useEffect(() => {
    loadVersions();
  }, [template.id]);

  const loadVersions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/templates/${template.id}/versions`);
      if (!response.ok) throw new Error('Failed to load versions');
      const data = await response.json();
      setVersions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load versions');
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (version: Version) => {
    if (!window.confirm(`Are you sure you want to rollback to version ${version.version}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/templates/${template.id}/versions/${version.id}/rollback`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to rollback version');
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rollback version');
    }
  };

  const renderVersionDiff = (current: Version, compare: Version) => {
    const changes: { field: string; current: any; previous: any }[] = [];

    // Compare fields
    if (current.name !== compare.name) {
      changes.push({ field: 'Name', current: current.name, previous: compare.name });
    }
    if (current.description !== compare.description) {
      changes.push({ field: 'Description', current: current.description, previous: compare.description });
    }
    if (current.strategy !== compare.strategy) {
      changes.push({ field: 'Strategy', current: current.strategy, previous: compare.strategy });
    }

    // Compare parameters
    Object.keys({ ...current.parameters, ...compare.parameters }).forEach(key => {
      if (current.parameters[key] !== compare.parameters[key]) {
        changes.push({
          field: `Parameter: ${key}`,
          current: current.parameters[key],
          previous: compare.parameters[key],
        });
      }
    });

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Field</TableCell>
              <TableCell>Current Version</TableCell>
              <TableCell>Previous Version</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {changes.map((change, index) => (
              <TableRow key={index}>
                <TableCell>{change.field}</TableCell>
                <TableCell>{change.current}</TableCell>
                <TableCell>{change.previous}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Version Control</Typography>
        <Box>
          <Tooltip title="View History">
            <IconButton onClick={() => setShowHistory(true)}>
              <HistoryIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Compare Versions">
            <IconButton onClick={() => setShowCompare(true)}>
              <CompareIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Version History Dialog */}
      <Dialog
        open={showHistory}
        onClose={() => setShowHistory(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Version History
          <IconButton
            onClick={() => setShowHistory(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Version</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Created At</TableCell>
                  <TableCell>Created By</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {versions.map((version) => (
                  <TableRow key={version.id}>
                    <TableCell>v{version.version}</TableCell>
                    <TableCell>{version.name}</TableCell>
                    <TableCell>{new Date(version.created_at).toLocaleString()}</TableCell>
                    <TableCell>{version.created_by}</TableCell>
                    <TableCell>
                      <Tooltip title="Rollback to this version">
                        <IconButton
                          onClick={() => handleRollback(version)}
                          color="primary"
                        >
                          <RestoreIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHistory(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Version Comparison Dialog */}
      <Dialog
        open={showCompare}
        onClose={() => setShowCompare(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Compare Versions
          <IconButton
            onClick={() => setShowCompare(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="subtitle1" gutterBottom>
                Select Version to Compare
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Version</TableCell>
                      <TableCell>Name</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {versions.map((version) => (
                      <TableRow
                        key={version.id}
                        hover
                        selected={compareVersion?.id === version.id}
                        onClick={() => setCompareVersion(version)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>v{version.version}</TableCell>
                        <TableCell>{version.name}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
            <Grid item xs={6}>
              {compareVersion && (
                <>
                  <Typography variant="subtitle1" gutterBottom>
                    Version Comparison
                  </Typography>
                  {renderVersionDiff(
                    {
                      id: template.id,
                      template_id: template.id,
                      version: versions.length + 1,
                      name: template.name,
                      description: template.description,
                      strategy: template.strategy,
                      parameters: template.parameters,
                      created_at: new Date().toISOString(),
                      created_by: 'Current',
                    },
                    compareVersion
                  )}
                </>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCompare(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 