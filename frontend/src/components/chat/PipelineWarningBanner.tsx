/**
 * Inline warning banner shown in the chat area when no Agent Pipeline
 * is assigned to the current project.
 */

import { useSelectedPipeline } from '@/hooks/useSelectedPipeline';
import { AlertTriangle } from 'lucide-react';

interface PipelineWarningBannerProps {
  projectId: string;
}

export function PipelineWarningBanner({ projectId }: PipelineWarningBannerProps) {
  const { hasAssignment, isLoading } = useSelectedPipeline(projectId);

  if (isLoading || hasAssignment) return null;

  return (
    <div
      role="alert"
      className="mx-4 mb-2 flex items-start gap-2 rounded-lg border border-gold/30 bg-gold/8 p-3 text-xs"
    >
      <AlertTriangle
        className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary"
        aria-hidden="true"
      />
      <span className="text-primary">
        No Agent Pipeline selected — issues will use the default pipeline. Select one on the Project
        page.
      </span>
    </div>
  );
}
