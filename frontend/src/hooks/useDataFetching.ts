import { useCallback, useState, useEffect, useRef } from 'react';

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxSize?: number; // Maximum number of items in cache
}

interface CacheItem<T> {
  data: T;
  timestamp: number;
}

interface FetchOptions {
  useCache?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  onLoading?: (isLoading: boolean) => void;
}

interface FetchingState<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
}

export const useDataFetching = <T>(
  fetchFn: () => Promise<T>,
  options: FetchOptions & CacheOptions = {}
) => {
  const {
    useCache = true,
    ttl = 5 * 60 * 1000, // 5 minutes
    maxSize = 100,
    onSuccess,
    onError,
    onLoading,
  } = options;

  const [state, setState] = useState<FetchingState<T>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const cacheRef = useRef<Map<string, CacheItem<T>>>(new Map());

  const getFromCache = useCallback(
    (key: string): T | null => {
      const cachedItem = cacheRef.current.get(key);
      if (!cachedItem) return null;

      const isExpired = Date.now() - cachedItem.timestamp > ttl;
      if (isExpired) {
        cacheRef.current.delete(key);
        return null;
      }

      return cachedItem.data;
    },
    [ttl]
  );

  const setToCache = useCallback(
    (key: string, data: T) => {
      if (cacheRef.current.size >= maxSize) {
        // Remove oldest item
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
    async (key: string) => {
      if (useCache) {
        const cachedData = getFromCache(key);
        if (cachedData) {
          setState((prev) => ({
            ...prev,
            data: cachedData,
            isLoading: false,
            error: null,
          }));
          onSuccess?.(cachedData);
          return;
        }
      }

      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
      }));
      onLoading?.(true);

      try {
        const data = await fetchFn();
        setState((prev) => ({
          ...prev,
          data,
          isLoading: false,
        }));

        if (useCache) {
          setToCache(key, data);
        }

        onSuccess?.(data);
      } catch (error) {
        const errorObj = error instanceof Error ? error : new Error('Fetch failed');
        setState((prev) => ({
          ...prev,
          error: errorObj,
          isLoading: false,
        }));
        onError?.(errorObj);
      } finally {
        onLoading?.(false);
      }
    },
    [fetchFn, useCache, getFromCache, setToCache, onSuccess, onError, onLoading]
  );

  const refreshData = useCallback(
    (key: string) => {
      if (useCache) {
        cacheRef.current.delete(key);
      }
      return fetchData(key);
    },
    [fetchData, useCache]
  );

  const clearData = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    fetchData,
    refreshData,
    clearData,
    clearCache,
  };
}; 