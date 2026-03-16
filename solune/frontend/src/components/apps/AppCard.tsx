/**
 * AppCard — displays a single application in the apps grid.
 * Shows name, description, status badge, and action buttons.
 */

import { Play, Square, Trash2 } from 'lucide-react';
import type { App } from '@/types/apps';
import { useConfirmation } from '@/hooks/useConfirmation';

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  creating: {
    bg: 'bg-blue-100/90 dark:bg-blue-950/50',
    text: 'text-blue-700 dark:text-blue-300',
    label: 'Creating',
  },
  active: {
    bg: 'bg-emerald-100/90 dark:bg-emerald-950/50',
    text: 'text-emerald-700 dark:text-emerald-300',
    label: 'Active',
  },
  stopped: {
    bg: 'bg-zinc-100/90 dark:bg-zinc-800/50',
    text: 'text-zinc-600 dark:text-zinc-400',
    label: 'Stopped',
  },
  error: {
    bg: 'bg-red-100/90 dark:bg-red-950/50',
    text: 'text-red-700 dark:text-red-300',
    label: 'Error',
  },
};

interface AppCardProps {
  app: App;
  onSelect: (name: string) => void;
  onStart: (name: string) => void;
  onStop: (name: string) => void;
  onDelete: (name: string) => void;
}

export function AppCard({ app, onSelect, onStart, onStop, onDelete }: AppCardProps) {
  const style = STATUS_STYLES[app.status] ?? STATUS_STYLES.stopped;
  const { confirm } = useConfirmation();

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const confirmed = await confirm({
      title: 'Delete App',
      description: `Are you sure you want to delete "${app.display_name}"? This action cannot be undone.`,
      confirmLabel: 'Delete',
      variant: 'danger',
    });
    if (confirmed) {
      onDelete(app.name);
    }
  };

  return (
    <button
      type="button"
      className="group relative flex flex-col rounded-xl border border-zinc-200 bg-white p-5 text-left shadow-sm transition-all hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-700/60 dark:bg-zinc-900"
      onClick={() => onSelect(app.name)}
    >
      {/* Header */}
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
          {app.display_name}
        </h3>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}>
          {style.label}
        </span>
      </div>

      {/* Description */}
      <p className="mb-4 line-clamp-2 flex-1 text-sm text-zinc-500 dark:text-zinc-400">
        {app.description || 'No description'}
      </p>

      {/* Actions (stop event propagation so card click doesn't fire) */}
      <div
        className="flex items-center gap-2"
        role="toolbar"
        aria-label={`Actions for ${app.display_name}`}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        {app.status === 'stopped' && (
          <button
            type="button"
            aria-label={`Start ${app.display_name}`}
            className="inline-flex items-center gap-1 rounded-md bg-emerald-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-1"
            onClick={(e) => { e.stopPropagation(); onStart(app.name); }}
          >
            <Play className="h-3 w-3" aria-hidden="true" /> Start
          </button>
        )}
        {app.status === 'active' && (
          <button
            type="button"
            aria-label={`Stop ${app.display_name}`}
            className="inline-flex items-center gap-1 rounded-md bg-zinc-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500 focus-visible:ring-offset-1"
            onClick={(e) => { e.stopPropagation(); onStop(app.name); }}
          >
            <Square className="h-3 w-3" aria-hidden="true" /> Stop
          </button>
        )}
        {app.status !== 'active' && (
          <button
            type="button"
            aria-label={`Delete ${app.display_name}`}
            className="inline-flex items-center gap-1 rounded-md bg-red-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-1"
            onClick={handleDelete}
          >
            <Trash2 className="h-3 w-3" aria-hidden="true" /> Delete
          </button>
        )}
      </div>
    </button>
  );
}
