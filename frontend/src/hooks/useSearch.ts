import { useState, useCallback, useMemo } from 'react';

interface SearchOptions {
  debounceMs?: number;
  minLength?: number;
  caseSensitive?: boolean;
}

export const useSearch = <T extends Record<string, any>>(
  searchFields: (keyof T)[],
  options: SearchOptions = {}
) => {
  const {
    debounceMs = 300,
    minLength = 2,
    caseSensitive = false,
  } = options;

  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');

  // Debounce search term
  useMemo(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [searchTerm, debounceMs]);

  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
  }, []);

  const clearSearch = useCallback(() => {
    setSearchTerm('');
    setDebouncedSearchTerm('');
  }, []);

  const searchData = useCallback(
    <R extends T>(data: R[]): R[] => {
      if (!debouncedSearchTerm || debouncedSearchTerm.length < minLength) {
        return data;
      }

      const searchValue = caseSensitive
        ? debouncedSearchTerm
        : debouncedSearchTerm.toLowerCase();

      return data.filter((item) =>
        searchFields.some((field) => {
          const value = item[field];
          if (value === null || value === undefined) return false;

          const stringValue = String(value);
          const searchableValue = caseSensitive
            ? stringValue
            : stringValue.toLowerCase();

          return searchableValue.includes(searchValue);
        })
      );
    },
    [debouncedSearchTerm, searchFields, minLength, caseSensitive]
  );

  const isSearching = useMemo(() => {
    return searchTerm.length >= minLength;
  }, [searchTerm, minLength]);

  const getSearchTerm = useCallback(() => {
    return searchTerm;
  }, [searchTerm]);

  const getDebouncedSearchTerm = useCallback(() => {
    return debouncedSearchTerm;
  }, [debouncedSearchTerm]);

  return {
    handleSearch,
    clearSearch,
    searchData,
    isSearching,
    getSearchTerm,
    getDebouncedSearchTerm,
  };
}; 