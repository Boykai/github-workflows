/**
 * PipelineEmptyState — Empty board state CTA for creating a new pipeline.
 *
 * Extracted from AgentsPipelinePage to keep the page ≤ 250 lines (FR-001).
 */

import { Tooltip } from '@/components/ui/tooltip';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';

interface PipelineEmptyStateProps {
  onCreatePipeline: () => void;
}

export function PipelineEmptyState({ onCreatePipeline }: PipelineEmptyStateProps) {
  return (
    <div className="celestial-panel flex flex-col items-center justify-center gap-3 rounded-[1.2rem] border border-dashed border-border/60 bg-background/24 p-8 text-center">
      <Tooltip contentKey="pipeline.board.createButton">
        <button
          type="button"
          onClick={onCreatePipeline}
          className="group relative mb-2 flex h-24 w-24 items-center justify-center rounded-full transition-transform duration-200 hover:scale-[1.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          aria-label="Create new pipeline"
        >
          <div className="absolute inset-0 rounded-full border border-border/40 bg-[radial-gradient(circle_at_center,hsl(var(--glow)/0.22)_0%,transparent_62%)] transition-colors duration-200 group-hover:border-primary/30 group-hover:bg-[radial-gradient(circle_at_center,hsl(var(--glow)/0.32)_0%,transparent_62%)]" />
          <div className="absolute inset-[10px] rounded-full border border-primary/18 transition-colors duration-200 group-hover:border-primary/35" />
          <span aria-hidden="true" className="absolute left-1/2 top-1.5 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-[hsl(var(--glow))] shadow-[0_0_12px_hsl(var(--glow)/0.8)]" />
          <span aria-hidden="true" className="absolute bottom-4 right-2 h-2.5 w-2.5 rounded-full bg-[hsl(var(--gold))] shadow-[0_0_18px_hsl(var(--gold)/0.45)]" />
          <span aria-hidden="true" className="absolute left-2 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-[hsl(var(--gold)/0.55)]" />
          <ThemedAgentIcon
            name="Pipeline constellation"
            iconName="constellation"
            size="lg"
            className="h-14 w-14 border-primary/30 shadow-[0_12px_30px_hsl(var(--night)/0.3)] transition-transform duration-200 group-hover:scale-105"
          />
        </button>
      </Tooltip>
      <h3 className="text-sm font-semibold text-foreground">Create new agent pipeline</h3>
      <p className="text-xs text-muted-foreground max-w-md">
        Build custom agent workflows by creating a pipeline with stages and agents. Click
        the constellation to get started.
      </p>
    </div>
  );
}
