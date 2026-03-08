/**
 * PipelineSelector — per-Chore Agent Pipeline dropdown.
 *
 * Shows "Auto (Project Default)" as first option and saved pipelines by name.
 * Warns if the selected pipeline no longer exists.
 */

import { useId, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import type { PipelineConfigSummary } from '@/types';

interface PipelineSelectorProps {
  projectId: string;
  value: string; // "" = Auto, UUID = specific pipeline
  onChange: (pipelineId: string) => void;
  disabled?: boolean;
  inputId?: string;
}

export function PipelineSelector({ projectId, value, onChange, disabled, inputId }: PipelineSelectorProps) {
  const generatedId = useId();
  const selectId = inputId ?? `pipeline-select-${projectId}-${generatedId}`;
  const { data: pipelineList, isLoading } = useQuery({
    queryKey: ['pipelines', 'list', projectId],
    queryFn: () => pipelinesApi.list(projectId),
    staleTime: 60_000,
    enabled: !!projectId,
  });

  const pipelines: PipelineConfigSummary[] = useMemo(
    () => pipelineList?.pipelines ?? [],
    [pipelineList],
  );

  const selectedExists = value === '' || pipelines.some(p => p.id === value);

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={selectId} className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        Agent Pipeline
      </label>
      <select
        id={selectId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || isLoading}
        className="moonwell h-8 w-full rounded-md border-border/60 px-3 text-xs text-foreground disabled:opacity-50"
      >
        <option value="">Auto (Project Default)</option>
        {pipelines.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      {!selectedExists && value && (
        <p className="text-[10px] text-yellow-600 dark:text-yellow-400">
          ⚠ Selected pipeline no longer available — will use Auto
        </p>
      )}
    </div>
  );
}
