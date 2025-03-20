import { useState, useCallback } from 'react';
import { useApiError } from './useApiError';

interface ApiRequestOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  onFinally?: () => void;
}

export const useApiRequest = <T>() => {
  const [isLoading, setIsLoading] = useState(false);
  const { handleError, clearError } = useApiError();

  const execute = useCallback(
    async (
      requestFn: () => Promise<T>,
      options: ApiRequestOptions<T> = {}
    ): Promise<T | null> => {
      setIsLoading(true);
      clearError();

      try {
        const data = await requestFn();
        options.onSuccess?.(data);
        return data;
      } catch (error) {
        const errorMessage = handleError(error as Error);
        options.onError?.(error as Error);
        return null;
      } finally {
        setIsLoading(false);
        options.onFinally?.();
      }
    },
    [clearError, handleError]
  );

  const executeWithRetry = useCallback(
    async (
      requestFn: () => Promise<T>,
      options: ApiRequestOptions<T> & { maxRetries?: number } = {}
    ): Promise<T | null> => {
      const { maxRetries = 3, ...restOptions } = options;
      let lastError: Error | null = null;

      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          const data = await execute(requestFn, {
            ...restOptions,
            onError: (error) => {
              lastError = error;
              restOptions.onError?.(error);
            },
          });

          if (data !== null) {
            return data;
          }
        } catch (error) {
          lastError = error as Error;
          restOptions.onError?.(error as Error);
        }

        if (attempt < maxRetries) {
          // Exponential backoff
          await new Promise((resolve) =>
            setTimeout(resolve, Math.pow(2, attempt) * 1000)
          );
        }
      }

      return null;
    },
    [execute]
  );

  return {
    isLoading,
    execute,
    executeWithRetry,
  };
}; 