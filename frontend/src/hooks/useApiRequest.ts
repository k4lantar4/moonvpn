import { useCallback, useRef } from 'react';

interface RequestOptions<T> {
  retries?: number;
  retryDelay?: number;
  timeout?: number;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  onRetry?: (attempt: number) => void;
  onTimeout?: () => void;
}

interface RequestState<T> {
  isLoading: boolean;
  error: Error | null;
  data: T | null;
}

export const useApiRequest = <T>() => {
  const abortControllerRef = useRef<AbortController | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);

  const execute = useCallback(
    async (
      requestFn: () => Promise<T>,
      options: RequestOptions<T> = {}
    ): Promise<T> => {
      const {
        retries = 3,
        retryDelay = 1000,
        timeout = 30000,
        onSuccess,
        onError,
        onRetry,
        onTimeout,
      } = options;

      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      abortControllerRef.current = new AbortController();
      retryCountRef.current = 0;

      const executeRequest = async (): Promise<T> => {
        try {
          // Set up timeout
          const timeoutPromise = new Promise<never>((_, reject) => {
            timeoutRef.current = setTimeout(() => {
              reject(new Error('Request timeout'));
            }, timeout);
          });

          // Execute request with timeout
          const result = await Promise.race([
            requestFn(),
            timeoutPromise,
          ]);

          // Clear timeout
          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
          }

          // Handle success
          if (onSuccess) {
            onSuccess(result);
          }

          return result;
        } catch (error) {
          // Clear timeout
          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
          }

          // Handle timeout
          if (error instanceof Error && error.message === 'Request timeout') {
            if (onTimeout) {
              onTimeout();
            }
            throw error;
          }

          // Handle retry
          if (retryCountRef.current < retries) {
            retryCountRef.current++;
            if (onRetry) {
              onRetry(retryCountRef.current);
            }
            await new Promise((resolve) => setTimeout(resolve, retryDelay));
            return executeRequest();
          }

          // Handle error
          if (onError) {
            onError(error instanceof Error ? error : new Error('Unknown error'));
          }

          throw error;
        }
      };

      return executeRequest();
    },
    []
  );

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);

  return {
    execute,
    cancel,
  };
}; 