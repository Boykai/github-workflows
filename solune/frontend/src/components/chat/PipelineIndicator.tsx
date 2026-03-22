/**
 * PipelineIndicator component — badge near the submit button showing the active pipeline.
 */

import { AlertTriangle, Info } from '@/lib/icons';
import { cn } from '@/lib/utils';

interface PipelineIndicatorProps {
  activePipelineName: string | null;
  hasMultipleMentions: boolean;
  hasInvalidMentions: boolean;
}

export function PipelineIndicator({
  activePipelineName,
  hasMultipleMentions,
  hasInvalidMentions,
}: PipelineIndicatorProps) {
  // Hidden when no @mention tokens exist
  if (!activePipelineName && !hasInvalidMentions) return null;

  // Warning: only invalid mentions, no valid pipeline
  if (!activePipelineName && hasInvalidMentions) {
    return (
      <div className="flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
        <AlertTriangle className="h-3 w-3 shrink-0" />
        Pipeline not found
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex items-center gap-1 px-2 py-1 text-xs rounded-md',
        'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
      )}
      title={hasMultipleMentions ? 'Multiple pipelines mentioned — using last' : undefined}
    >
      {hasMultipleMentions && <Info className="h-3 w-3 shrink-0" />}
      Using pipeline: {activePipelineName}
    </div>
  );
}
