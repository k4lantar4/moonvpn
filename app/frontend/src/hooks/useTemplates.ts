import { useState, useEffect } from 'react';
import { Template, TemplateCategory } from '../types/template';
import { api } from '../services/api';

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

interface ValidationRule {
  id: number;
  template_id: number;
  field: string;
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value: string;
  message: string;
  is_active: boolean;
}

interface TestResult {
  id: number;
  template_id: number;
  status: string;
  message: string;
  execution_time: number;
  parameters: Record<string, any>;
  errors?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

interface DocumentationOptions {
  format: 'markdown' | 'pdf';
  language: 'en' | 'fa';
}

interface UseTemplatesReturn {
  templates: Template[];
  categories: TemplateCategory[];
  loading: boolean;
  error: string | null;
  createTemplate: (data: Omit<Template, 'id' | 'created_at' | 'updated_at'>) => Promise<Template>;
  updateTemplate: (id: number, data: Partial<Template>) => Promise<Template>;
  deleteTemplate: (id: number) => Promise<void>;
  toggleTemplate: (id: number, isActive: boolean) => Promise<Template>;
  createCategory: (data: Omit<TemplateCategory, 'id' | 'created_at' | 'updated_at'>) => Promise<TemplateCategory>;
  updateCategory: (id: number, data: Partial<TemplateCategory>) => Promise<TemplateCategory>;
  deleteCategory: (id: number) => Promise<void>;
  importTemplates: (templates: Omit<Template, 'id' | 'created_at' | 'updated_at'>[]) => Promise<Template[]>;
  // Version control functions
  getTemplateVersions: (templateId: number) => Promise<Version[]>;
  rollbackTemplateVersion: (templateId: number, versionId: number) => Promise<Template>;
  compareTemplateVersions: (templateId: number, versionId1: number, versionId2: number) => Promise<{ changes: any[] }>;
  getValidationRules: (templateId: number) => Promise<ValidationRule[]>;
  addValidationRule: (templateId: number, rule: Omit<ValidationRule, 'id' | 'template_id' | 'created_at' | 'updated_at'>) => Promise<ValidationRule>;
  updateValidationRule: (templateId: number, ruleId: number, rule: Partial<ValidationRule>) => Promise<ValidationRule>;
  deleteValidationRule: (templateId: number, ruleId: number) => Promise<void>;
  toggleValidationRule: (templateId: number, ruleId: number) => Promise<ValidationRule>;
  validateTemplate: (templateId: number, data: Record<string, any>) => Promise<{ isValid: boolean; errors: Record<string, string> }>;
  runTemplateTest: (templateId: number, parameters: Record<string, any>) => Promise<TestResult>;
  getTestResults: (templateId: number, limit?: number) => Promise<TestResult[]>;
  generateDocumentation: (templateId: string, options: DocumentationOptions) => Promise<any>;
  downloadDocumentation: (templateId: string, options: DocumentationOptions) => Promise<void>;
}

export const useTemplates = (): UseTemplatesReturn => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
    loadCategories();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/templates');
      setTemplates(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await api.get('/templates/categories');
      setCategories(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load categories');
    }
  };

  const createTemplate = async (data: Omit<Template, 'id' | 'created_at' | 'updated_at'>) => {
    const response = await api.post('/templates', data);
    setTemplates([...templates, response.data]);
    return response.data;
  };

  const updateTemplate = async (id: number, data: Partial<Template>) => {
    const response = await api.put(`/templates/${id}`, data);
    setTemplates(templates.map(t => t.id === id ? response.data : t));
    return response.data;
  };

  const deleteTemplate = async (id: number) => {
    await api.delete(`/templates/${id}`);
    setTemplates(templates.filter(t => t.id !== id));
  };

  const toggleTemplate = async (id: number, isActive: boolean) => {
    const response = await api.patch(`/templates/${id}/toggle`, { is_active: isActive });
    setTemplates(templates.map(t => t.id === id ? response.data : t));
    return response.data;
  };

  const createCategory = async (data: Omit<TemplateCategory, 'id' | 'created_at' | 'updated_at'>) => {
    const response = await api.post('/templates/categories', data);
    setCategories([...categories, response.data]);
    return response.data;
  };

  const updateCategory = async (id: number, data: Partial<TemplateCategory>) => {
    const response = await api.put(`/templates/categories/${id}`, data);
    setCategories(categories.map(c => c.id === id ? response.data : c));
    return response.data;
  };

  const deleteCategory = async (id: number) => {
    await api.delete(`/templates/categories/${id}`);
    setCategories(categories.filter(c => c.id !== id));
  };

  const importTemplates = async (templates: Omit<Template, 'id' | 'created_at' | 'updated_at'>[]) => {
    const response = await api.post('/templates/import', { templates });
    setTemplates([...templates, ...response.data]);
    return response.data;
  };

  // Version control functions
  const getTemplateVersions = async (templateId: number): Promise<Version[]> => {
    const response = await api.get(`/templates/${templateId}/versions`);
    return response.data;
  };

  const rollbackTemplateVersion = async (templateId: number, versionId: number): Promise<Template> => {
    const response = await api.post(`/templates/${templateId}/versions/${versionId}/rollback`);
    setTemplates(templates.map(t => t.id === templateId ? response.data : t));
    return response.data;
  };

  const compareTemplateVersions = async (
    templateId: number,
    versionId1: number,
    versionId2: number
  ): Promise<{ changes: any[] }> => {
    const response = await api.get(`/templates/${templateId}/versions/compare`, {
      params: { version1: versionId1, version2: versionId2 },
    });
    return response.data;
  };

  const getValidationRules = async (templateId: number): Promise<ValidationRule[]> => {
    const response = await api.get(`/templates/${templateId}/validation-rules`);
    return response.data;
  };

  const addValidationRule = async (
    templateId: number,
    rule: Omit<ValidationRule, 'id' | 'template_id' | 'created_at' | 'updated_at'>
  ): Promise<ValidationRule> => {
    const response = await api.post(`/templates/${templateId}/validation-rules`, rule);
    setTemplates(templates.map(t => t.id === templateId ? { ...t, validation_rules: [...(t.validation_rules || []), response.data] } : t));
    return response.data;
  };

  const updateValidationRule = async (
    templateId: number,
    ruleId: number,
    rule: Partial<ValidationRule>
  ): Promise<ValidationRule> => {
    const response = await api.put(`/templates/${templateId}/validation-rules/${ruleId}`, rule);
    setTemplates(templates.map(t => t.id === templateId ? {
      ...t,
      validation_rules: t.validation_rules?.map(r => r.id === ruleId ? response.data : r)
    } : t));
    return response.data;
  };

  const deleteValidationRule = async (templateId: number, ruleId: number): Promise<void> => {
    await api.delete(`/templates/${templateId}/validation-rules/${ruleId}`);
    setTemplates(templates.map(t => t.id === templateId ? {
      ...t,
      validation_rules: t.validation_rules?.filter(r => r.id !== ruleId)
    } : t));
  };

  const toggleValidationRule = async (templateId: number, ruleId: number): Promise<ValidationRule> => {
    const response = await api.patch(`/templates/${templateId}/validation-rules/${ruleId}/toggle`);
    setTemplates(templates.map(t => t.id === templateId ? response.data : t));
    return response.data;
  };

  const validateTemplate = async (templateId: number, data: Record<string, any>): Promise<{ isValid: boolean; errors: Record<string, string> }> => {
    const response = await api.post(`/templates/${templateId}/validate`, data);
    return response.data;
  };

  const runTemplateTest = async (templateId: number, parameters: Record<string, any>): Promise<TestResult> => {
    try {
      const response = await fetch(`/api/v1/templates/${templateId}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ parameters }),
      });

      if (!response.ok) {
        throw new Error('Failed to run template test');
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error running template test:', error);
      throw error;
    }
  };

  const getTestResults = async (templateId: number, limit: number = 10): Promise<TestResult[]> => {
    try {
      const response = await fetch(`/api/v1/templates/${templateId}/test-results?limit=${limit}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch test results');
      }

      const results = await response.json();
      return results;
    } catch (error) {
      console.error('Error fetching test results:', error);
      throw error;
    }
  };

  const generateDocumentation = async (templateId: string, options: DocumentationOptions) => {
    try {
      const response = await api.post(`/templates/${templateId}/documentation`, options);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  };

  const downloadDocumentation = async (templateId: string, options: DocumentationOptions) => {
    try {
      const response = await api.post(
        `/templates/${templateId}/documentation/download`,
        options,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `template-${templateId}-documentation.${options.format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw handleApiError(error);
    }
  };

  return {
    templates,
    categories,
    loading,
    error,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    toggleTemplate,
    createCategory,
    updateCategory,
    deleteCategory,
    importTemplates,
    getTemplateVersions,
    rollbackTemplateVersion,
    compareTemplateVersions,
    getValidationRules,
    addValidationRule,
    updateValidationRule,
    deleteValidationRule,
    toggleValidationRule,
    validateTemplate,
    runTemplateTest,
    getTestResults,
    generateDocumentation,
    downloadDocumentation,
  };
}; 