import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Grid,
  FormControlLabel,
  Switch,
  IconButton,
  Tooltip,
  Alert,
  Card,
  CardContent,
  Divider,
  CircularProgress,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { Template } from '../../types/template';
import { RecoveryStrategy } from '../../types/recovery';
import { useTemplates } from '../../hooks/useTemplates';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { TemplateVersionControl } from './TemplateVersionControl';
import { TemplateValidation } from './TemplateValidation';
import { TemplateTesting } from './TemplateTesting';

interface TemplateFormData {
  name: string;
  description: string;
  category_id: number | null;
  strategy: RecoveryStrategy;
  parameters: Record<string, string>;
  is_active: boolean;
}

export const TemplateForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TemplateFormData>();
  const { categories, loading, error, createTemplate, updateTemplate, getTemplate, templates, validateTemplate } = useTemplates();
  const [parameterKeys, setParameterKeys] = useState<string[]>(['']);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<Template>>({
    name: '',
    description: '',
    strategy: '',
    parameters: {},
    category_id: undefined,
    is_active: true,
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (id) {
      const loadTemplate = async () => {
        const template = await getTemplate(parseInt(id));
        if (template) {
          setValue('name', template.name);
          setValue('description', template.description || '');
          setValue('category_id', template.category_id);
          setValue('strategy', template.strategy);
          setValue('parameters', template.parameters);
          setValue('is_active', template.is_active);
          setParameterKeys(Object.keys(template.parameters));
          setFormData(template);
        }
      };
      loadTemplate();
    }
  }, [id, getTemplate, setValue]);

  const handleAddParameter = () => {
    setParameterKeys([...parameterKeys, '']);
  };

  const handleRemoveParameter = (index: number) => {
    setParameterKeys(parameterKeys.filter((_, i) => i !== index));
  };

  const handleParameterChange = (index: number, value: string) => {
    const newKeys = [...parameterKeys];
    newKeys[index] = value;
    setParameterKeys(newKeys);
  };

  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setValidationErrors({});

    try {
      const parameters: Record<string, string> = {};
      parameterKeys.forEach((key) => {
        if (key) {
          parameters[key] = formData.parameters[key] || '';
        }
      });

      const templateData = {
        ...formData,
        parameters,
      };

      if (id) {
        const validationResult = await validateTemplate(parseInt(id), templateData);
        if (!validationResult.isValid) {
          setValidationErrors(validationResult.errors);
          return;
        }
        await updateTemplate(parseInt(id), templateData);
      } else {
        await createTemplate(templateData as Omit<Template, 'id' | 'created_at' | 'updated_at'>);
      }

      navigate('/templates');
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name as string]: value,
    }));
    // Clear validation error when field is modified
    if (validationErrors[name as string]) {
      setValidationErrors({ ...validationErrors, [name as string]: '' });
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {id ? 'Edit Template' : 'Create Template'}
      </Typography>

      <Card>
        <CardContent>
          <form onSubmit={handleSubmitForm}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  error={!!validationErrors.name}
                  helperText={validationErrors.name}
                  required
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  multiline
                  rows={4}
                  error={!!validationErrors.description}
                  helperText={validationErrors.description}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth error={!!validationErrors.category_id}>
                  <InputLabel>Category</InputLabel>
                  <Select
                    name="category_id"
                    value={formData.category_id || ''}
                    onChange={handleChange}
                  >
                    <MenuItem value="">None</MenuItem>
                    {categories.map((category) => (
                      <MenuItem key={category.id} value={category.id}>
                        {category.name}
                      </MenuItem>
                    ))}
                  </Select>
                  {validationErrors.category_id && (
                    <Typography color="error" variant="caption">
                      {validationErrors.category_id}
                    </Typography>
                  )}
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth error={!!validationErrors.strategy}>
                  <InputLabel>Strategy</InputLabel>
                  <Select
                    name="strategy"
                    value={formData.strategy}
                    onChange={handleChange}
                  >
                    {Object.values(RecoveryStrategy).map((strategy) => (
                      <MenuItem key={strategy} value={strategy}>
                        {strategy}
                      </MenuItem>
                    ))}
                  </Select>
                  {validationErrors.strategy && (
                    <Typography color="error" variant="caption">
                      {validationErrors.strategy}
                    </Typography>
                  )}
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Parameters
                </Typography>
                {parameterKeys.map((key, index) => (
                  <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
                    <Grid item xs={5}>
                      <TextField
                        fullWidth
                        label="Parameter Name"
                        value={key}
                        onChange={(e) => handleParameterChange(index, e.target.value)}
                        error={!!validationErrors[`parameters.${key}`]}
                        helperText={validationErrors[`parameters.${key}`]}
                      />
                    </Grid>
                    <Grid item xs={5}>
                      <TextField
                        fullWidth
                        label="Default Value"
                        value={formData.parameters[key] || ''}
                        onChange={(e) => handleChange({ target: { name: `parameters.${key}`, value: e.target.value } })}
                        error={!!validationErrors[`parameters.${key}`]}
                        helperText={validationErrors[`parameters.${key}`]}
                      />
                    </Grid>
                    <Grid item xs={2}>
                      <IconButton onClick={() => handleRemoveParameter(index)}>
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                ))}
                <Button
                  startIcon={<AddIcon />}
                  onClick={handleAddParameter}
                  sx={{ mt: 1 }}
                >
                  Add Parameter
                </Button>
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Controller
                      name="is_active"
                      control={control}
                      render={({ field }) => (
                        <Switch
                          {...field}
                          checked={field.value}
                          aria-label="Template active status"
                        />
                      )}
                    />
                  }
                  label="Active"
                />
              </Grid>

              {submitError && (
                <Grid item xs={12}>
                  <Alert severity="error">{submitError}</Alert>
                </Grid>
              )}

              {id && (
                <>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 3 }} />
                    <TemplateVersionControl template={formData as Template} />
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Validation Rules
                    </Typography>
                    <Paper sx={{ p: 2 }}>
                      <TemplateValidation template={formData as Template} />
                    </Paper>
                  </Grid>
                </>
              )}

              {template && (
                <Box sx={{ mt: 4 }}>
                  <Divider sx={{ mb: 3 }} />
                  <TemplateTesting template={template} />
                </Box>
              )}

              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                  <Button
                    variant="outlined"
                    onClick={() => navigate('/templates')}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={Object.keys(errors).length > 0 || Object.keys(validationErrors).length > 0}
                    startIcon={loading && <CircularProgress size={20} />}
                  >
                    {id ? 'Update Template' : 'Create Template'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}; 