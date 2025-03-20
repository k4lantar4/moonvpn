import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { theme } from './theme';
import { TemplateList } from './components/templates/TemplateList';
import { TemplateForm } from './components/templates/TemplateForm';
import { TemplateCategoryList } from './components/templates/TemplateCategoryList';
import { TemplateAnalytics } from './components/templates/TemplateAnalytics';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<TemplateList />} />
          <Route path="/templates/new" element={<TemplateForm />} />
          <Route path="/templates/:id/edit" element={<TemplateForm />} />
          <Route path="/templates/categories" element={<TemplateCategoryList />} />
          <Route path="/templates/analytics" element={<TemplateAnalytics />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App; 