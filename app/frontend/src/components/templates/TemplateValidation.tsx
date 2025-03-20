import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tooltip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { Template, ValidationRule } from '../../types/template';
import { useTemplates } from '../../hooks/useTemplates';

interface TemplateValidationProps {
  template: Template;
}

export const TemplateValidation: React.FC<TemplateValidationProps> = ({ template }) => {
  const [rules, setRules] = useState<ValidationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingRule, setEditingRule] = useState<ValidationRule | null>(null);
  const [newRule, setNewRule] = useState<Partial<ValidationRule>>({
    field: '',
    type: 'required',
    value: '',
    message: '',
    is_active: true,
  });

  const {
    getValidationRules,
    addValidationRule,
    updateValidationRule,
    deleteValidationRule,
  } = useTemplates();

  useEffect(() => {
    loadValidationRules();
  }, [template.id]);

  const loadValidationRules = async () => {
    try {
      setLoading(true);
      const data = await getValidationRules(template.id);
      setRules(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load validation rules');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRule = async () => {
    try {
      const data = await addValidationRule(template.id, newRule as Omit<ValidationRule, 'id' | 'template_id' | 'created_at' | 'updated_at'>);
      setRules([...rules, data]);
      setShowAddDialog(false);
      setNewRule({
        field: '',
        type: 'required',
        value: '',
        message: '',
        is_active: true,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add validation rule');
    }
  };

  const handleUpdateRule = async (rule: ValidationRule) => {
    try {
      const data = await updateValidationRule(template.id, rule.id, rule);
      setRules(rules.map(r => r.id === rule.id ? data : r));
      setEditingRule(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update validation rule');
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!window.confirm('Are you sure you want to delete this validation rule?')) return;

    try {
      await deleteValidationRule(template.id, ruleId);
      setRules(rules.filter(r => r.id !== ruleId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete validation rule');
    }
  };

  const handleToggleRule = async (rule: ValidationRule) => {
    try {
      const data = await updateValidationRule(template.id, rule.id, { is_active: !rule.is_active });
      setRules(rules.map(r => r.id === rule.id ? data : r));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle validation rule');
    }
  };

  if (loading) return <Typography>Loading validation rules...</Typography>;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Validation Rules</Typography>
        <Button
          startIcon={<AddIcon />}
          onClick={() => setShowAddDialog(true)}
          variant="contained"
        >
          Add Rule
        </Button>
      </Box>

      <Grid container spacing={2}>
        {rules.map((rule) => (
          <Grid item xs={12} key={rule.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle1">
                      {rule.field} - {rule.type}
                      {rule.is_active ? (
                        <CheckCircleIcon color="success" sx={{ ml: 1 }} />
                      ) : (
                        <ErrorIcon color="error" sx={{ ml: 1 }} />
                      )}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {rule.message}
                    </Typography>
                  </Box>
                  <Box>
                    <Tooltip title="Edit Rule">
                      <IconButton onClick={() => setEditingRule(rule)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Toggle Rule">
                      <IconButton onClick={() => handleToggleRule(rule)}>
                        {rule.is_active ? <CheckCircleIcon /> : <ErrorIcon />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Rule">
                      <IconButton onClick={() => handleDeleteRule(rule.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Add/Edit Rule Dialog */}
      <Dialog
        open={showAddDialog || !!editingRule}
        onClose={() => {
          setShowAddDialog(false);
          setEditingRule(null);
        }}
      >
        <DialogTitle>
          {editingRule ? 'Edit Validation Rule' : 'Add Validation Rule'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Field"
                value={editingRule?.field || newRule.field}
                onChange={(e) => {
                  if (editingRule) {
                    setEditingRule({ ...editingRule, field: e.target.value });
                  } else {
                    setNewRule({ ...newRule, field: e.target.value });
                  }
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Validation Type</InputLabel>
                <Select
                  value={editingRule?.type || newRule.type}
                  onChange={(e) => {
                    if (editingRule) {
                      setEditingRule({ ...editingRule, type: e.target.value as ValidationRule['type'] });
                    } else {
                      setNewRule({ ...newRule, type: e.target.value as ValidationRule['type'] });
                    }
                  }}
                >
                  <MenuItem value="required">Required</MenuItem>
                  <MenuItem value="min">Minimum Value</MenuItem>
                  <MenuItem value="max">Maximum Value</MenuItem>
                  <MenuItem value="pattern">Pattern</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Value"
                value={editingRule?.value || newRule.value}
                onChange={(e) => {
                  if (editingRule) {
                    setEditingRule({ ...editingRule, value: e.target.value });
                  } else {
                    setNewRule({ ...newRule, value: e.target.value });
                  }
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Error Message"
                value={editingRule?.message || newRule.message}
                onChange={(e) => {
                  if (editingRule) {
                    setEditingRule({ ...editingRule, message: e.target.value });
                  } else {
                    setNewRule({ ...newRule, message: e.target.value });
                  }
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={editingRule?.is_active ?? newRule.is_active}
                    onChange={(e) => {
                      if (editingRule) {
                        setEditingRule({ ...editingRule, is_active: e.target.checked });
                      } else {
                        setNewRule({ ...newRule, is_active: e.target.checked });
                      }
                    }}
                  />
                }
                label="Active"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setShowAddDialog(false);
              setEditingRule(null);
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={() => {
              if (editingRule) {
                handleUpdateRule(editingRule);
              } else {
                handleAddRule();
              }
            }}
            variant="contained"
          >
            {editingRule ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 