import { useState, useCallback, useMemo } from 'react';

type SortDirection = 'asc' | 'desc';

interface SortState<T> {
  field: keyof T | null;
  direction: SortDirection;
}

interface SortOptions<T> {
  initialField?: keyof T;
  initialDirection?: SortDirection;
}

export const useSorting = <T extends Record<string, any>>(
  options: SortOptions<T> = {}
) => {
  const {
    initialField,
    initialDirection = 'asc',
  } = options;

  const [state, setState] = useState<SortState<T>>({
    field: initialField || null,
    direction: initialDirection,
  });

  const toggleSort = useCallback((field: keyof T) => {
    setState((prev) => {
      if (prev.field === field) {
        return {
          field,
          direction: prev.direction === 'asc' ? 'desc' : 'asc',
        };
      }
      return {
        field,
        direction: 'asc',
      };
    });
  }, []);

  const setSort = useCallback((field: keyof T, direction: SortDirection) => {
    setState({
      field,
      direction,
    });
  }, []);

  const clearSort = useCallback(() => {
    setState({
      field: null,
      direction: 'asc',
    });
  }, []);

  const sortData = useCallback(
    <R extends T>(data: R[]): R[] => {
      if (!state.field) {
        return data;
      }

      return [...data].sort((a, b) => {
        const aValue = a[state.field!];
        const bValue = b[state.field!];

        if (aValue === bValue) return 0;
        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;

        const comparison = aValue < bValue ? -1 : 1;
        return state.direction === 'asc' ? comparison : -comparison;
      });
    },
    [state.field, state.direction]
  );

  const getSortIcon = useCallback(
    (field: keyof T): 'asc' | 'desc' | null => {
      if (state.field !== field) return null;
      return state.direction;
    },
    [state.field, state.direction]
  );

  const isSorted = useCallback(
    (field: keyof T): boolean => {
      return state.field === field;
    },
    [state.field]
  );

  const getSortLabel = useCallback(
    (field: keyof T): string => {
      if (!isSorted(field)) return 'Sort';
      return state.direction === 'asc' ? 'Sort ascending' : 'Sort descending';
    },
    [isSorted, state.direction]
  );

  return {
    ...state,
    toggleSort,
    setSort,
    clearSort,
    sortData,
    getSortIcon,
    isSorted,
    getSortLabel,
  };
}; 