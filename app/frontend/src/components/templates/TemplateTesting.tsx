import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import { PlayArrow as PlayArrowIcon } from '@mui/icons-material';
import { Template } from '../../types/template';
import { useTemplates } from '../../hooks/useTemplates';

interface TemplateTestingProps {
  template: Template;
}

export const TemplateTesting: React.FC<TemplateTestingProps> = ({ template }) => {
  const [testParameters, setTestParameters] = useState<Record<string, string>>({});
  const [testResult, setTestResult] = useState<{
    isValid: boolean;
    errors: Record<string, string>;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { validateTemplate, runTemplateTest } = useTemplates();

  const handleParameterChange = (key: string, value: string) => {
    setTestParameters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleTestValidation = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await validateTemplate(template.id, testParameters);
      setTestResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to validate template');
    } finally {
      setLoading(false);
    }
  };

  const handleRunTest = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await runTemplateTest(template.id, testParameters);
      setTestResult({
        isValid: result.status === 'success',
        errors: result.errors || {},
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run template test');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Test Template
      </Typography>

      <Card>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Test Parameters
              </Typography>
              {Object.keys(template.parameters).map((key) => (
                <TextField
                  key={key}
                  fullWidth
                  label={key}
                  value={testParameters[key] || ''}
                  onChange={(e) => handleParameterChange(key, e.target.value)}
                  margin="normal"
                  error={!!testResult?.errors[key]}
                  helperText={testResult?.errors[key]}
                />
              ))}
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
                  onClick={handleTestValidation}
                  disabled={loading}
                >
                  Validate
                </Button>
                <Button
                  variant="outlined"
                  startIcon={loading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
                  onClick={handleRunTest}
                  disabled={loading}
                >
                  Run Test
                </Button>
              </Box>
            </Grid>

            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}

            {testResult && (
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Alert severity={testResult.isValid ? 'success' : 'error'}>
                  {testResult.isValid
                    ? 'Template validation successful!'
                    : 'Template validation failed. Please check the errors above.'}
                </Alert>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}; 