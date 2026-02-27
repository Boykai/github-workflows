/**
 * AgentPresetSelector component - renders three preset buttons
 * (Custom, GitHub Copilot, Spec Kit) with confirmation dialog
 * before replacing current agent configuration (T025, T026).
 */

import { useState, useCallback } from 'react';
import type { AgentAssignment, AgentPreset } from '@/types';
import { generateId } from '@/utils/generateId';

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
        makeAssignment(a.slug, a.display_name ?? a.slug)
      );
    }
  }

  return result;
}

// ============ Preset Definitions (T025) ============

const PRESETS: AgentPreset[] = [
  {
    id: 'custom',
    label: 'Custom',
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
    // Custom matches when all columns are empty
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
}: AgentPresetSelectorProps) {
  const [confirmPreset, setConfirmPreset] = useState<AgentPreset | null>(null);

  const handleClick = useCallback((preset: AgentPreset) => {
    setConfirmPreset(preset);
  }, []);

  const handleConfirm = useCallback(() => {
    if (!confirmPreset) return;
    const resolved = resolvePreset(confirmPreset, columnNames);
    onApplyPreset(resolved);
    setConfirmPreset(null);
  }, [confirmPreset, columnNames, onApplyPreset]);

  const handleCancel = useCallback(() => {
    setConfirmPreset(null);
  }, []);

  return (
    <>
      <div className="flex items-center gap-1 ml-auto bg-muted/50 p-1 rounded-md border border-border/50">
        {PRESETS.map((preset) => {
          const isActive = matchesPreset(preset, currentMappings, columnNames);
          return (
            <button
              key={preset.id}
              className={`px-3 py-1 text-xs font-medium rounded-sm transition-colors ${isActive ? 'bg-background text-foreground shadow-sm border border-border/50' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
              onClick={() => handleClick(preset)}
              title={preset.description}
              type="button"
            >
              {preset.label}
            </button>
          );
        })}
      </div>

      {/* Confirmation dialog */}
      {confirmPreset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm" onClick={handleCancel}>
          <div
            className="bg-card border border-border rounded-lg shadow-lg w-full max-w-md p-6 flex flex-col gap-4"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Confirm preset"
          >
            <h4 className="text-lg font-semibold text-foreground m-0">
              Apply &ldquo;{confirmPreset.label}&rdquo; preset?
            </h4>
            <p className="text-sm text-muted-foreground m-0">
              This will replace your current agent configuration. Unsaved changes will be reflected
              in the save bar.
            </p>
            <div className="flex justify-end gap-3 mt-2">
              <button
                className="px-4 py-2 text-sm font-medium rounded-md border border-border bg-background text-foreground hover:bg-muted transition-colors"
                onClick={handleCancel}
                type="button"
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                onClick={handleConfirm}
                type="button"
              >
                Apply Preset
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
