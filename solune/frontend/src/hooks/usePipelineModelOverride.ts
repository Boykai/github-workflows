/**
 * usePipelineModelOverride — derives and manages model override state.
 */

import { useState, useCallback, useMemo } from 'react';
import type { PipelineConfig, PipelineModelOverride } from '@/types';
import type { Dispatch, SetStateAction } from 'react';

function deriveModelOverride(config: PipelineConfig | null): PipelineModelOverride {
  if (!config) {
    return { mode: 'auto', modelId: '', modelName: '' };
  }

  // Collect agents from groups (preferred) with fallback to legacy agents field
  const agents = config.stages.flatMap((stage) => {
    const fromGroups = (stage.groups ?? []).flatMap((g) => g.agents);
    return fromGroups.length > 0 ? fromGroups : stage.agents;
  });
  if (agents.length === 0) {
    return { mode: 'auto', modelId: '', modelName: '' };
  }

  const uniqueModels = [...new Set(agents.map((agent) => agent.model_id || ''))];
  if (uniqueModels.length === 1) {
    const modelId = uniqueModels[0];
    if (!modelId) {
      return { mode: 'auto', modelId: '', modelName: '' };
    }
    const matchingAgent = agents.find((agent) => agent.model_id === modelId);
    return {
      mode: 'specific',
      modelId,
      modelName: matchingAgent?.model_name ?? '',
    };
  }

  return { mode: 'mixed', modelId: '', modelName: '' };
}

export interface UsePipelineModelOverrideReturn {
  modelOverride: PipelineModelOverride;
  setModelOverride: (override: PipelineModelOverride) => void;
  resetPending: () => void;
}

export function usePipelineModelOverride(
  pipeline: PipelineConfig | null,
  setPipeline: Dispatch<SetStateAction<PipelineConfig | null>>,
): UsePipelineModelOverrideReturn {
  const [pendingModelOverride, setPendingModelOverride] = useState<PipelineModelOverride | null>(
    null,
  );

  const hasAnyAgents = useMemo(
    () =>
      pipeline?.stages.some((stage) => {
        const fromGroups = (stage.groups ?? []).flatMap((g) => g.agents);
        return fromGroups.length > 0 || stage.agents.length > 0;
      }) ?? false,
    [pipeline],
  );

  const modelOverride = useMemo(() => {
    const derived = deriveModelOverride(pipeline);
    if (hasAnyAgents) return derived;
    return pendingModelOverride ?? derived;
  }, [hasAnyAgents, pendingModelOverride, pipeline]);

  const setModelOverride = useCallback(
    (override: PipelineModelOverride) => {
      setPendingModelOverride(override);
      setPipeline((prev) => {
        if (!prev) return null;
        const applyOverride = (agent: typeof prev.stages[0]['agents'][0]) => ({
          ...agent,
          model_id: override.mode === 'specific' ? override.modelId : '',
          model_name: override.mode === 'specific' ? override.modelName : '',
        });
        const updatedStages = prev.stages.map((stage) => ({
          ...stage,
          groups: (stage.groups ?? []).map((group) => ({
            ...group,
            agents: group.agents.map(applyOverride),
          })),
          agents: stage.agents.map(applyOverride),
        }));
        return { ...prev, stages: updatedStages };
      });
    },
    [setPipeline],
  );

  const resetPendingOverride = useCallback(() => {
    setPendingModelOverride(null);
  }, []);

  return { modelOverride, setModelOverride, resetPending: resetPendingOverride };
}
