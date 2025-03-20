import { useState, useCallback, useMemo } from 'react';

interface PaginationState {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

interface PaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
  totalItems?: number;
}

export const usePagination = (options: PaginationOptions = {}) => {
  const {
    initialPage = 1,
    initialPageSize = 10,
    totalItems = 0,
  } = options;

  const [state, setState] = useState<PaginationState>({
    page: initialPage,
    pageSize: initialPageSize,
    totalItems,
    totalPages: Math.ceil(totalItems / initialPageSize),
  });

  const setPage = useCallback((page: number) => {
    setState((prev) => ({
      ...prev,
      page: Math.max(1, Math.min(page, prev.totalPages)),
    }));
  }, []);

  const setPageSize = useCallback((pageSize: number) => {
    setState((prev) => ({
      ...prev,
      pageSize,
      totalPages: Math.ceil(prev.totalItems / pageSize),
      page: 1, // Reset to first page when changing page size
    }));
  }, []);

  const setTotalItems = useCallback((totalItems: number) => {
    setState((prev) => ({
      ...prev,
      totalItems,
      totalPages: Math.ceil(totalItems / prev.pageSize),
    }));
  }, []);

  const nextPage = useCallback(() => {
    setState((prev) => ({
      ...prev,
      page: Math.min(prev.page + 1, prev.totalPages),
    }));
  }, []);

  const previousPage = useCallback(() => {
    setState((prev) => ({
      ...prev,
      page: Math.max(prev.page - 1, 1),
    }));
  }, []);

  const goToFirstPage = useCallback(() => {
    setState((prev) => ({
      ...prev,
      page: 1,
    }));
  }, []);

  const goToLastPage = useCallback(() => {
    setState((prev) => ({
      ...prev,
      page: prev.totalPages,
    }));
  }, []);

  const pageRange = useMemo(() => {
    const { page, totalPages } = state;
    const delta = 2; // Number of pages to show before and after current page
    const range: number[] = [];
    const rangeWithDots: (number | string)[] = [];

    for (let i = 0; i < totalPages; i++) {
      if (
        i === 0 || // First page
        i === totalPages - 1 || // Last page
        (i >= page - delta && i <= page + delta) // Pages around current page
      ) {
        range.push(i + 1);
      }
    }

    let l: number;
    for (let i = 0; i < range.length; i++) {
      if (l) {
        if (range[i] - l === 2) {
          rangeWithDots.push(l + 1);
        } else if (range[i] - l !== 1) {
          rangeWithDots.push('...');
        }
      }
      rangeWithDots.push(range[i]);
      l = range[i];
    }

    return rangeWithDots;
  }, [state.page, state.totalPages]);

  const canGoToNextPage = useMemo(() => state.page < state.totalPages, [state.page, state.totalPages]);
  const canGoToPreviousPage = useMemo(() => state.page > 1, [state.page]);

  return {
    ...state,
    setPage,
    setPageSize,
    setTotalItems,
    nextPage,
    previousPage,
    goToFirstPage,
    goToLastPage,
    pageRange,
    canGoToNextPage,
    canGoToPreviousPage,
  };
}; 