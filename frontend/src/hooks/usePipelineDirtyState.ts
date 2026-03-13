/** Dirty-state tracking for pipeline config changes. */

import { useMemo, useCallback } from 'react';
import { computeSnapshot } from './usePipelineReducer';
import type { PipelineConfig, PipelineBoardState } from '@/types';
import type { PipelineAction } from './usePipelineReducer';

interface DirtyStateArgs {
  pipeline: PipelineConfig | null;
  savedSnapshot: string | null;
  editingPipelineId: string | null;
  boardState: PipelineBoardState;
  dispatch: React.Dispatch<PipelineAction>;
  resetPending: () => void;
}

export function usePipelineDirtyState({
  pipeline,
  savedSnapshot,
  editingPipelineId,
  dispatch,
  resetPending,
}: DirtyStateArgs) {
  const isDirty = useMemo(() => {
    if (!pipeline) return false;
    return computeSnapshot(pipeline) !== savedSnapshot;
  }, [pipeline, savedSnapshot]);

  const discardChanges = useCallback(() => {
    if (editingPipelineId && savedSnapshot) {
      dispatch({ type: 'DISCARD_EDITING' });
    } else {
      dispatch({ type: 'DISCARD_NEW' });
      resetPending();
    }
  }, [editingPipelineId, savedSnapshot, dispatch, resetPending]);

  return { isDirty, discardChanges };
}
