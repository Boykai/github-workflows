/**
 * Reducer + types for usePipelineConfig state management.
 */

import type { PipelineConfig, PipelineBoardState } from '@/types';
import type { SetStateAction } from 'react';
import { ensureDefaultGroups } from '@/lib/pipelineMigration';

export interface PipelineState {
  boardState: PipelineBoardState;
  pipeline: PipelineConfig | null;
  editingPipelineId: string | null;
  isSaving: boolean;
  saveError: string | null;
  savedSnapshot: string | null;
}

export type PipelineAction =
  | { type: 'NEW_PIPELINE'; config: PipelineConfig }
  | { type: 'LOAD_SUCCESS'; config: PipelineConfig; id: string }
  | { type: 'SAVE_START' }
  | { type: 'SAVE_SUCCESS'; config: PipelineConfig }
  | { type: 'SAVE_FAILURE'; error: string }
  | { type: 'DELETE_SUCCESS' }
  | { type: 'SET_PIPELINE'; updater: SetStateAction<PipelineConfig | null> }
  | { type: 'SET_ERROR'; error: string }
  | { type: 'DISCARD_EDITING' }
  | { type: 'DISCARD_NEW' };

export const initialState: PipelineState = {
  boardState: 'empty',
  pipeline: null,
  editingPipelineId: null,
  isSaving: false,
  saveError: null,
  savedSnapshot: null,
};

export function computeSnapshot(p: PipelineConfig): string {
  return JSON.stringify({
    name: p.name,
    description: p.description,
    stages: p.stages,
  });
}

export function pipelineReducer(state: PipelineState, action: PipelineAction): PipelineState {
  switch (action.type) {
    case 'NEW_PIPELINE': {
      const migrated = ensureDefaultGroups(action.config);
      return {
        ...state,
        boardState: 'creating',
        pipeline: migrated,
        editingPipelineId: null,
        isSaving: false,
        saveError: null,
        savedSnapshot: computeSnapshot(migrated),
      };
    }
    case 'LOAD_SUCCESS': {
      const migrated = ensureDefaultGroups(action.config);
      return {
        ...state,
        boardState: 'editing',
        pipeline: migrated,
        editingPipelineId: action.id,
        saveError: null,
        savedSnapshot: computeSnapshot(migrated),
      };
    }
    case 'SAVE_START':
      return { ...state, isSaving: true, saveError: null };
    case 'SAVE_SUCCESS': {
      const migrated = ensureDefaultGroups(action.config);
      return {
        ...state,
        pipeline: migrated,
        editingPipelineId: migrated.id,
        boardState: 'editing',
        isSaving: false,
        savedSnapshot: computeSnapshot(migrated),
      };
    }
    case 'SAVE_FAILURE':
      return { ...state, isSaving: false, saveError: action.error };
    case 'DELETE_SUCCESS':
      return { ...initialState };
    case 'SET_PIPELINE': {
      const pipeline =
        typeof action.updater === 'function' ? action.updater(state.pipeline) : action.updater;
      return { ...state, pipeline };
    }
    case 'SET_ERROR':
      return { ...state, saveError: action.error };
    case 'DISCARD_EDITING': {
      if (!state.savedSnapshot) return state;
      let saved: Record<string, unknown>;
      try {
        saved = JSON.parse(state.savedSnapshot) as Record<string, unknown>;
      } catch {
        return { ...state, saveError: 'Failed to restore saved pipeline state' };
      }
      return {
        ...state,
        pipeline: state.pipeline ? { ...state.pipeline, ...saved } : null,
        saveError: null,
      };
    }
    case 'DISCARD_NEW':
      return { ...initialState };
    default:
      return state;
  }
}
