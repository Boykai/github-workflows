/**
 * PipelineStagesSection — Displays pipeline stages with agent assignments
 * and a pipeline selector dropdown. Extracted from ProjectsPage.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown } from '@/lib/icons';
import { statusColorToCSS } from '@/components/board/colorUtils';
import { formatAgentName } from '@/utils/formatAgentName';
import { cn } from '@/lib/utils';
import type { CSSProperties } from 'react';
import type { StatusColor } from '@/types';

interface PipelineStage {
  name: string;
  agents: { id: string; agent_slug: string; agent_display_name?: string }[];
}

interface Pipeline {
  id: string;
  name: string;
  stages: PipelineStage[];
}

interface BoardColumn {
  status: { option_id: string; name: string; color: StatusColor };
  items: unknown[];
  item_count: number;
}

interface PipelineStagesSectionProps {
  columns: BoardColumn[];
  savedPipelines: Pipeline[];
  assignedPipelineId: string | undefined;
  assignPipelineMutation: {
    mutate: (pipelineId: string) => void;
    isPending: boolean;
  };
}

export function PipelineStagesSection({
  columns,
  savedPipelines,
  assignedPipelineId,
  assignPipelineMutation,
}: PipelineStagesSectionProps) {
  const [pipelineSelectorOpen, setPipelineSelectorOpen] = useState(false);
  const pipelineSelectorRef = useRef<HTMLDivElement>(null);

  const pipelineColumnCount = Math.max(columns.length, 1);
  const pipelineGridStyle = useMemo<CSSProperties>(
    () => ({ gridTemplateColumns: `repeat(${pipelineColumnCount}, minmax(min(14rem, 85vw), 1fr))` }),
    [pipelineColumnCount],
  );

  const assignedPipeline = useMemo(
    () => savedPipelines.find((pipeline) => pipeline.id === (assignedPipelineId ?? '')) ?? null,
    [assignedPipelineId, savedPipelines],
  );

  const assignedStageMap = useMemo(
    () => new Map((assignedPipeline?.stages ?? []).map((stage) => [stage.name.toLowerCase(), stage])),
    [assignedPipeline],
  );

  useEffect(() => {
    if (!pipelineSelectorOpen) return;

    function handlePointerDown(event: MouseEvent) {
      if (
        pipelineSelectorRef.current &&
        !pipelineSelectorRef.current.contains(event.target as Node)
      ) {
        setPipelineSelectorOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setPipelineSelectorOpen(false);
      }
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [pipelineSelectorOpen]);

  const handlePipelineSelection = useCallback(
    (pipelineId: string) => {
      setPipelineSelectorOpen(false);
      assignPipelineMutation.mutate(pipelineId);
    },
    [assignPipelineMutation],
  );

  return (
    <section id="pipeline-stages" className="space-y-4 scroll-mt-24">
      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 id="pipeline-stages-heading" className="text-lg font-semibold">
            Pipeline Stages
          </h3>
          {savedPipelines.length > 0 ? (
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                <span>Agent Pipeline</span>
                <div ref={pipelineSelectorRef} className="relative">
                  <button
                    type="button"
                    onClick={() => setPipelineSelectorOpen((current) => !current)}
                    disabled={assignPipelineMutation.isPending}
                    className={cn(
                      'project-pipeline-select project-pipeline-trigger flex h-9 min-w-[12rem] items-center justify-between gap-3 rounded-full px-4 text-xs font-medium text-foreground',
                      assignedPipelineId && 'project-pipeline-select-active',
                      pipelineSelectorOpen && 'project-pipeline-select-open',
                    )}
                    aria-haspopup="listbox"
                    aria-expanded={pipelineSelectorOpen}
                    aria-label="Agent Pipeline"
                  >
                    <span className="truncate">
                      {assignedPipeline?.name ?? 'No pipeline selected'}
                    </span>
                    <ChevronDown
                      className={cn(
                        'h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform',
                        pipelineSelectorOpen && 'rotate-180',
                      )}
                    />
                  </button>

                  {pipelineSelectorOpen && (
                    <div className="project-pipeline-menu absolute right-0 top-full z-30 mt-2 w-[min(20rem,calc(100vw-3rem))] overflow-hidden rounded-[1.1rem] border border-border/80">
                      <div className="border-b border-border/65 px-3 py-2.5 text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground/90">
                        Select pipeline
                      </div>
                      <div
                        className="max-h-72 overflow-y-auto p-1.5"
                        role="listbox"
                        aria-label="Agent Pipeline options"
                      >
                        <button
                          type="button"
                          role="option"
                          aria-selected={!assignedPipelineId}
                          onClick={() => handlePipelineSelection('')}
                          disabled={assignPipelineMutation.isPending}
                          className={cn(
                            'project-pipeline-option flex w-full items-center justify-between gap-3 rounded-[0.9rem] px-3 py-2.5 text-left text-sm disabled:cursor-not-allowed disabled:opacity-60',
                            !assignedPipelineId && 'project-pipeline-option-active',
                          )}
                        >
                          <span className="truncate">No pipeline selected</span>
                          {!assignedPipelineId && (
                            <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">
                              Current
                            </span>
                          )}
                        </button>
                        {savedPipelines.map((pipeline) => {
                          const isSelected = pipeline.id === (assignedPipelineId ?? '');

                          return (
                            <button
                              key={pipeline.id}
                              type="button"
                              role="option"
                              aria-selected={isSelected}
                              onClick={() => handlePipelineSelection(pipeline.id)}
                              disabled={assignPipelineMutation.isPending}
                              className={cn(
                                'project-pipeline-option flex w-full items-center justify-between gap-3 rounded-[0.9rem] px-3 py-2.5 text-left text-sm disabled:cursor-not-allowed disabled:opacity-60',
                                isSelected && 'project-pipeline-option-active',
                              )}
                            >
                              <span className="truncate">{pipeline.name}</span>
                              {isSelected && (
                                <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">
                                  Current
                                </span>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <Link
              to="/pipeline"
              className="solar-chip-soft inline-flex items-center rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] transition-colors hover:bg-primary/10 hover:text-foreground"
            >
              Create new pipeline
            </Link>
          )}
        </div>
        <div className="overflow-x-auto pb-2">
          <div
            className="grid min-w-full items-stretch gap-3"
            style={pipelineGridStyle}
            role="region"
            aria-labelledby="pipeline-stages-heading"
          >
            {columns.map((col) => {
              const assigned = assignedStageMap.get(col.status.name.toLowerCase())?.agents ?? [];
              const dotColor = statusColorToCSS(col.status.color);

              return (
                <div
                  key={col.status.option_id}
                  className="celestial-panel pipeline-stage-card flex h-full min-w-0 flex-col items-center gap-2 rounded-[1.2rem] border border-border/75 bg-background/28 p-4 text-center shadow-sm sm:rounded-[1.35rem]"
                >
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: dotColor }}
                  />
                  <span className="text-sm font-medium">{col.status.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {col.item_count} items
                  </span>
                  {assigned.length > 0 ? (
                    <div className="mt-1 flex flex-wrap justify-center gap-1">
                      {assigned.map((assignment) => (
                        <span
                          key={assignment.id}
                          className="solar-chip rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]"
                        >
                          {formatAgentName(
                            assignment.agent_slug,
                            assignment.agent_display_name,
                          )}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="mt-1 text-[10px] text-muted-foreground/60">
                      No agents
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
