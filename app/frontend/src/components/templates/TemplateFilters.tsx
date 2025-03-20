import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Paper,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { Template } from '../../types/template';
import { RecoveryStrategy } from '../../types/recovery';

interface TemplateFiltersProps {
  templates: Template[];
  onFilterChange: (filteredTemplates: Template[]) => void;
}

export const TemplateFilters: React.FC<TemplateFiltersProps> = ({
  templates,
  onFilterChange,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState<string>('');
  const [strategy, setStrategy] = useState<string>('');
  const [activeOnly, setActiveOnly] = useState(false);

  const categories = Array.from(
    new Set(templates.map((template) => template.category?.name).filter(Boolean))
  );

  useEffect(() => {
    let filtered = [...templates];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (template) =>
          template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          template.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply category filter
    if (category) {
      filtered = filtered.filter(
        (template) => template.category?.name === category
      );
    }

    // Apply strategy filter
    if (strategy) {
      filtered = filtered.filter(
        (template) => template.strategy === strategy
      );
    }

    // Apply active status filter
    if (activeOnly) {
      filtered = filtered.filter((template) => template.is_active);
    }

    onFilterChange(filtered);
  }, [searchTerm, category, strategy, activeOnly, templates, onFilterChange]);

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Filters
      </Typography>
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 2,
          alignItems: isMobile ? 'stretch' : 'center',
        }}
      >
        <TextField
          label="Search"
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ minWidth: 200 }}
        />

        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Category</InputLabel>
          <Select
            value={category}
            label="Category"
            onChange={(e) => setCategory(e.target.value)}
          >
            <MenuItem value="">All Categories</MenuItem>
            {categories.map((cat) => (
              <MenuItem key={cat} value={cat}>
                {cat}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Strategy</InputLabel>
          <Select
            value={strategy}
            label="Strategy"
            onChange={(e) => setStrategy(e.target.value)}
          >
            <MenuItem value="">All Strategies</MenuItem>
            {Object.values(RecoveryStrategy).map((strat) => (
              <MenuItem key={strat} value={strat}>
                {strat}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              aria-label="Show active templates only"
            />
          }
          label="Active Only"
        />
      </Box>
    </Paper>
  );
}; 