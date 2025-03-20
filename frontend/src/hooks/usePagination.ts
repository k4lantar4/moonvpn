import { useCallback, useState, useMemo } from 'react';

interface PaginationOptions {
  initialPage?: number;
  pageSize?: number;
  totalItems?: number;
  maxVisiblePages?: number;
}

interface PaginationState {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  visiblePages: number[];
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

export const usePagination = (options: PaginationOptions = {}) => {
  const {
    initialPage = 1,
    pageSize = 10,
    totalItems = 0,
    maxVisiblePages = 5,
  } = options;

  const [state, setState] = useState<PaginationState>({
    currentPage: initialPage,
    pageSize,
    totalItems,
    totalPages: Math.ceil(totalItems / pageSize),
    visiblePages: [],
    hasNextPage: initialPage < Math.ceil(totalItems / pageSize),
    hasPreviousPage: initialPage > 1,
  });

  const calculateVisiblePages = useCallback(
    (currentPage: number, totalPages: number, maxVisible: number) => {
      const pages: number[] = [];
      const halfMax = Math.floor(maxVisible / 2);

      let startPage = Math.max(currentPage - halfMax, 1);
      let endPage = Math.min(startPage + maxVisible - 1, totalPages);

      if (endPage - startPage + 1 < maxVisible) {
        startPage = Math.max(endPage - maxVisible + 1, 1);
      }

      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }

      return pages;
    },
    []
  );

  const updatePagination = useCallback(
    (newTotalItems: number) => {
      const newTotalPages = Math.ceil(newTotalItems / state.pageSize);
      const newVisiblePages = calculateVisiblePages(
        state.currentPage,
        newTotalPages,
        maxVisiblePages
      );

      setState((prev) => ({
        ...prev,
        totalItems: newTotalItems,
        totalPages: newTotalPages,
        visiblePages: newVisiblePages,
        hasNextPage: state.currentPage < newTotalPages,
        hasPreviousPage: state.currentPage > 1,
      }));
    },
    [state.currentPage, state.pageSize, maxVisiblePages, calculateVisiblePages]
  );

  const goToPage = useCallback(
    (page: number) => {
      if (page < 1 || page > state.totalPages) return;

      const newVisiblePages = calculateVisiblePages(
        page,
        state.totalPages,
        maxVisiblePages
      );

      setState((prev) => ({
        ...prev,
        currentPage: page,
        visiblePages: newVisiblePages,
        hasNextPage: page < state.totalPages,
        hasPreviousPage: page > 1,
      }));
    },
    [state.totalPages, maxVisiblePages, calculateVisiblePages]
  );

  const nextPage = useCallback(() => {
    if (state.hasNextPage) {
      goToPage(state.currentPage + 1);
    }
  }, [state.currentPage, state.hasNextPage, goToPage]);

  const previousPage = useCallback(() => {
    if (state.hasPreviousPage) {
      goToPage(state.currentPage - 1);
    }
  }, [state.currentPage, state.hasPreviousPage, goToPage]);

  const setPageSize = useCallback(
    (newPageSize: number) => {
      const newTotalPages = Math.ceil(state.totalItems / newPageSize);
      const newVisiblePages = calculateVisiblePages(
        state.currentPage,
        newTotalPages,
        maxVisiblePages
      );

      setState((prev) => ({
        ...prev,
        pageSize: newPageSize,
        totalPages: newTotalPages,
        visiblePages: newVisiblePages,
        hasNextPage: state.currentPage < newTotalPages,
        hasPreviousPage: state.currentPage > 1,
      }));
    },
    [state.currentPage, state.totalItems, maxVisiblePages, calculateVisiblePages]
  );

  const resetPagination = useCallback(() => {
    const newVisiblePages = calculateVisiblePages(
      initialPage,
      state.totalPages,
      maxVisiblePages
    );

    setState((prev) => ({
      ...prev,
      currentPage: initialPage,
      visiblePages: newVisiblePages,
      hasNextPage: initialPage < state.totalPages,
      hasPreviousPage: false,
    }));
  }, [initialPage, state.totalPages, maxVisiblePages, calculateVisiblePages]);

  const paginationInfo = useMemo(
    () => ({
      startIndex: (state.currentPage - 1) * state.pageSize,
      endIndex: Math.min(state.currentPage * state.pageSize, state.totalItems),
      currentPage: state.currentPage,
      pageSize: state.pageSize,
      totalItems: state.totalItems,
      totalPages: state.totalPages,
    }),
    [state.currentPage, state.pageSize, state.totalItems]
  );

  return {
    ...state,
    ...paginationInfo,
    goToPage,
    nextPage,
    previousPage,
    setPageSize,
    resetPagination,
    updatePagination,
  };
}; 