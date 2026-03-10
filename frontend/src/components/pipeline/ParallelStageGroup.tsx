/**
 * ParallelStageGroup — visual container for agents executing in parallel
 * within a single pipeline stage. Renders a distinct border, label, and
 * descriptive text to differentiate parallel stages from sequential ones.
 */

import { GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ParallelStageGroupProps {
  children: React.ReactNode;
  className?: string;
}

export function ParallelStageGroup({ children, className }: ParallelStageGroupProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-primary/25 bg-primary/[0.07] p-2 shadow-[0_0_0_1px_hsl(var(--primary)/0.04),0_18px_40px_-28px_hsl(var(--glow)/0.6)]',
        className
      )}
    >
      <p className="mb-2 flex items-center gap-1.5 text-[11px] text-muted-foreground">
        <GitBranch className="h-3.5 w-3.5 text-primary" />
        All agents in this stage start together, then the pipeline waits for every one to finish
        before moving on.
      </p>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(14rem,1fr))] gap-2">{children}</div>
    </div>
  );
}
