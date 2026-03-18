/**
 * AgentPresetSelector component - renders preset buttons
 * (Clear, GitHub Copilot, Spec Kit) plus saved pipeline configurations
 * with confirmation dialog before replacing current agent configuration.
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { AgentAssignment, AgentPreset, PipelineConfigSummary, PipelineConfig } from '@/types';
import { generateId } from '@/utils/generateId';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { formatAgentName } from '@/utils/formatAgentName';
import { pipelinesApi } from '@/services/api';
import { cn } from '@/lib/utils';

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
      const stageAgents = (stage.groups ?? []).flatMap((g) => g.agents);
      const agents = stageAgents.length > 0 ? stageAgents : stage.agents;
      result[matchedCol] = agents.map((agent) =>
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
  const [confirmPreset, setConfirmPreset] = useState<AgentPreset | null>(null);
  const [confirmPipeline, setConfirmPipeline] = useState<PipelineConfigSummary | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const restoredProjectRef = useRef<string | null>(null);

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

  const handleDropdownChange = useCallback((open: boolean) => {
    setShowDropdown(open);
  }, []);

  const [prevProjectId, setPrevProjectId] = useState(projectId);
  if (projectId !== prevProjectId) {
    setPrevProjectId(projectId);
    setApplyError(null);
    setShowDropdown(false);
    setConfirmPreset(null);
    setConfirmPipeline(null);
  }

  // Reset restored project ref when projectId changes (must be in effect, not render)
  useEffect(() => {
    restoredProjectRef.current = null;
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

  const handlePresetClick = useCallback((preset: AgentPreset) => {
    setApplyError(null);
    setConfirmPreset(preset);
    setShowDropdown(false);
  }, []);

  const handlePipelineClick = useCallback((pipeline: PipelineConfigSummary) => {
    setApplyError(null);
    setConfirmPipeline(pipeline);
    setShowDropdown(false);
  }, []);

  const handleConfirmPreset = useCallback(() => {
    if (!confirmPreset) return;
    const resolved = resolvePreset(confirmPreset, columnNames);
    onApplyPreset(resolved);
    persistSelection(`builtin:${confirmPreset.id}`);
    setApplyError(null);
    setConfirmPreset(null);
  }, [confirmPreset, columnNames, onApplyPreset, persistSelection]);

  const handleConfirmPipeline = useCallback(async () => {
    if (!confirmPipeline || !projectId) return;
    try {
      const fullConfig = await pipelinesApi.get(projectId, confirmPipeline.id);
      const mappings = pipelineConfigToMappings(fullConfig, columnNames);
      onApplyPreset(mappings);
      persistSelection(confirmPipeline.id);
      setApplyError(null);
      setConfirmPipeline(null);
    } catch {
      setApplyError('Failed to load and apply the selected pipeline. Please try again.');
    }
  }, [confirmPipeline, projectId, columnNames, onApplyPreset, persistSelection]);

  const handleCancel = useCallback(() => {
    setConfirmPreset(null);
    setConfirmPipeline(null);
  }, []);

  const isClearingPreset = confirmPreset?.id === 'custom';

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
                className={cn('celestial-focus rounded-md px-3 py-1 text-xs font-semibold transition-colors', isActive ? 'solar-chip-soft' : 'text-muted-foreground hover:bg-primary/10 hover:text-foreground')}
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
          <Popover open={showDropdown} onOpenChange={handleDropdownChange}>
            <PopoverTrigger asChild>
              <button
                className={cn('celestial-focus rounded-md px-3 py-1 text-xs font-semibold transition-colors', activePipelineName
                    ? 'solar-chip-soft'
                    : 'text-muted-foreground hover:bg-primary/10 hover:text-foreground')}
                aria-label={
                  activePipelineName
                    ? `Active saved pipeline: ${activePipelineName}`
                    : 'Saved pipeline configurations'
                }
                type="button"
              >
                {activePipelineName ?? 'Saved'} ▾
              </button>
            </PopoverTrigger>
            <PopoverContent side="bottom" align="end" className="w-56 p-0 py-1">
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
            </PopoverContent>
          </Popover>
        )}
      </div>

      {/* Confirmation dialog for built-in presets */}
      {confirmPreset && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          onClick={handleCancel}
          onKeyDown={(e) => {
            if (e.key === 'Escape') handleCancel();
          }}
          role="presentation"
        >
          {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions */}
          <div
            className="celestial-panel flex w-full max-w-md flex-col gap-4 rounded-[1.2rem] border border-border p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Confirm preset"
          >
            <h4 className="text-lg font-semibold text-foreground m-0">
              {isClearingPreset
                ? 'Clear pipeline assignments?'
                : `Apply “${confirmPreset.label}” preset?`}
            </h4>
            <p className="text-sm text-muted-foreground m-0">
              {isClearingPreset
                ? 'This will remove all agents from the pipeline board. Unsaved changes will be reflected in the save bar.'
                : 'This will replace your current agent configuration. Unsaved changes will be reflected in the save bar.'}
            </p>
            <div className="flex justify-end gap-3 mt-2">
              <button
                className="celestial-focus solar-action rounded-full px-4 py-2 text-sm font-medium transition-colors"
                onClick={handleCancel}
                type="button"
              >
                Cancel
              </button>
              <button
                className="celestial-focus px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                onClick={handleConfirmPreset}
                type="button"
              >
                {isClearingPreset ? 'Clear' : 'Apply Preset'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation dialog for saved pipeline */}
      {confirmPipeline && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          onClick={handleCancel}
          onKeyDown={(e) => {
            if (e.key === 'Escape') handleCancel();
          }}
          role="presentation"
        >
          {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions */}
          <div
            className="celestial-panel flex w-full max-w-md flex-col gap-4 rounded-[1.2rem] border border-border p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Confirm pipeline configuration"
          >
            <h4 className="text-lg font-semibold text-foreground m-0">
              Apply &ldquo;{confirmPipeline.name}&rdquo; pipeline?
            </h4>
            <p className="text-sm text-muted-foreground m-0">
              This will replace your current agent configuration with the saved pipeline. Unsaved
              changes will be reflected in the save bar.
            </p>
            {applyError && (
              <div
                className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
                role="alert"
              >
                {applyError}
              </div>
            )}
            <div className="flex justify-end gap-3 mt-2">
              <button
                className="celestial-focus solar-action rounded-full px-4 py-2 text-sm font-medium transition-colors"
                onClick={handleCancel}
                type="button"
              >
                Cancel
              </button>
              <button
                className="celestial-focus px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                onClick={handleConfirmPipeline}
                type="button"
              >
                Apply Pipeline
              </button>
            </div>
          </div>
        </div>
      )}

      {applyError && !confirmPipeline && (
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
