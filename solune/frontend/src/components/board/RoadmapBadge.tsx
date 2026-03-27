/**
 * Compact badge reflecting live roadmap state.
 *
 * Displays near the queue mode toggle on the board page:
 * - "Active" when roadmap items are in the pipeline
 * - "Idle" when roadmap is enabled but no generation in progress
 * - "Generating…" during an active generation cycle
 * - Hidden when roadmap_enabled is false
 */

interface RoadmapBadgeProps {
  enabled: boolean;
  isGenerating?: boolean;
  hasActiveItems?: boolean;
}

export function RoadmapBadge({ enabled, isGenerating, hasActiveItems }: RoadmapBadgeProps) {
  if (!enabled) return null;

  let label: string;
  let colorClass: string;

  if (isGenerating) {
    label = 'Generating…';
    colorClass = 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300';
  } else if (hasActiveItems) {
    label = 'Active';
    colorClass = 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
  } else {
    label = 'Idle';
    colorClass = 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400';
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}
      aria-label={`Roadmap status: ${label}`}
    >
      🗺️ {label}
    </span>
  );
}
