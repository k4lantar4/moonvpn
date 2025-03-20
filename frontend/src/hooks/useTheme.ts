import { useState, useEffect, useCallback } from 'react';
import { createTheme, Theme } from '@mui/material/styles';
import { useLocalStorage } from './useLocalStorage';

type ThemeMode = 'light' | 'dark';

interface ThemeOptions {
  mode: ThemeMode;
  primaryColor: string;
  secondaryColor: string;
  customColors?: Record<string, string>;
}

const defaultThemeOptions: ThemeOptions = {
  mode: 'light',
  primaryColor: '#1976d2',
  secondaryColor: '#dc004e',
};

export const useTheme = () => {
  const [themeOptions, setThemeOptions] = useLocalStorage<ThemeOptions>(
    'theme_options',
    defaultThemeOptions
  );

  const [theme, setTheme] = useState<Theme>(() =>
    createTheme({
      palette: {
        mode: themeOptions.mode,
        primary: {
          main: themeOptions.primaryColor,
        },
        secondary: {
          main: themeOptions.secondaryColor,
        },
        ...(themeOptions.customColors || {}),
      },
    })
  );

  useEffect(() => {
    setTheme(
      createTheme({
        palette: {
          mode: themeOptions.mode,
          primary: {
            main: themeOptions.primaryColor,
          },
          secondary: {
            main: themeOptions.secondaryColor,
          },
          ...(themeOptions.customColors || {}),
        },
      })
    );
  }, [themeOptions]);

  const toggleThemeMode = useCallback(() => {
    setThemeOptions((prev) => ({
      ...prev,
      mode: prev.mode === 'light' ? 'dark' : 'light',
    }));
  }, [setThemeOptions]);

  const updateThemeColors = useCallback(
    (colors: Partial<Omit<ThemeOptions, 'mode'>>) => {
      setThemeOptions((prev) => ({
        ...prev,
        ...colors,
      }));
    },
    [setThemeOptions]
  );

  return {
    theme,
    themeOptions,
    toggleThemeMode,
    updateThemeColors,
  };
}; 