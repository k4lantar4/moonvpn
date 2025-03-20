import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Code as CodeIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Download as DownloadIcon,
  Language as LanguageIcon,
} from '@mui/icons-material';
import { Template } from '../../types/template';
import { useTemplates } from '../../hooks/useTemplates';

interface TemplateDocumentationProps {
  template: Template;
}

type DocFormat = 'markdown' | 'pdf';
type Language = 'en' | 'fa';

export const TemplateDocumentation: React.FC<TemplateDocumentationProps> = ({ template }) => {
  const [format, setFormat] = useState<DocFormat>('markdown');
  const [language, setLanguage] = useState<Language>('en');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const { generateDocumentation, downloadDocumentation } = useTemplates();

  const handleGeneratePreview = async () => {
    try {
      setLoading(true);
      setError(null);
      const doc = await generateDocumentation(template.id, { format, language });
      setPreview(doc);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate documentation');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      setLoading(true);
      setError(null);
      await downloadDocumentation(template.id, { format, language });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download documentation');
    } finally {
      setLoading(false);
    }
  };

  const renderValidationRules = () => (
    <List>
      {template.validation_rules?.map((rule) => (
        <ListItem key={rule.id}>
          <ListItemIcon>
            {rule.is_active ? (
              <CheckCircleIcon color="success" />
            ) : (
              <ErrorIcon color="error" />
            )}
          </ListItemIcon>
          <ListItemText
            primary={`${rule.field} - ${rule.type}`}
            secondary={rule.message}
          />
        </ListItem>
      ))}
    </List>
  );

  const renderParameters = () => (
    <List>
      {Object.entries(template.parameters).map(([key, value]) => (
        <ListItem key={key}>
          <ListItemIcon>
            <CodeIcon />
          </ListItemIcon>
          <ListItemText
            primary={key}
            secondary={typeof value === 'string' ? value : JSON.stringify(value)}
          />
        </ListItem>
      ))}
    </List>
  );

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Template Documentation
      </Typography>

      <Card>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Document Format</InputLabel>
                <Select
                  value={format}
                  label="Document Format"
                  onChange={(e) => setFormat(e.target.value as DocFormat)}
                >
                  <MenuItem value="markdown">Markdown</MenuItem>
                  <MenuItem value="pdf">PDF</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Language</InputLabel>
                <Select
                  value={language}
                  label="Language"
                  onChange={(e) => setLanguage(e.target.value as Language)}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="fa">Persian</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <DescriptionIcon />}
                  onClick={handleGeneratePreview}
                  disabled={loading}
                >
                  Generate Preview
                </Button>
                <Button
                  variant="outlined"
                  startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
                  onClick={handleDownload}
                  disabled={loading}
                >
                  Download
                </Button>
              </Box>
            </Grid>

            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" gutterBottom>
                Template Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Parameters
                  </Typography>
                  {renderParameters()}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Validation Rules
                  </Typography>
                  {renderValidationRules()}
                </Grid>
              </Grid>
            </Grid>

            {preview && (
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Preview
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={10}
                  value={preview}
                  InputProps={{
                    readOnly: true,
                  }}
                />
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}; 