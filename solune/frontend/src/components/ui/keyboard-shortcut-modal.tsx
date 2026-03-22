/**
 * KeyboardShortcutModal — accessible modal listing all available keyboard shortcuts.
 */

import { useEffect, useRef } from 'react';
import { X } from '@/lib/icons';
import { cn } from '@/lib/utils';

interface ShortcutEntry {
  keys: string[];
  description: string;
}

interface ShortcutGroup {
  title: string;
  shortcuts: ShortcutEntry[];
}

const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);
const MOD = isMac ? '⌘' : 'Ctrl';

const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    title: 'Navigation',
    shortcuts: [
      { keys: ['1'], description: 'Go to Dashboard' },
      { keys: ['2'], description: 'Go to Board' },
      { keys: ['3'], description: 'Go to Agents' },
      { keys: ['4'], description: 'Go to Pipeline' },
      { keys: ['5'], description: 'Go to Settings' },
    ],
  },
  {
    title: 'Actions',
    shortcuts: [
      { keys: [MOD, 'K'], description: 'Command Palette' },
      { keys: [MOD, 'Enter'], description: 'Send chat message' },
      { keys: ['Esc'], description: 'Close modal' },
    ],
  },
  {
    title: 'Help',
    shortcuts: [{ keys: ['?'], description: 'Show this modal' }],
  },
];

interface KeyboardShortcutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function KeyboardShortcutModal({ isOpen, onClose }: KeyboardShortcutModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      // Focus close button on open
      setTimeout(() => closeButtonRef.current?.focus(), 0);
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus();
      previousFocusRef.current = null;
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
      // Trap focus inside the modal — only interactive element is the close button
      if (e.key === 'Tab') {
        e.preventDefault();
        closeButtonRef.current?.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown, true);
    return () => document.removeEventListener('keydown', handleKeyDown, true);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm celestial-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Modal */}
      <div
        className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcut-modal-title"
      >
        <div className="celestial-panel celestial-fade-in w-full max-w-md rounded-2xl border border-border/80 bg-card shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border/70 px-5 py-4">
            <h2 id="shortcut-modal-title" className="text-lg font-semibold">
              Keyboard Shortcuts
            </h2>
            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              className="rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              aria-label="Close shortcuts modal"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Content */}
          <div className="max-h-[60vh] overflow-y-auto px-5 py-4 space-y-5">
            {SHORTCUT_GROUPS.map((group) => (
              <div key={group.title}>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  {group.title}
                </h3>
                <div className="space-y-1.5">
                  {group.shortcuts.map((shortcut) => (
                    <div
                      key={shortcut.description}
                      className="flex items-center justify-between py-1"
                    >
                      <span className="text-sm text-foreground">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, i) => (
                          <span key={i}>
                            <kbd
                              className={cn(
                                'inline-flex min-w-[1.75rem] items-center justify-center rounded-md border border-border bg-muted px-1.5 py-0.5 text-xs font-medium text-foreground shadow-sm',
                              )}
                            >
                              {key}
                            </kbd>
                            {i < shortcut.keys.length - 1 && (
                              <span className="mx-0.5 text-muted-foreground">+</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
