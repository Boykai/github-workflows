/**
 * PipelineStagesSection — Displays board columns with their assigned pipeline agents.
 * Extracted from ProjectsPage to reduce page size and improve modularity.
 */

import { useMemo, type CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import { statusColorToCSS } from '@/components/board/colorUtils';
import { PipelineSelector } from '@/components/board/PipelineSelector';
import { formatAgentName } from '@/utils/formatAgentName';
import type { PipelineConfigSummary, PipelineStage, StatusColor } from '@/types';

interface BoardColumn {
  status: {
    option_id: string;
    name: string;
    color: StatusColor;
  };
  item_count: number;
  items: unknown[];
}

export interface PipelineStagesSectionProps {
  columns: BoardColumn[];
  savedPipelines: PipelineConfigSummary[] | undefined;
  assignedPipelineId: string | null | undefined;
  isAssigning: boolean;
  onSelectPipeline: (pipelineId: string) => void;
}

export function PipelineStagesSection({
  columns,
  savedPipelines,
  assignedPipelineId,
  isAssigning,
  onSelectPipeline,
}: PipelineStagesSectionProps) {
  const assignedPipeline = useMemo(
    () => savedPipelines?.find((p) => p.id === (assignedPipelineId ?? '')) ?? null,
    [assignedPipelineId, savedPipelines],
  );

  const assignedStageMap = useMemo(
    () => new Map((assignedPipeline?.stages ?? []).map((stage: PipelineStage) => [stage.name.toLowerCase(), stage])),
    [assignedPipeline],
  );

  const pipelineColumnCount = Math.max(columns.length, 1);
  const pipelineGridStyle: CSSProperties = useMemo(
    () => ({ gridTemplateColumns: `repeat(${pipelineColumnCount}, minmax(min(14rem, 85vw), 1fr))` }),
    [pipelineColumnCount],
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
                <PipelineSelector
                  assignedPipelineId={assignedPipelineId}
                  savedPipelines={savedPipelines}
                  isAssigning={isAssigning}
                  onSelect={onSelectPipeline}
                />
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
                    aria-hidden="true"
                  />
                  <span className="text-sm font-medium">{col.status.name}</span>
                  <span className="text-xs text-muted-foreground">{col.item_count} items</span>
                  {assigned.length > 0 ? (
                    <div className="mt-1 flex flex-wrap justify-center gap-1">
                      {assigned.map((assignment) => (
                        <span
                          key={assignment.id}
                          className="solar-chip rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]"
                        >
                          {formatAgentName(assignment.agent_slug, assignment.agent_display_name)}
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
