import { useState, useCallback } from 'react';
import { useSnackbar } from 'notistack';
import { FetchBaseQueryError } from '@reduxjs/toolkit/query';
import { SerializedError } from '@reduxjs/toolkit';

interface ApiError {
  message: string;
  code?: string;
  details?: unknown;
}

export const useApiError = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleError = useCallback(
    (error: FetchBaseQueryError | SerializedError | undefined) => {
      setIsError(true);
      let message = 'An unexpected error occurred';

      if (error) {
        if ('status' in error) {
          // FetchBaseQueryError
          const status = error.status;
          const data = error.data as ApiError;

          switch (status) {
            case 400:
              message = data.message || 'Bad Request';
              break;
            case 401:
              message = 'Unauthorized. Please log in again.';
              break;
            case 403:
              message = 'Access denied. You do not have permission to perform this action.';
              break;
            case 404:
              message = 'The requested resource was not found.';
              break;
            case 409:
              message = 'A conflict occurred. Please try again.';
              break;
            case 422:
              message = data.message || 'Validation error';
              break;
            case 429:
              message = 'Too many requests. Please try again later.';
              break;
            case 500:
              message = 'Internal server error. Please try again later.';
              break;
            default:
              message = data.message || `Error ${status}`;
          }
        } else if ('message' in error) {
          // SerializedError
          message = error.message || 'An unexpected error occurred';
        }
      }

      setErrorMessage(message);
      enqueueSnackbar(message, { variant: 'error' });

      return message;
    },
    [enqueueSnackbar]
  );

  const clearError = useCallback(() => {
    setIsError(false);
    setErrorMessage(null);
  }, []);

  return {
    isError,
    errorMessage,
    handleError,
    clearError,
  };
}; 