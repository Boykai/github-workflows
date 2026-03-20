/**
 * useGlobalShortcuts — global keyboard shortcuts for power users.
 * Listens on document keydown and dispatches actions based on key combos.
 */

import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

interface UseGlobalShortcutsOptions {
  onOpenShortcutModal: () => void;
}

function isTextInput(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false;
  const tagName = target.tagName.toLowerCase();
  return tagName === 'input' || tagName === 'textarea' || target.isContentEditable;
}

function isModalOpen(): boolean {
  return document.querySelector('[role="dialog"][aria-modal="true"]') !== null;
}

export function useGlobalShortcuts({ onOpenShortcutModal }: UseGlobalShortcutsOptions): void {
  const navigate = useNavigate();

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const inInput = isTextInput(event.target);

      // Ctrl+K / Cmd+K — open command palette (unless a modal is already open)
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        if (!isModalOpen()) {
          window.dispatchEvent(new CustomEvent('solune:open-command-palette'));
        }
        return;
      }

      // Skip remaining shortcuts when in text input (except Escape)
      if (inInput && event.key !== 'Escape') return;

      // Suppress non-Escape shortcuts when a modal dialog is open
      if (isModalOpen()) return;

      // ? — open shortcut help modal (only when not in input)
      if (event.key === '?' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault();
        onOpenShortcutModal();
        return;
      }

      // Number key navigation (1-5)
      const sectionMap: Record<string, string> = {
        '1': '/',
        '2': '/board',
        '3': '/agents',
        '4': '/pipeline',
        '5': '/settings',
      };
      if (sectionMap[event.key] && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault();
        navigate(sectionMap[event.key]);
      }
    },
    [navigate, onOpenShortcutModal],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
