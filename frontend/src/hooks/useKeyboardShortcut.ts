import { useEffect, useCallback } from 'react';

type KeyCombo = string | string[];
type ModifierKey = 'ctrl' | 'shift' | 'alt' | 'meta';

interface ShortcutOptions {
  preventDefault?: boolean;
  stopPropagation?: boolean;
  enabled?: boolean;
}

interface ShortcutDefinition {
  key: KeyCombo;
  handler: () => void;
  options?: ShortcutOptions;
}

export const useKeyboardShortcut = (
  shortcuts: ShortcutDefinition[]
) => {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      shortcuts.forEach(({ key, handler, options = {} }) => {
        const {
          preventDefault = true,
          stopPropagation = true,
          enabled = true,
        } = options;

        if (!enabled) return;

        const keys = Array.isArray(key) ? key : [key];
        const modifiers: ModifierKey[] = [];

        // Check modifier keys
        if (event.ctrlKey) modifiers.push('ctrl');
        if (event.shiftKey) modifiers.push('shift');
        if (event.altKey) modifiers.push('alt');
        if (event.metaKey) modifiers.push('meta');

        // Check if all required keys are pressed
        const allKeysPressed = keys.every((k) => {
          const keyLower = k.toLowerCase();
          if (modifiers.includes(keyLower as ModifierKey)) {
            return true;
          }
          return event.key.toLowerCase() === keyLower;
        });

        if (allKeysPressed) {
          if (preventDefault) {
            event.preventDefault();
          }
          if (stopPropagation) {
            event.stopPropagation();
          }
          handler();
        }
      });
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  return {
    handleKeyDown,
  };
}; 