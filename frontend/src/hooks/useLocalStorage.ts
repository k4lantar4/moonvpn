import { useState, useEffect, useCallback } from 'react';

interface StorageOptions {
  prefix?: string;
  serialize?: (value: any) => string;
  deserialize?: (value: string) => any;
}

export const useLocalStorage = <T>(
  key: string,
  initialValue: T,
  options: StorageOptions = {}
) => {
  const {
    prefix = 'app_',
    serialize = JSON.stringify,
    deserialize = JSON.parse,
  } = options;

  const prefixedKey = `${prefix}${key}`;

  // Get from local storage then
  // parse stored json or return initialValue
  const readValue = useCallback((): T => {
    try {
      const item = window.localStorage.getItem(prefixedKey);
      return item ? deserialize(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${prefixedKey}":`, error);
      return initialValue;
    }
  }, [prefixedKey, initialValue, deserialize]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  // Return a wrapped version of useState's setter function that ...
  // ... persists the new value to localStorage.
  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      try {
        // Allow value to be a function so we have same API as useState
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        
        // Save state
        setStoredValue(valueToStore);
        
        // Save to local storage
        window.localStorage.setItem(prefixedKey, serialize(valueToStore));
      } catch (error) {
        console.warn(`Error setting localStorage key "${prefixedKey}":`, error);
      }
    },
    [prefixedKey, serialize, storedValue]
  );

  // Remove value from local storage
  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(prefixedKey);
      setStoredValue(initialValue);
    } catch (error) {
      console.warn(`Error removing localStorage key "${prefixedKey}":`, error);
    }
  }, [prefixedKey, initialValue]);

  // Clear all values with the prefix
  const clearAll = useCallback(() => {
    try {
      const keys = Object.keys(window.localStorage);
      keys.forEach((k) => {
        if (k.startsWith(prefix)) {
          window.localStorage.removeItem(k);
        }
      });
      setStoredValue(initialValue);
    } catch (error) {
      console.warn(`Error clearing localStorage with prefix "${prefix}":`, error);
    }
  }, [prefix, initialValue]);

  // Listen for changes in other tabs/windows
  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === prefixedKey) {
        setStoredValue(readValue());
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [prefixedKey, readValue]);

  return {
    value: storedValue,
    setValue,
    removeValue,
    clearAll,
  };
}; 