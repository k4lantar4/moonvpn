import { useCallback, useState } from 'react';
import { useApiRequest } from './useApiRequest';
import { useFormValidation } from './useFormValidation';

interface SubmitOptions<T> {
  validateBeforeSubmit?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  onValidationError?: (errors: Record<keyof T, string>) => void;
}

interface SubmitState<T> {
  isSubmitting: boolean;
  error: Error | null;
  data: T | null;
}

export const useFormSubmit = <T extends Record<string, any>>(
  submitFn: (values: T) => Promise<T>,
  validationRules: Record<keyof T, ((value: T[keyof T]) => string | undefined)[]>,
  options: SubmitOptions<T> = {}
) => {
  const {
    validateBeforeSubmit = true,
    onSuccess,
    onError,
    onValidationError,
  } = options;

  const [state, setState] = useState<SubmitState<T>>({
    isSubmitting: false,
    error: null,
    data: null,
  });

  const { execute } = useApiRequest<T>();

  const {
    values,
    errors,
    handleChange,
    handleBlur,
    validateForm,
    resetForm,
  } = useFormValidation<T>({} as T, validationRules);

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) {
        e.preventDefault();
      }

      setState((prev) => ({
        ...prev,
        isSubmitting: true,
        error: null,
      }));

      try {
        if (validateBeforeSubmit) {
          const isValid = validateForm();
          if (!isValid) {
            onValidationError?.(errors);
            setState((prev) => ({
              ...prev,
              isSubmitting: false,
            }));
            return;
          }
        }

        const result = await execute(
          () => submitFn(values),
          {
            onSuccess: (data) => {
              setState((prev) => ({
                ...prev,
                data,
                isSubmitting: false,
              }));
              onSuccess?.(data);
            },
            onError: (error) => {
              setState((prev) => ({
                ...prev,
                error,
                isSubmitting: false,
              }));
              onError?.(error);
            },
          }
        );

        return result;
      } catch (error) {
        const errorObj = error instanceof Error ? error : new Error('Submit failed');
        setState((prev) => ({
          ...prev,
          error: errorObj,
          isSubmitting: false,
        }));
        onError?.(errorObj);
      }
    },
    [
      values,
      errors,
      validateForm,
      submitFn,
      execute,
      validateBeforeSubmit,
      onSuccess,
      onError,
      onValidationError,
    ]
  );

  const handleReset = useCallback(() => {
    resetForm();
    setState({
      isSubmitting: false,
      error: null,
      data: null,
    });
  }, [resetForm]);

  const handleFieldChange = useCallback(
    (field: keyof T, value: T[keyof T]) => {
      handleChange(field, value);
    },
    [handleChange]
  );

  const handleFieldBlur = useCallback(
    (field: keyof T) => {
      handleBlur(field);
    },
    [handleBlur]
  );

  return {
    ...state,
    values,
    errors,
    handleSubmit,
    handleReset,
    handleFieldChange,
    handleFieldBlur,
  };
}; 