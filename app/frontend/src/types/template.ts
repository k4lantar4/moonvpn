import { RecoveryStrategy } from './recovery';

export interface TemplateCategory {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ValidationRule {
  id: number;
  template_id: number;
  field: string;
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value: string;
  message: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Template {
  id: number;
  name: string;
  description: string | null;
  category_id: number | null;
  strategy: RecoveryStrategy;
  parameters: Record<string, string>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  category?: TemplateCategory;
  validation_rules?: ValidationRule[];
}

export interface TemplateFormData {
  name: string;
  description: string;
  category_id: number | null;
  strategy: RecoveryStrategy;
  parameters: Record<string, string>;
  is_active: boolean;
  validation_rules?: ValidationRule[];
}

export interface TemplateFilters {
  search: string;
  category: number | null;
  strategy: RecoveryStrategy | null;
  activeOnly: boolean;
} 