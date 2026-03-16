/**
 * AppCard — displays a single application in the apps grid.
 * Shows name, description, status badge, and action buttons.
 */

import { Play, Square, Trash2 } from 'lucide-react';
import { Tooltip } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { App, AppStatus } from '@/types/apps';

const STATUS_STYLES: Record<AppStatus, { bg: string; text: string; label: string }> = {
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
  isStartPending?: boolean;
  isStopPending?: boolean;
  isDeletePending?: boolean;
}

export function AppCard({
  app,
  onSelect,
  onStart,
  onStop,
  onDelete,
  isStartPending = false,
  isStopPending = false,
  isDeletePending = false,
}: AppCardProps) {
  const style = STATUS_STYLES[app.status] ?? STATUS_STYLES.stopped;

  return (
    <div
      className="group relative flex cursor-pointer flex-col rounded-xl border border-zinc-200 p-5 text-left shadow-sm transition-all hover:shadow-md dark:border-zinc-700/60 dark:bg-zinc-900"
    >
      {/* Clickable card overlay — navigates to detail view */}
      <button
        type="button"
        className="absolute inset-0 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
        aria-label={`View app ${app.display_name}`}
        onClick={() => onSelect(app.name)}
      />
      {/* Header */}
      <div className="relative z-10 mb-2 flex items-center justify-between">
        <Tooltip content={app.display_name}>
          <h3 className="truncate text-base font-semibold text-zinc-900 dark:text-zinc-100">
            {app.display_name}
          </h3>
        </Tooltip>
        <span className={cn('shrink-0 rounded-full px-2 py-0.5 text-xs font-medium', style.bg, style.text)}>
          {style.label}
        </span>
      </div>

      {/* Description */}
      <Tooltip content={app.description || 'No description'}>
        <p className="relative z-10 mb-4 line-clamp-2 flex-1 text-sm text-zinc-500 dark:text-zinc-400">
          {app.description || 'No description'}
        </p>
      </Tooltip>

      {/* Actions — z-10 to sit above the card overlay button */}
      <div
        className="relative z-10 flex items-center gap-2"
        role="toolbar"
        aria-label={`Actions for ${app.display_name}`}
      >
        {app.status === 'stopped' && (
          <button
            type="button"
            aria-label={`Start app ${app.display_name}`}
            disabled={isStartPending}
            className="inline-flex items-center gap-1 rounded-md bg-emerald-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={() => onStart(app.name)}
          >
            <Play aria-hidden="true" className="h-3 w-3" /> Start
          </button>
        )}
        {app.status === 'active' && (
          <button
            type="button"
            aria-label={`Stop app ${app.display_name}`}
            disabled={isStopPending}
            className="inline-flex items-center gap-1 rounded-md bg-zinc-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={() => onStop(app.name)}
          >
            <Square aria-hidden="true" className="h-3 w-3" /> Stop
          </button>
        )}
        {app.status !== 'active' && (
          <button
            type="button"
            aria-label={`Delete app ${app.display_name}`}
            disabled={isDeletePending}
            className="inline-flex items-center gap-1 rounded-md bg-red-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={() => onDelete(app.name)}
          >
            <Trash2 aria-hidden="true" className="h-3 w-3" /> Delete
          </button>
        )}
      </div>
    </div>
  );
}
