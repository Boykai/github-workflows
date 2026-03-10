/**
 * AgentPresetSelector component - renders preset buttons
 * (Clear, GitHub Copilot, Spec Kit) plus saved pipeline configurations
 * with confirmation dialog before replacing current agent configuration.
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { AgentAssignment, AgentPreset, PipelineConfigSummary, PipelineConfig } from '@/types';
import { useConfirmation } from '@/hooks/useConfirmation';
import { cn } from '@/lib/utils';
import { generateId } from '@/utils/generateId';
import { formatAgentName } from '@/utils/formatAgentName';
import { pipelinesApi } from '@/services/api';

function makeAssignment(slug: string, displayName: string): AgentAssignment {
  return { id: generateId(), slug, display_name: displayName };
}

/**
 * Build preset mappings by matching preset status keys (case-insensitive)
 * to actual project column names. Non-matching columns get empty arrays.
 */
function resolvePreset(
  preset: AgentPreset,
  columnNames: string[]
): Record<string, AgentAssignment[]> {
  const result: Record<string, AgentAssignment[]> = {};
  const lowerMap = new Map<string, string>();

  for (const col of columnNames) {
    lowerMap.set(col.toLowerCase(), col);
    result[col] = [];
  }

  for (const [statusKey, assignments] of Object.entries(preset.mappings)) {
    const actualCol = lowerMap.get(statusKey.toLowerCase());
    if (actualCol) {
      // Deep-clone each assignment with fresh UUIDs
      result[actualCol] = assignments.map((a) =>
        makeAssignment(a.slug, formatAgentName(a.slug, a.display_name))
      );
    }
  }

  return result;
}

/**
 * Convert a saved PipelineConfig to agent assignment mappings.
 */
function pipelineConfigToMappings(
  config: PipelineConfig,
  columnNames: string[]
): Record<string, AgentAssignment[]> {
  const result: Record<string, AgentAssignment[]> = {};
  const lowerMap = new Map<string, string>();

  for (const col of columnNames) {
    lowerMap.set(col.toLowerCase(), col);
    result[col] = [];
  }

  for (const stage of config.stages) {
    const matchedCol = lowerMap.get(stage.name.toLowerCase());
    if (matchedCol) {
      result[matchedCol] = stage.agents.map((agent) =>
        makeAssignment(
          agent.agent_slug,
          formatAgentName(agent.agent_slug, agent.agent_display_name)
        )
      );
    }
  }

  return result;
}

function mappingsMatch(
  expectedMappings: Record<string, { slug: string }[]>,
  currentMappings: Record<string, { slug: string }[]>,
  columnNames: string[]
): boolean {
  for (const col of columnNames) {
    const expectedAgents = expectedMappings[col] ?? [];
    const currentAgents = currentMappings[col] ?? [];

    if (expectedAgents.length !== currentAgents.length) {
      return false;
    }

    for (let index = 0; index < expectedAgents.length; index++) {
      if (expectedAgents[index].slug !== currentAgents[index].slug) {
        return false;
      }
    }
  }

  return true;
}

// ============ Preset Definitions (T025) ============

const PRESETS: AgentPreset[] = [
  {
    id: 'custom',
    label: 'Clear',
    description: 'Clear all agent assignments',
    mappings: {},
  },
  {
    id: 'copilot',
    label: 'GitHub Copilot',
    description: 'Copilot for implementation, Copilot Review for reviews',
    mappings: {
      'In Progress': [makeAssignment('copilot', 'GitHub Copilot')],
      'In Review': [makeAssignment('copilot-review', 'Copilot Review')],
    },
  },
  {
    id: 'speckit',
    label: 'Spec Kit',
    description: 'Full Spec Kit pipeline with specification, planning, and implementation',
    mappings: {
      Backlog: [makeAssignment('speckit.specify', 'Spec Kit - Specify')],
      Ready: [
        makeAssignment('speckit.plan', 'Spec Kit - Plan'),
        makeAssignment('speckit.tasks', 'Spec Kit - Tasks'),
      ],
      'In Progress': [makeAssignment('speckit.implement', 'Spec Kit - Implement')],
      'In Review': [makeAssignment('copilot-review', 'Copilot Review')],
    },
  },
];

// ============ Component ============

interface AgentPresetSelectorProps {
  /** Actual project column names */
  columnNames: string[];
  /** Current agent mappings (to detect active preset) */
  currentMappings: Record<string, { slug: string }[]>;
  /** Apply a preset configuration */
  onApplyPreset: (mappings: Record<string, AgentAssignment[]>) => void;
  /** Project ID for fetching saved pipeline configs */
  projectId?: string | null;
  /** Render only the saved pipeline dropdown trigger */
  dropdownOnly?: boolean;
}

/**
 * Check if the current mappings match a preset (by comparing slugs
 * per status column, ignoring columns with no agents in either).
 */
function matchesPreset(
  preset: AgentPreset,
  currentMappings: Record<string, { slug: string }[]>,
  columnNames: string[]
): boolean {
  if (preset.id === 'custom') {
    // Clear matches when all columns are empty
    return columnNames.every((col) => (currentMappings[col] ?? []).length === 0);
  }

  const resolved = resolvePreset(preset, columnNames);
  for (const col of columnNames) {
    const presetAgents = resolved[col] ?? [];
    const currentAgents = currentMappings[col] ?? [];
    if (presetAgents.length !== currentAgents.length) return false;
    for (let i = 0; i < presetAgents.length; i++) {
      if (presetAgents[i].slug !== currentAgents[i].slug) return false;
    }
  }
  return true;
}

export function AgentPresetSelector({
  columnNames,
  currentMappings,
  onApplyPreset,
  projectId,
  dropdownOnly = false,
}: AgentPresetSelectorProps) {
  const [showDropdown, setShowDropdown] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const restoredProjectRef = useRef<string | null>(null);
  const { confirm } = useConfirmation();

  // Fetch saved pipeline configurations
  const { data: savedPipelines } = useQuery({
    queryKey: ['pipelines', projectId],
    queryFn: () => pipelinesApi.list(projectId!),
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000,
  });

  // Persist selected config to localStorage
  const persistSelection = useCallback(
    (configId: string) => {
      if (projectId) {
        localStorage.setItem(`pipeline-config:${projectId}`, configId);
      }
    },
    [projectId]
  );

  useEffect(() => {
    if (!showDropdown) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowDropdown(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showDropdown]);

  useEffect(() => {
    restoredProjectRef.current = null;
    setApplyError(null);
    setShowDropdown(false);
  }, [projectId]);

  useEffect(() => {
    if (!projectId || restoredProjectRef.current === projectId) {
      return undefined;
    }

    const storedSelection = localStorage.getItem(`pipeline-config:${projectId}`);
    restoredProjectRef.current = projectId;

    if (!storedSelection) {
      return undefined;
    }

    let cancelled = false;

    const restoreSelection = async () => {
      try {
        if (storedSelection.startsWith('builtin:')) {
          const presetId = storedSelection.slice('builtin:'.length);
          const preset = PRESETS.find((candidate) => candidate.id === presetId);
          if (preset) {
            onApplyPreset(resolvePreset(preset, columnNames));
          }
          return;
        }

        const fullConfig = await pipelinesApi.get(projectId, storedSelection);
        if (!cancelled) {
          onApplyPreset(pipelineConfigToMappings(fullConfig, columnNames));
        }
      } catch {
        if (!cancelled) {
          setApplyError('Failed to restore the saved pipeline selection.');
        }
      }
    };

    void restoreSelection();

    return () => {
      cancelled = true;
    };
  }, [columnNames, onApplyPreset, projectId]);

  const handlePresetClick = useCallback(
    (preset: AgentPreset) => {
      const isClearingPreset = preset.id === 'custom';
      setApplyError(null);
      setShowDropdown(false);
      void confirm({
        title: isClearingPreset
          ? 'Clear pipeline assignments?'
          : `Apply “${preset.label}” preset?`,
        description: isClearingPreset
          ? 'This will remove all agents from the pipeline board. Unsaved changes will be reflected in the save bar.'
          : 'This will replace your current agent configuration. Unsaved changes will be reflected in the save bar.',
        variant: isClearingPreset ? 'warning' : 'info',
        confirmLabel: isClearingPreset ? 'Clear' : 'Apply Preset',
        onConfirm: async () => {
          const resolved = resolvePreset(preset, columnNames);
          onApplyPreset(resolved);
          persistSelection(`builtin:${preset.id}`);
          setApplyError(null);
        },
      });
    },
    [columnNames, confirm, onApplyPreset, persistSelection]
  );

  const handlePipelineClick = useCallback(
    (pipeline: PipelineConfigSummary) => {
      if (!projectId) {
        return;
      }

      setApplyError(null);
      setShowDropdown(false);
      void confirm({
        title: `Apply “${pipeline.name}” pipeline?`,
        description:
          'This will replace your current agent configuration with the saved pipeline. Unsaved changes will be reflected in the save bar.',
        variant: 'info',
        confirmLabel: 'Apply Pipeline',
        onConfirm: async () => {
          const fullConfig = await pipelinesApi.get(projectId, pipeline.id);
          const mappings = pipelineConfigToMappings(fullConfig, columnNames);
          onApplyPreset(mappings);
          persistSelection(pipeline.id);
          setApplyError(null);
        },
      });
    },
    [columnNames, confirm, onApplyPreset, persistSelection, projectId]
  );

  const hasSavedPipelines = (savedPipelines?.pipelines?.length ?? 0) > 0;

  const selectedSavedPipelineId = useMemo(() => {
    if (!projectId) return null;
    const storedSelection = localStorage.getItem(`pipeline-config:${projectId}`);
    if (!storedSelection || storedSelection.startsWith('builtin:')) return null;
    return storedSelection;
  }, [projectId]);

  const { data: activeSavedPipelineConfig } = useQuery({
    queryKey: ['pipeline', projectId, selectedSavedPipelineId],
    queryFn: () => pipelinesApi.get(projectId!, selectedSavedPipelineId!),
    enabled: !!projectId && !!selectedSavedPipelineId,
    staleTime: 5 * 60 * 1000,
  });

  // Derive active saved pipeline name for display (T017/T018)
  const activePipelineName = useMemo(() => {
    if (
      !selectedSavedPipelineId ||
      !savedPipelines?.pipelines?.length ||
      !activeSavedPipelineConfig
    ) {
      return null;
    }

    const matchedPipeline = savedPipelines.pipelines.find(
      (pipeline) => pipeline.id === selectedSavedPipelineId
    );
    if (!matchedPipeline) return null;

    const resolvedMappings = pipelineConfigToMappings(activeSavedPipelineConfig, columnNames);
    if (!mappingsMatch(resolvedMappings, currentMappings, columnNames)) {
      return null;
    }

    return matchedPipeline.name;
  }, [
    selectedSavedPipelineId,
    savedPipelines,
    activeSavedPipelineConfig,
    columnNames,
    currentMappings,
  ]);

  return (
    <>
      <div className="ml-auto flex items-center gap-1 rounded-xl border border-border/60 bg-background/56 p-1 shadow-sm">
        {!dropdownOnly &&
          PRESETS.map((preset) => {
            const isActive = matchesPreset(preset, currentMappings, columnNames);
            return (
              <button
                key={preset.id}
                className={cn(
                  'rounded-md px-3 py-1 text-xs font-semibold transition-colors',
                  isActive
                    ? 'solar-chip-soft'
                    : 'text-muted-foreground hover:bg-primary/10 hover:text-foreground'
                )}
                onClick={() => handlePresetClick(preset)}
                title={preset.description}
                type="button"
              >
                {preset.label}
              </button>
            );
          })}

        {/* Saved pipelines dropdown */}
        {hasSavedPipelines && (
          <div className="relative">
            <button
              className={cn(
                'rounded-md px-3 py-1 text-xs font-semibold transition-colors',
                activePipelineName
                  ? 'solar-chip-soft'
                  : 'text-muted-foreground hover:bg-primary/10 hover:text-foreground'
              )}
              onClick={() => setShowDropdown(!showDropdown)}
              title={
                activePipelineName
                  ? `Active saved pipeline: ${activePipelineName}`
                  : 'Saved pipeline configurations'
              }
              type="button"
            >
              {activePipelineName ?? 'Saved'} ▾
            </button>
            {showDropdown && (
              <>
                {/* Backdrop to close dropdown */}
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowDropdown(false)}
                  role="presentation"
                />
                <div className="absolute right-0 top-full z-50 mt-1 w-56 rounded-xl border border-border bg-popover shadow-lg backdrop-blur-sm py-1">
                  {savedPipelines?.pipelines.map((pipeline) => (
                    <button
                      key={pipeline.id}
                      className="w-full px-3 py-2 text-left text-xs transition-colors hover:bg-primary/10"
                      onClick={() => handlePipelineClick(pipeline)}
                      type="button"
                    >
                      <div className="font-medium text-foreground truncate">{pipeline.name}</div>
                      <div className="text-muted-foreground">
                        {pipeline.stage_count} stages · {pipeline.agent_count} agents
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {applyError && (
        <div
          className="mt-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive"
          role="alert"
        >
          {applyError}
        </div>
      )}
    </>
  );
}
