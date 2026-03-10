/**
 * ParallelStageGroup — visual wrapper for agents running in parallel within a single stage.
 * Renders a shared container with distinct styling and a "Runs in Parallel" label.
 */

import { GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ParallelStageGroupProps {
  children: React.ReactNode;
  isParallel: boolean;
}

export function ParallelStageGroup({ children, isParallel }: ParallelStageGroupProps) {
  return (
    <div
      className={cn(
        'rounded-xl border p-2',
        isParallel
          ? 'border-primary/25 bg-primary/[0.07] shadow-[0_0_0_1px_hsl(var(--primary)/0.04),0_18px_40px_-28px_hsl(var(--glow)/0.6)]'
          : 'border-border/50 bg-background/18'
      )}
    >
      {isParallel && (
        <p className="mb-2 flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <GitBranch className="h-3.5 w-3.5 text-primary" />
          All agents in this stage start together, then the pipeline waits for every one to finish
          before moving on.
        </p>
      )}
      {children}
    </div>
  );
}
