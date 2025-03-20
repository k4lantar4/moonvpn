import { useCallback, useState, useEffect, useRef } from 'react';

interface InfiniteScrollOptions<T> {
  pageSize?: number;
  threshold?: number;
  onLoadMore: (page: number) => Promise<T[]>;
  onSuccess?: (items: T[]) => void;
  onError?: (error: Error) => void;
}

interface InfiniteScrollState<T> {
  items: T[];
  page: number;
  isLoading: boolean;
  hasMore: boolean;
  error: Error | null;
}

export const useInfiniteScroll = <T>(
  options: InfiniteScrollOptions<T>
) => {
  const {
    pageSize = 20,
    threshold = 100,
    onLoadMore,
    onSuccess,
    onError,
  } = options;

  const [state, setState] = useState<InfiniteScrollState<T>>({
    items: [],
    page: 1,
    isLoading: false,
    hasMore: true,
    error: null,
  });

  const containerRef = useRef<HTMLElement | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const loadMore = useCallback(async () => {
    if (state.isLoading || !state.hasMore) return;

    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const newItems = await onLoadMore(state.page);
      
      if (newItems.length < pageSize) {
        setState((prev) => ({
          ...prev,
          hasMore: false,
        }));
      }

      setState((prev) => ({
        ...prev,
        items: [...prev.items, ...newItems],
        page: prev.page + 1,
        isLoading: false,
      }));

      onSuccess?.(newItems);
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error('Failed to load more items');
      setState((prev) => ({
        ...prev,
        error: errorObj,
        isLoading: false,
      }));
      onError?.(errorObj);
    }
  }, [state.page, state.isLoading, state.hasMore, onLoadMore, pageSize, onSuccess, onError]);

  const handleScroll = useCallback(() => {
    if (!containerRef.current || state.isLoading || !state.hasMore) return;

    const container = containerRef.current;
    const scrollPosition = container.scrollTop + container.clientHeight;
    const scrollHeight = container.scrollHeight;

    if (scrollHeight - scrollPosition <= threshold) {
      loadMore();
    }
  }, [state.isLoading, state.hasMore, threshold, loadMore]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll);
    return () => {
      container.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);

  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        const target = entries[0];
        if (target.isIntersecting && !state.isLoading && state.hasMore) {
          loadMore();
        }
      },
      {
        root: containerRef.current,
        rootMargin: `${threshold}px`,
      }
    );

    const lastItem = containerRef.current?.lastElementChild;
    if (lastItem) {
      observerRef.current.observe(lastItem);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [state.isLoading, state.hasMore, threshold, loadMore]);

  const reset = useCallback(() => {
    setState({
      items: [],
      page: 1,
      isLoading: false,
      hasMore: true,
      error: null,
    });
  }, []);

  const refresh = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      page: 1,
      hasMore: true,
      error: null,
    }));
    await loadMore();
  }, [loadMore]);

  return {
    ...state,
    containerRef,
    reset,
    refresh,
  };
}; 