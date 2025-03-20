import { useCallback, useState, useMemo } from 'react';

type SortDirection = 'asc' | 'desc' | null;
type SortFunction<T> = (a: T, b: T) => number;

interface SortConfig<T> {
  key: keyof T;
  direction: SortDirection;
}

interface SortingOptions<T> {
  initialSort?: SortConfig<T>;
  multiSort?: boolean;
  caseSensitive?: boolean;
}

interface SortingState<T> {
  sortConfig: SortConfig<T>[];
  sortedData: T[];
}

export const useSorting = <T extends Record<string, any>>(
  data: T[],
  options: SortingOptions<T> = {}
) => {
  const {
    initialSort,
    multiSort = false,
    caseSensitive = false,
  } = options;

  const [state, setState] = useState<SortingState<T>>({
    sortConfig: initialSort ? [initialSort] : [],
    sortedData: data,
  });

  const getSortFunction = useCallback(
    (key: keyof T, direction: SortDirection): SortFunction<T> => {
      return (a: T, b: T) => {
        let aValue = a[key];
        let bValue = b[key];

        if (!caseSensitive && typeof aValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }

        if (aValue === bValue) return 0;
        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;

        const comparison = aValue < bValue ? -1 : 1;
        return direction === 'asc' ? comparison : -comparison;
      };
    },
    [caseSensitive]
  );

  const sortData = useCallback(
    (sortConfig: SortConfig<T>[]) => {
      if (sortConfig.length === 0) {
        return data;
      }

      return [...data].sort((a, b) => {
        for (const { key, direction } of sortConfig) {
          if (!direction) continue;

          const comparison = getSortFunction(key, direction)(a, b);
          if (comparison !== 0) return comparison;
        }
        return 0;
      });
    },
    [data, getSortFunction]
  );

  const handleSort = useCallback(
    (key: keyof T) => {
      setState((prev) => {
        const newSortConfig = [...prev.sortConfig];
        const existingSortIndex = newSortConfig.findIndex(
          (config) => config.key === key
        );

        if (existingSortIndex >= 0) {
          const existingSort = newSortConfig[existingSortIndex];
          if (existingSort.direction === 'asc') {
            existingSort.direction = 'desc';
          } else if (existingSort.direction === 'desc') {
            if (multiSort) {
              newSortConfig.splice(existingSortIndex, 1);
            } else {
              existingSort.direction = null;
            }
          } else {
            existingSort.direction = 'asc';
          }
        } else {
          if (!multiSort) {
            newSortConfig.length = 0;
          }
          newSortConfig.push({ key, direction: 'asc' });
        }

        const sortedData = sortData(newSortConfig);

        return {
          sortConfig: newSortConfig,
          sortedData,
        };
      });
    },
    [multiSort, sortData]
  );

  const clearSort = useCallback(() => {
    setState({
      sortConfig: [],
      sortedData: data,
    });
  }, [data]);

  const getSortDirection = useCallback(
    (key: keyof T): SortDirection => {
      const sortConfig = state.sortConfig.find((config) => config.key === key);
      return sortConfig?.direction || null;
    },
    [state.sortConfig]
  );

  const isSorted = useCallback(
    (key: keyof T): boolean => {
      return state.sortConfig.some((config) => config.key === key);
    },
    [state.sortConfig]
  );

  const getSortIcon = useCallback(
    (key: keyof T): string => {
      const direction = getSortDirection(key);
      if (!direction) return '↕️';
      return direction === 'asc' ? '↑' : '↓';
    },
    [getSortDirection]
  );

  const sortInfo = useMemo(
    () => ({
      currentSort: state.sortConfig,
      isMultiSort: multiSort,
      caseSensitive,
    }),
    [state.sortConfig, multiSort, caseSensitive]
  );

  return {
    ...state,
    ...sortInfo,
    handleSort,
    clearSort,
    getSortDirection,
    isSorted,
    getSortIcon,
  };
}; 