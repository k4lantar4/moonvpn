import { useState, useCallback } from 'react';

interface ValidationRule<T> {
  field: keyof T;
  validate: (value: any) => boolean;
  message: string;
}

interface ValidationResult<T> {
  isValid: boolean;
  errors: Partial<Record<keyof T, string>>;
}

export const useFormValidation = <T extends Record<string, any>>(
  initialValues: T,
  validationRules: ValidationRule<T>[]
) => {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});

  const validateField = useCallback(
    (field: keyof T, value: any): string | null => {
      const fieldRules = validationRules.filter((rule) => rule.field === field);
      for (const rule of fieldRules) {
        if (!rule.validate(value)) {
          return rule.message;
        }
      }
      return null;
    },
    [validationRules]
  );

  const validateForm = useCallback((): ValidationResult<T> => {
    const newErrors: Partial<Record<keyof T, string>> = {};
    let isValid = true;

    validationRules.forEach((rule) => {
      const error = validateField(rule.field, values[rule.field]);
      if (error) {
        newErrors[rule.field] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return { isValid, errors: newErrors };
  }, [values, validationRules, validateField]);

  const handleChange = useCallback(
    (field: keyof T, value: any) => {
      setValues((prev) => ({ ...prev, [field]: value }));
      
      // Clear error when user starts typing
      if (errors[field]) {
        const error = validateField(field, value);
        setErrors((prev) => ({
          ...prev,
          [field]: error || undefined,
        }));
      }
    },
    [errors, validateField]
  );

  const handleBlur = useCallback(
    (field: keyof T) => {
      setTouched((prev) => ({ ...prev, [field]: true }));
      const error = validateField(field, values[field]);
      setErrors((prev) => ({
        ...prev,
        [field]: error || undefined,
      }));
    },
    [values, validateField]
  );

  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  const isFieldValid = useCallback(
    (field: keyof T): boolean => {
      return !errors[field] && touched[field];
    },
    [errors, touched]
  );

  const isFieldInvalid = useCallback(
    (field: keyof T): boolean => {
      return !!errors[field] && touched[field];
    },
    [errors, touched]
  );

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    validateForm,
    resetForm,
    isFieldValid,
    isFieldInvalid,
  };
}; 