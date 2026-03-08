/**
 * MentionToken component — styled chip/tag for a resolved @mention inline in the input.
 * Renders as a non-editable span with data attributes for DOM-based pipeline ID extraction.
 */

import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MentionTokenProps {
  pipelineId: string;
  pipelineName: string;
  isValid: boolean;
}

export function MentionToken({ pipelineId, pipelineName, isValid }: MentionTokenProps) {
  return (
    <span
      contentEditable={false}
      data-pipeline-id={pipelineId}
      data-pipeline-name={pipelineName}
      data-mention-token=""
      className={cn(
        'inline-flex items-center gap-0.5 rounded px-1 py-0.5 text-xs font-medium align-baseline select-none',
        isValid
          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      )}
    >
      {!isValid && <AlertTriangle className="h-3 w-3 shrink-0" />}
      @{pipelineName}
    </span>
  );
}
