/**
 * Inline warning banner shown in the chat area when no Agent Pipeline
 * is assigned to the current project.
 */

import { useSelectedPipeline } from '@/hooks/useSelectedPipeline';
import { AlertTriangle } from '@/lib/icons';

interface PipelineWarningBannerProps {
  projectId: string;
}

export function PipelineWarningBanner({ projectId }: PipelineWarningBannerProps) {
  const { hasAssignment, isLoading } = useSelectedPipeline(projectId);

  if (isLoading || hasAssignment) return null;

  return (
    <div
      role="alert"
      className="mx-4 mb-2 flex items-start gap-2 rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-xs dark:border-yellow-800 dark:bg-yellow-900/20"
    >
      <AlertTriangle
        className="mt-0.5 h-3.5 w-3.5 shrink-0 text-yellow-600 dark:text-yellow-400"
        aria-hidden="true"
      />
      <span className="text-yellow-800 dark:text-yellow-300">
        No Agent Pipeline selected — issues will use the default pipeline. Select one on the Project
        page.
      </span>
    </div>
  );
}
