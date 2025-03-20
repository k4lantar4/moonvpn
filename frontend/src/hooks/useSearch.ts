import { useCallback, useState, useMemo, useEffect } from 'react';

interface SearchOptions {
  debounceTime?: number;
  minLength?: number;
  caseSensitive?: boolean;
  searchFields?: string[];
  highlightMatches?: boolean;
}

interface SearchState<T> {
  searchTerm: string;
  debouncedSearchTerm: string;
  results: T[];
  isLoading: boolean;
  error: Error | null;
}

export const useSearch = <T extends Record<string, any>>(
  data: T[],
  options: SearchOptions = {}
) => {
  const {
    debounceTime = 300,
    minLength = 2,
    caseSensitive = false,
    searchFields = [],
    highlightMatches = false,
  } = options;

  const [state, setState] = useState<SearchState<T>>({
    searchTerm: '',
    debouncedSearchTerm: '',
    results: data,
    isLoading: false,
    error: null,
  });

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setState((prev) => ({
        ...prev,
        debouncedSearchTerm: prev.searchTerm,
      }));
    }, debounceTime);

    return () => clearTimeout(timer);
  }, [state.searchTerm, debounceTime]);

  const searchData = useCallback(
    (searchTerm: string) => {
      if (!searchTerm || searchTerm.length < minLength) {
        return data;
      }

      const searchValue = caseSensitive
        ? searchTerm
        : searchTerm.toLowerCase();

      return data.filter((item) => {
        const fieldsToSearch = searchFields.length > 0
          ? searchFields
          : Object.keys(item);

        return fieldsToSearch.some((field) => {
          const fieldValue = item[field];
          if (fieldValue === null || fieldValue === undefined) {
            return false;
          }

          const stringValue = String(fieldValue);
          const searchableValue = caseSensitive
            ? stringValue
            : stringValue.toLowerCase();

          return searchableValue.includes(searchValue);
        });
      });
    },
    [data, searchFields, caseSensitive, minLength]
  );

  const handleSearch = useCallback(
    (searchTerm: string) => {
      setState((prev) => ({
        ...prev,
        searchTerm,
        isLoading: true,
        error: null,
      }));

      try {
        const results = searchData(searchTerm);
        setState((prev) => ({
          ...prev,
          results,
          isLoading: false,
        }));
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error: error instanceof Error ? error : new Error('Search failed'),
          isLoading: false,
        }));
      }
    },
    [searchData]
  );

  const clearSearch = useCallback(() => {
    setState((prev) => ({
      ...prev,
      searchTerm: '',
      debouncedSearchTerm: '',
      results: data,
      error: null,
    }));
  }, [data]);

  const highlightMatch = useCallback(
    (text: string, searchTerm: string): string => {
      if (!highlightMatches || !searchTerm) {
        return text;
      }

      const regex = new RegExp(
        `(${searchTerm})`,
        caseSensitive ? 'g' : 'gi'
      );

      return text.replace(regex, '<mark>$1</mark>');
    },
    [caseSensitive, highlightMatches]
  );

  const searchInfo = useMemo(
    () => ({
      totalResults: state.results.length,
      hasResults: state.results.length > 0,
      isSearching: state.searchTerm !== state.debouncedSearchTerm,
      searchFields: searchFields.length > 0 ? searchFields : Object.keys(data[0] || {}),
    }),
    [state.results.length, state.searchTerm, state.debouncedSearchTerm, searchFields, data]
  );

  return {
    ...state,
    ...searchInfo,
    handleSearch,
    clearSearch,
    highlightMatch,
  };
}; 