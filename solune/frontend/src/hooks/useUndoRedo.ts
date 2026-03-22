/**
 * Convenience hook wrapping UndoRedoContext.
 *
 * Provides type-safe access to the undo/redo stack with derived state.
 */

import { useContext } from 'react';
import { UndoRedoContext, type UndoRedoContextValue } from '@/context/UndoRedoContext';

export function useUndoRedo(): UndoRedoContextValue {
  return useContext(UndoRedoContext);
}
