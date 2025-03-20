import { useCallback, useState, useMemo } from 'react';

type FilterOperator = 'equals' | 'contains' | 'startsWith' | 'endsWith' | 'greaterThan' | 'lessThan' | 'between' | 'in' | 'custom';

interface FilterValue {
  operator: FilterOperator;
  value: any;
  customFilter?: (item: any) => boolean;
}

interface FilterConfig<T> {
  [key: string]: FilterValue;
}

interface FilteringOptions<T> {
  initialFilters?: FilterConfig<T>;
  caseSensitive?: boolean;
  debounceTime?: number;
}

interface FilteringState<T> {
  filters: FilterConfig<T>;
  filteredData: T[];
}

export const useFiltering = <T extends Record<string, any>>(
  data: T[],
  options: FilteringOptions<T> = {}
) => {
  const {
    initialFilters = {},
    caseSensitive = false,
    debounceTime = 300,
  } = options;

  const [state, setState] = useState<FilteringState<T>>({
    filters: initialFilters,
    filteredData: data,
  });

  const applyFilter = useCallback(
    (item: T, key: string, filter: FilterValue): boolean => {
      const { operator, value, customFilter } = filter;
      const itemValue = item[key];

      if (customFilter) {
        return customFilter(item);
      }

      if (itemValue === null || itemValue === undefined) {
        return false;
      }

      switch (operator) {
        case 'equals':
          return caseSensitive
            ? itemValue === value
            : String(itemValue).toLowerCase() === String(value).toLowerCase();

        case 'contains':
          return caseSensitive
            ? String(itemValue).includes(String(value))
            : String(itemValue).toLowerCase().includes(String(value).toLowerCase());

        case 'startsWith':
          return caseSensitive
            ? String(itemValue).startsWith(String(value))
            : String(itemValue).toLowerCase().startsWith(String(value).toLowerCase());

        case 'endsWith':
          return caseSensitive
            ? String(itemValue).endsWith(String(value))
            : String(itemValue).toLowerCase().endsWith(String(value).toLowerCase());

        case 'greaterThan':
          return itemValue > value;

        case 'lessThan':
          return itemValue < value;

        case 'between':
          const [min, max] = value;
          return itemValue >= min && itemValue <= max;

        case 'in':
          return Array.isArray(value) && value.includes(itemValue);

        default:
          return true;
      }
    },
    [caseSensitive]
  );

  const filterData = useCallback(
    (filters: FilterConfig<T>) => {
      if (Object.keys(filters).length === 0) {
        return data;
      }

      return data.filter((item) =>
        Object.entries(filters).every(([key, filter]) =>
          applyFilter(item, key, filter)
        )
      );
    },
    [data, applyFilter]
  );

  const handleFilter = useCallback(
    (key: string, filter: FilterValue) => {
      setState((prev) => {
        const newFilters = {
          ...prev.filters,
          [key]: filter,
        };

        const filteredData = filterData(newFilters);

        return {
          filters: newFilters,
          filteredData,
        };
      });
    },
    [filterData]
  );

  const removeFilter = useCallback(
    (key: string) => {
      setState((prev) => {
        const { [key]: removed, ...remainingFilters } = prev.filters;
        const filteredData = filterData(remainingFilters);

        return {
          filters: remainingFilters,
          filteredData,
        };
      });
    },
    [filterData]
  );

  const clearFilters = useCallback(() => {
    setState({
      filters: {},
      filteredData: data,
    });
  }, [data]);

  const hasFilter = useCallback(
    (key: string): boolean => {
      return key in state.filters;
    },
    [state.filters]
  );

  const getFilterValue = useCallback(
    (key: string): FilterValue | undefined => {
      return state.filters[key];
    },
    [state.filters]
  );

  const filterInfo = useMemo(
    () => ({
      activeFilters: Object.keys(state.filters),
      totalItems: data.length,
      filteredItems: state.filteredData.length,
    }),
    [state.filters, data.length, state.filteredData.length]
  );

  return {
    ...state,
    ...filterInfo,
    handleFilter,
    removeFilter,
    clearFilters,
    hasFilter,
    getFilterValue,
  };
}; 