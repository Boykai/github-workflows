/**
 * PipelineStagesPanel — Pipeline stages visualization with pipeline assignment dropdown.
 * Extracted from ProjectsPage to keep the page within 250 lines.
 */

import { useRef, useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';
import { statusColorToCSS } from '@/components/board/colorUtils';
import { formatAgentName } from '@/utils/formatAgentName';
import { cn } from '@/lib/utils';
import type { BoardColumn, PipelineConfigSummary, PipelineStage, ProjectPipelineAssignment } from '@/types';

interface PipelineStagesPanelProps {
  columns: BoardColumn[];
  pipelineGridStyle: React.CSSProperties;
  assignedStageMap: Map<string, PipelineStage>;
  savedPipelines: PipelineConfigSummary[] | undefined;
  pipelineAssignment: ProjectPipelineAssignment | undefined;
  assignedPipeline: PipelineConfigSummary | null;
  isAssigning: boolean;
  onPipelineSelect: (pipelineId: string) => void;
}

export function PipelineStagesPanel({
  columns,
  pipelineGridStyle,
  assignedStageMap,
  savedPipelines,
  pipelineAssignment,
  assignedPipeline,
  isAssigning,
  onPipelineSelect,
}: PipelineStagesPanelProps) {
  const [selectorOpen, setSelectorOpen] = useState(false);
  const selectorRef = useRef<HTMLDivElement>(null);

  // Close selector on outside click or Escape
  useEffect(() => {
    if (!selectorOpen) return;
    const handlePointerDown = (e: MouseEvent) => {
      if (selectorRef.current && !selectorRef.current.contains(e.target as Node)) {
        setSelectorOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectorOpen(false);
    };
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectorOpen]);

  const handleSelect = useCallback(
    (pipelineId: string) => {
      setSelectorOpen(false);
      onPipelineSelect(pipelineId);
    },
    [onPipelineSelect]
  );

  return (
    <section id="pipeline-stages" className="space-y-4 scroll-mt-24">
      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 id="pipeline-stages-heading" className="text-lg font-semibold">
            Pipeline Stages
          </h3>
          {(savedPipelines?.length ?? 0) > 0 ? (
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                <span>Agent Pipeline</span>
                <div ref={selectorRef} className="relative">
                  <button
                    type="button"
                    onClick={() => setSelectorOpen((c) => !c)}
                    disabled={isAssigning}
                    className={cn(
                      'project-pipeline-select project-pipeline-trigger flex h-9 min-w-[12rem] items-center justify-between gap-3 rounded-full px-4 text-xs font-medium text-foreground',
                      pipelineAssignment?.pipeline_id && 'project-pipeline-select-active',
                      selectorOpen && 'project-pipeline-select-open'
                    )}
                    aria-haspopup="listbox"
                    aria-expanded={selectorOpen}
                    aria-label="Agent Pipeline"
                  >
                    <span className="truncate">
                      {assignedPipeline?.name ?? 'No pipeline selected'}
                    </span>
                    <ChevronDown
                      aria-hidden="true"
                      className={cn(
                        'h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform',
                        selectorOpen && 'rotate-180'
                      )}
                    />
                  </button>

                  {selectorOpen && (
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
                          aria-selected={!pipelineAssignment?.pipeline_id}
                          onClick={() => handleSelect('')}
                          disabled={isAssigning}
                          className={cn(
                            'project-pipeline-option flex w-full items-center justify-between gap-3 rounded-[0.9rem] px-3 py-2.5 text-left text-sm disabled:cursor-not-allowed disabled:opacity-60',
                            !pipelineAssignment?.pipeline_id && 'project-pipeline-option-active'
                          )}
                        >
                          <span className="truncate">No pipeline selected</span>
                          {!pipelineAssignment?.pipeline_id && (
                            <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">Current</span>
                          )}
                        </button>
                        {savedPipelines?.map((pipeline) => {
                          const isSelected = pipeline.id === (pipelineAssignment?.pipeline_id ?? '');
                          return (
                            <button
                              key={pipeline.id}
                              type="button"
                              role="option"
                              aria-selected={isSelected}
                              onClick={() => handleSelect(pipeline.id)}
                              disabled={isAssigning}
                              className={cn(
                                'project-pipeline-option flex w-full items-center justify-between gap-3 rounded-[0.9rem] px-3 py-2.5 text-left text-sm disabled:cursor-not-allowed disabled:opacity-60',
                                isSelected && 'project-pipeline-option-active'
                              )}
                            >
                              <span className="truncate">{pipeline.name}</span>
                              {isSelected && (
                                <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">Current</span>
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
                    aria-label={col.status.name}
                  />
                  <span className="text-sm font-medium">{col.status.name}</span>
                  <span className="text-xs text-muted-foreground">{col.item_count} items</span>
                  {assigned.length > 0 ? (
                    <div className="mt-1 flex flex-wrap justify-center gap-1">
                      {assigned.map((a) => (
                        <span
                          key={a.id}
                          className="solar-chip rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]"
                        >
                          {formatAgentName(a.agent_slug, a.agent_display_name)}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="mt-1 text-[10px] text-muted-foreground/60">No agents</span>
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
