/**
 * UndoRedoContext — session-scoped undo/redo for destructive board actions.
 *
 * Features:
 * - Configurable undo time window (default: 30 seconds).
 * - LIFO undo/redo stacks.
 * - Keyboard shortcuts: Ctrl+Z (undo), Ctrl+Shift+Z (redo).
 * - Automatic expiry of old undo entries.
 * - New actions clear the redo stack (standard semantics).
 */

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

// ── Types ──

export interface ActionHistoryEntry {
  /** Unique entry identifier. */
  id: string;
  /** Type of destructive action. */
  actionType: 'archive' | 'delete' | 'label_remove' | 'status_change';
  /** Type of affected entity. */
  entityType: 'board_item' | 'label' | 'card';
  /** ID of the affected entity. */
  entityId: string;
  /** Snapshot of entity state before the action. */
  previousState: Record<string, unknown>;
  /** Snapshot of entity state after the action. */
  newState: Record<string, unknown>;
  /** Unix timestamp when the action was performed. */
  timestamp: number;
  /** Unix timestamp when the undo window closes. */
  expiresAt: number;
  /** Human-readable description. */
  description: string;
}

export interface UndoRedoContextValue {
  /** Push a new destructive action onto the undo stack. */
  pushAction: (entry: Omit<ActionHistoryEntry, 'id' | 'timestamp' | 'expiresAt'>) => void;
  /** Undo the last action. Returns the entry that was undone, or null. */
  undo: () => ActionHistoryEntry | null;
  /** Redo the last undone action. Returns the entry that was redone, or null. */
  redo: () => ActionHistoryEntry | null;
  /** Whether there are undoable actions. */
  canUndo: boolean;
  /** Whether there are redoable actions. */
  canRedo: boolean;
  /** Human-readable description of the next undo action. */
  nextUndoDescription: string | null;
  /** Human-readable description of the next redo action. */
  nextRedoDescription: string | null;
}

// ── Context ──

const noop = () => null;

export const UndoRedoContext = createContext<UndoRedoContextValue>({
  pushAction: () => {},
  undo: noop,
  redo: noop,
  canUndo: false,
  canRedo: false,
  nextUndoDescription: null,
  nextRedoDescription: null,
});

// ── Defaults ──

const DEFAULT_UNDO_WINDOW_MS = 30_000; // 30 seconds
const MAX_STACK_SIZE = 50;

// ── Provider ──

interface UndoRedoProviderProps {
  children: ReactNode;
  /** Undo window duration in milliseconds (default: 30_000). */
  undoWindowMs?: number;
}

export function UndoRedoProvider({
  children,
  undoWindowMs = DEFAULT_UNDO_WINDOW_MS,
}: UndoRedoProviderProps) {
  const [undoStack, setUndoStack] = useState<ActionHistoryEntry[]>([]);
  const [redoStack, setRedoStack] = useState<ActionHistoryEntry[]>([]);
  const expiryTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Expiry logic ──

  useEffect(() => {
    expiryTimerRef.current = setInterval(() => {
      const now = Date.now();
      setUndoStack((prev) => {
        const filtered = prev.filter((entry) => entry.expiresAt > now);
        return filtered.length !== prev.length ? filtered : prev;
      });
    }, 5_000); // Check every 5 seconds

    return () => {
      if (expiryTimerRef.current) clearInterval(expiryTimerRef.current);
    };
  }, []);

  // ── Push action ──

  const pushAction = useCallback(
    (entry: Omit<ActionHistoryEntry, 'id' | 'timestamp' | 'expiresAt'>) => {
      const now = Date.now();
      const fullEntry: ActionHistoryEntry = {
        ...entry,
        id: crypto.randomUUID(),
        timestamp: now,
        expiresAt: now + undoWindowMs,
      };

      setUndoStack((prev) => [...prev.slice(-(MAX_STACK_SIZE - 1)), fullEntry]);
      setRedoStack([]); // Standard: new action clears redo stack
    },
    [undoWindowMs],
  );

  // ── Undo ──

  const undo = useCallback((): ActionHistoryEntry | null => {
    if (undoStack.length === 0) return null;

    const copy = [...undoStack];
    const undone = copy.pop()!;

    setUndoStack(copy);
    setRedoStack((prev) => [...prev.slice(-(MAX_STACK_SIZE - 1)), undone]);

    return undone;
  }, [undoStack]);

  // ── Redo ──

  const redo = useCallback((): ActionHistoryEntry | null => {
    if (redoStack.length === 0) return null;

    const copy = [...redoStack];
    const redone = copy.pop()!;

    setRedoStack(copy);
    setUndoStack((prev) => [...prev.slice(-(MAX_STACK_SIZE - 1)), redone]);

    return redone;
  }, [redoStack]);

  // ── Keyboard shortcuts ──

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const isModifier = e.ctrlKey || e.metaKey;
      if (!isModifier) return;

      // Skip when focus is inside a text input to avoid breaking native undo
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      if (e.key === 'z' || e.key === 'Z') {
        if (e.shiftKey) {
          // Ctrl+Shift+Z → redo
          e.preventDefault();
          redo();
        } else {
          // Ctrl+Z → undo
          e.preventDefault();
          undo();
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [undo, redo]);

  // ── Derived state ──

  const value = useMemo<UndoRedoContextValue>(
    () => ({
      pushAction,
      undo,
      redo,
      canUndo: undoStack.length > 0,
      canRedo: redoStack.length > 0,
      nextUndoDescription: undoStack.length > 0 ? undoStack[undoStack.length - 1].description : null,
      nextRedoDescription: redoStack.length > 0 ? redoStack[redoStack.length - 1].description : null,
    }),
    [pushAction, undo, redo, undoStack, redoStack],
  );

  return <UndoRedoContext.Provider value={value}>{children}</UndoRedoContext.Provider>;
}
