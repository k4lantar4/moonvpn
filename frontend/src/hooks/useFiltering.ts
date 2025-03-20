import { useState, useCallback, useMemo } from 'react';

type FilterOperator = 'equals' | 'contains' | 'startsWith' | 'endsWith' | 'greaterThan' | 'lessThan' | 'between' | 'in';

interface FilterCondition<T> {
  field: keyof T;
  operator: FilterOperator;
  value: any;
  value2?: any; // For 'between' operator
}

interface FilterState<T> {
  conditions: FilterCondition<T>[];
}

interface FilterOptions<T> {
  initialConditions?: FilterCondition<T>[];
}

export const useFiltering = <T extends Record<string, any>>(
  options: FilterOptions<T> = {}
) => {
  const {
    initialConditions = [],
  } = options;

  const [state, setState] = useState<FilterState<T>>({
    conditions: initialConditions,
  });

  const addFilter = useCallback((condition: FilterCondition<T>) => {
    setState((prev) => ({
      conditions: [...prev.conditions, condition],
    }));
  }, []);

  const removeFilter = useCallback((field: keyof T) => {
    setState((prev) => ({
      conditions: prev.conditions.filter((c) => c.field !== field),
    }));
  }, []);

  const updateFilter = useCallback((field: keyof T, condition: Partial<FilterCondition<T>>) => {
    setState((prev) => ({
      conditions: prev.conditions.map((c) =>
        c.field === field ? { ...c, ...condition } : c
      ),
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setState({
      conditions: [],
    });
  }, []);

  const filterData = useCallback(
    <R extends T>(data: R[]): R[] => {
      if (state.conditions.length === 0) {
        return data;
      }

      return data.filter((item) =>
        state.conditions.every((condition) => {
          const value = item[condition.field];
          const filterValue = condition.value;
          const filterValue2 = condition.value2;

          switch (condition.operator) {
            case 'equals':
              return value === filterValue;
            case 'contains':
              return String(value).toLowerCase().includes(String(filterValue).toLowerCase());
            case 'startsWith':
              return String(value).toLowerCase().startsWith(String(filterValue).toLowerCase());
            case 'endsWith':
              return String(value).toLowerCase().endsWith(String(filterValue).toLowerCase());
            case 'greaterThan':
              return value > filterValue;
            case 'lessThan':
              return value < filterValue;
            case 'between':
              return value >= filterValue && value <= filterValue2!;
            case 'in':
              return Array.isArray(filterValue) && filterValue.includes(value);
            default:
              return true;
          }
        })
      );
    },
    [state.conditions]
  );

  const getActiveFilters = useCallback(() => {
    return state.conditions;
  }, [state.conditions]);

  const hasActiveFilters = useCallback(() => {
    return state.conditions.length > 0;
  }, [state.conditions]);

  const getFilterValue = useCallback(
    (field: keyof T) => {
      const condition = state.conditions.find((c) => c.field === field);
      return condition?.value;
    },
    [state.conditions]
  );

  const getFilterOperator = useCallback(
    (field: keyof T) => {
      const condition = state.conditions.find((c) => c.field === field);
      return condition?.operator;
    },
    [state.conditions]
  );

  return {
    addFilter,
    removeFilter,
    updateFilter,
    clearFilters,
    filterData,
    getActiveFilters,
    hasActiveFilters,
    getFilterValue,
    getFilterOperator,
  };
}; 