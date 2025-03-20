import { useState, useCallback, useEffect, useRef } from 'react';
import { useApiRequest } from './useApiRequest';

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxSize?: number; // Maximum number of items to cache
}

interface CacheItem<T> {
  data: T;
  timestamp: number;
}

interface FetchOptions {
  useCache?: boolean;
  forceRefresh?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

export const useDataFetching = <T>(
  fetchFn: () => Promise<T>,
  cacheKey: string,
  options: CacheOptions & FetchOptions = {}
) => {
  const {
    ttl = 5 * 60 * 1000, // 5 minutes default
    maxSize = 100,
    useCache = true,
    forceRefresh = false,
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const cacheRef = useRef<Map<string, CacheItem<T>>>(new Map());
  const { isLoading, execute } = useApiRequest<T>();

  const getFromCache = useCallback(
    (key: string): T | null => {
      const cached = cacheRef.current.get(key);
      if (!cached) return null;

      const isExpired = Date.now() - cached.timestamp > ttl;
      if (isExpired) {
        cacheRef.current.delete(key);
        return null;
      }

      return cached.data;
    },
    [ttl]
  );

  const setToCache = useCallback(
    (key: string, data: T) => {
      // Remove oldest item if cache is full
      if (cacheRef.current.size >= maxSize) {
        const oldestKey = Array.from(cacheRef.current.entries()).sort(
          ([, a], [, b]) => a.timestamp - b.timestamp
        )[0][0];
        cacheRef.current.delete(oldestKey);
      }

      cacheRef.current.set(key, {
        data,
        timestamp: Date.now(),
      });
    },
    [maxSize]
  );

  const clearCache = useCallback(() => {
    cacheRef.current.clear();
  }, []);

  const fetchData = useCallback(
    async (options: FetchOptions = {}) => {
      const { forceRefresh = false, onSuccess, onError } = options;

      try {
        // Check cache first if not forcing refresh
        if (!forceRefresh && useCache) {
          const cachedData = getFromCache(cacheKey);
          if (cachedData) {
            setData(cachedData);
            onSuccess?.(cachedData);
            return;
          }
        }

        const result = await execute(fetchFn, {
          onSuccess: (data) => {
            setData(data);
            if (useCache) {
              setToCache(cacheKey, data);
            }
            onSuccess?.(data);
          },
          onError: (error) => {
            setError(error);
            onError?.(error);
          },
        });

        return result;
      } catch (error) {
        const err = error as Error;
        setError(err);
        onError?.(err);
        return null;
      }
    },
    [cacheKey, execute, fetchFn, getFromCache, setToCache, useCache]
  );

  // Initial fetch
  useEffect(() => {
    fetchData({ onSuccess, onError });
  }, [cacheKey, fetchData, onSuccess, onError]);

  const refresh = useCallback(() => {
    return fetchData({ forceRefresh: true, onSuccess, onError });
  }, [fetchData, onSuccess, onError]);

  const clearData = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return {
    data,
    error,
    isLoading,
    fetchData,
    refresh,
    clearData,
    clearCache,
  };
}; 