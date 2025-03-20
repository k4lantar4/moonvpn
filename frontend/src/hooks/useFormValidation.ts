import { useCallback, useState } from 'react';

type ValidationRule<T> = (value: T) => string | undefined;
type ValidationRules<T> = Record<keyof T, ValidationRule<T[keyof T]>[]>;

interface ValidationState<T> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  isValid: boolean;
}

interface ValidationOptions {
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  validateOnSubmit?: boolean;
}

export const useFormValidation = <T extends Record<string, any>>(
  initialValues: T,
  validationRules: ValidationRules<T>,
  options: ValidationOptions = {}
) => {
  const {
    validateOnChange = true,
    validateOnBlur = true,
    validateOnSubmit = true,
  } = options;

  const [state, setState] = useState<ValidationState<T>>({
    values: initialValues,
    errors: {},
    touched: {},
    isValid: false,
  });

  const validateField = useCallback(
    (field: keyof T, value: T[keyof T]) => {
      const rules = validationRules[field];
      if (!rules) return undefined;

      for (const rule of rules) {
        const error = rule(value);
        if (error) return error;
      }

      return undefined;
    },
    [validationRules]
  );

  const validateForm = useCallback(() => {
    const errors: Partial<Record<keyof T, string>> = {};
    let isValid = true;

    Object.keys(validationRules).forEach((field) => {
      const fieldKey = field as keyof T;
      const value = state.values[fieldKey];
      const error = validateField(fieldKey, value);

      if (error) {
        errors[fieldKey] = error;
        isValid = false;
      }
    });

    setState((prev) => ({
      ...prev,
      errors,
      isValid,
    }));

    return isValid;
  }, [state.values, validationRules, validateField]);

  const handleChange = useCallback(
    (field: keyof T, value: T[keyof T]) => {
      setState((prev) => ({
        ...prev,
        values: {
          ...prev.values,
          [field]: value,
        },
        touched: {
          ...prev.touched,
          [field]: true,
        },
      }));

      if (validateOnChange) {
        const error = validateField(field, value);
        setState((prev) => ({
          ...prev,
          errors: {
            ...prev.errors,
            [field]: error,
          },
        }));
      }
    },
    [validateField, validateOnChange]
  );

  const handleBlur = useCallback(
    (field: keyof T) => {
      setState((prev) => ({
        ...prev,
        touched: {
          ...prev.touched,
          [field]: true,
        },
      }));

      if (validateOnBlur) {
        const error = validateField(field, state.values[field]);
        setState((prev) => ({
          ...prev,
          errors: {
            ...prev.errors,
            [field]: error,
          },
        }));
      }
    },
    [state.values, validateField, validateOnBlur]
  );

  const handleSubmit = useCallback(
    (onSubmit: (values: T) => void) => {
      if (validateOnSubmit) {
        const isValid = validateForm();
        if (!isValid) return;
      }

      onSubmit(state.values);
    },
    [state.values, validateForm, validateOnSubmit]
  );

  const resetForm = useCallback(() => {
    setState({
      values: initialValues,
      errors: {},
      touched: {},
      isValid: false,
    });
  }, [initialValues]);

  const setFieldValue = useCallback(
    (field: keyof T, value: T[keyof T]) => {
      setState((prev) => ({
        ...prev,
        values: {
          ...prev.values,
          [field]: value,
        },
      }));
    },
    []
  );

  const setFieldError = useCallback(
    (field: keyof T, error: string | undefined) => {
      setState((prev) => ({
        ...prev,
        errors: {
          ...prev.errors,
          [field]: error,
        },
      }));
    },
    []
  );

  return {
    values: state.values,
    errors: state.errors,
    touched: state.touched,
    isValid: state.isValid,
    handleChange,
    handleBlur,
    handleSubmit,
    validateForm,
    resetForm,
    setFieldValue,
    setFieldError,
  };
}; 