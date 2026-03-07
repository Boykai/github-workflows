/**
 * SavedWorkflowsList — displays saved pipeline configurations as cards.
 * Shows pipeline name, last modified date, stage/agent count.
 */

import { Clock, Layers, Bot, Workflow } from 'lucide-react';
import type { PipelineConfigSummary } from '@/types';

interface SavedWorkflowsListProps {
  pipelines: PipelineConfigSummary[];
  activePipelineId: string | null;
  isLoading: boolean;
  onSelect: (pipelineId: string) => void;
}

function formatRelativeDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60_000);
    const diffHours = Math.floor(diffMs / 3_600_000);
    const diffDays = Math.floor(diffMs / 86_400_000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  } catch {
    return dateStr;
  }
}

export function SavedWorkflowsList({
  pipelines,
  activePipelineId,
  isLoading,
  onSelect,
}: SavedWorkflowsListProps) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        <Workflow className="h-5 w-5 text-primary/70" />
        Saved Workflows
      </h3>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-24 rounded-xl border border-border/50 bg-muted/20 animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && pipelines.length === 0 && (
        <div className="celestial-panel flex flex-col items-center gap-2 rounded-[1.2rem] border border-dashed border-border/60 p-6 text-center">
          <Workflow className="h-6 w-6 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">
            No saved pipelines yet. Create your first pipeline above!
          </p>
        </div>
      )}

      {/* Pipeline cards */}
      {!isLoading && pipelines.length > 0 && (
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {pipelines.map((pipeline) => {
            const isActive = pipeline.id === activePipelineId;
            return (
              <button
                key={pipeline.id}
                type="button"
                onClick={() => onSelect(pipeline.id)}
                className={`flex flex-col gap-2 rounded-xl border p-4 text-left transition-all hover:shadow-md ${
                  isActive
                    ? 'border-primary/50 bg-primary/5 ring-1 ring-primary/20 shadow-sm'
                    : 'border-border/60 bg-card/70 hover:border-primary/30'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-semibold text-foreground truncate">
                    {pipeline.name}
                  </h4>
                  {isActive && (
                    <span className="shrink-0 rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-medium text-primary">
                      Active
                    </span>
                  )}
                </div>

                {pipeline.description && (
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {pipeline.description}
                  </p>
                )}

                <div className="flex items-center gap-3 mt-auto text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Layers className="h-3 w-3" />
                    {pipeline.stage_count} stage{pipeline.stage_count !== 1 ? 's' : ''}
                  </span>
                  <span className="flex items-center gap-1">
                    <Bot className="h-3 w-3" />
                    {pipeline.agent_count} agent{pipeline.agent_count !== 1 ? 's' : ''}
                  </span>
                  <span className="flex items-center gap-1 ml-auto">
                    <Clock className="h-3 w-3" />
                    {formatRelativeDate(pipeline.updated_at)}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
