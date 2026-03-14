/**
 * pipelineMigration — pure functions to convert legacy flat-agent-list pipelines
 * into the new group-based format at load time.
 *
 * A pipeline is in legacy format if any stage has:
 * - `groups` is undefined, null, or an empty array, AND
 * - `agents` is a non-empty array
 *
 * The migration wraps each legacy stage's agents into a single ExecutionGroup
 * preserving the original execution_mode and agent order.
 *
 * The migration is idempotent — running it on an already-migrated pipeline is a no-op.
 */

import { generateId } from '@/utils/generateId';
import type { PipelineConfig, PipelineStage, ExecutionGroup } from '@/types';

/**
 * Returns true if the given stage is in legacy format (no groups, but has agents).
 */
export function isLegacyStage(stage: PipelineStage): boolean {
  return (!stage.groups || stage.groups.length === 0) && stage.agents.length > 0;
}

/**
 * Returns true if any stage in the pipeline is in legacy format.
 */
export function needsMigration(config: PipelineConfig): boolean {
  return config.stages.some(isLegacyStage);
}

/**
 * Migrate a single stage from legacy format to group format.
 * If the stage already has groups, it is returned unchanged.
 */
export function migrateStageToGroupFormat(stage: PipelineStage): PipelineStage {
  // Already migrated — has groups populated
  if (stage.groups && stage.groups.length > 0) {
    return stage;
  }

  // Legacy format — wrap agents in a single group
  const group: ExecutionGroup = {
    id: generateId(),
    order: 0,
    execution_mode: stage.execution_mode ?? 'sequential',
    agents: [...(stage.agents ?? [])],
  };

  return {
    ...stage,
    groups: [group],
    // Retain fields for backward compat
    agents: stage.agents ?? [],
    execution_mode: stage.execution_mode ?? 'sequential',
  };
}

/**
 * Migrate an entire pipeline config from legacy format to group format.
 * Each stage's flat agent list is wrapped into a single ExecutionGroup.
 * Already-migrated stages are left untouched (idempotent).
 */
export function migratePipelineToGroupFormat(config: PipelineConfig): PipelineConfig {
  return {
    ...config,
    stages: config.stages.map(migrateStageToGroupFormat),
  };
}

/**
 * Ensure every stage has at least one group.
 * Stages with no groups and no agents get a single empty default group.
 */
export function ensureDefaultGroups(config: PipelineConfig): PipelineConfig {
  return {
    ...config,
    stages: config.stages.map((stage) => {
      if (stage.groups && stage.groups.length > 0) return stage;
      if (stage.agents && stage.agents.length > 0) {
        return migrateStageToGroupFormat(stage);
      }
      // Empty stage — add one empty default group
      return {
        ...stage,
        groups: [
          {
            id: generateId(),
            order: 0,
            execution_mode: 'sequential' as const,
            agents: [],
          },
        ],
      };
    }),
  };
}
