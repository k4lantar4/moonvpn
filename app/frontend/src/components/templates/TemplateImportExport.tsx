import React, { useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { useTemplates } from '../../hooks/useTemplates';
import { Template } from '../../types/template';

export const TemplateImportExport: React.FC = () => {
  const { templates, importTemplates, loading, error } = useTemplates();
  const [openDialog, setOpenDialog] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);

  const handleExport = () => {
    const dataStr = JSON.stringify(templates, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = 'recovery-templates.json';

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImporting(true);
    setImportError(null);

    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const content = e.target?.result as string;
          const importedTemplates = JSON.parse(content) as Template[];
          
          // Validate imported templates
          if (!Array.isArray(importedTemplates)) {
            throw new Error('Invalid template format: expected an array of templates');
          }

          // Validate each template
          importedTemplates.forEach((template, index) => {
            if (!template.name || !template.strategy) {
              throw new Error(`Invalid template at index ${index}: missing required fields`);
            }
          });

          await importTemplates(importedTemplates);
          setOpenDialog(false);
        } catch (err) {
          setImportError(err instanceof Error ? err.message : 'Failed to import templates');
        } finally {
          setImporting(false);
        }
      };
      reader.readAsText(file);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to read file');
      setImporting(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <Button
        variant="outlined"
        startIcon={<UploadIcon />}
        onClick={() => setOpenDialog(true)}
        aria-label="Import templates"
      >
        Import
      </Button>
      <Button
        variant="outlined"
        startIcon={<DownloadIcon />}
        onClick={handleExport}
        aria-label="Export templates"
      >
        Export
      </Button>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Import Templates</DialogTitle>
        <DialogContent>
          {importError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {importError}
            </Alert>
          )}
          <Typography variant="body1" sx={{ mb: 2 }}>
            Select a JSON file containing recovery templates to import.
            The file should contain an array of template objects with the following structure:
          </Typography>
          <pre style={{ 
            backgroundColor: '#f5f5f5', 
            padding: '1rem', 
            borderRadius: '4px',
            overflow: 'auto',
            fontSize: '0.875rem'
          }}>
            {JSON.stringify({
              name: "Template Name",
              description: "Template Description",
              strategy: "RecoveryStrategy",
              parameters: {},
              category_id: 1,
              is_active: true
            }, null, 2)}
          </pre>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            component="label"
            variant="contained"
            disabled={importing}
          >
            {importing ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Importing...
              </>
            ) : (
              'Select File'
            )}
            <input
              type="file"
              hidden
              accept=".json"
              onChange={handleImport}
            />
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 