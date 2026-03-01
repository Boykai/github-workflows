/**
 * TriggerHistoryLog — displays chronological trigger history for a housekeeping task.
 */

import { useState } from 'react';
import { useTaskHistory } from '@/hooks/useHousekeeping';

interface TriggerHistoryLogProps {
  taskId: string;
  taskName: string;
  onClose?: () => void;
}

export function TriggerHistoryLog({ taskId, taskName, onClose }: TriggerHistoryLogProps) {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const { data, isLoading, error } = useTaskHistory(taskId, 50, 0, statusFilter);

  const triggerTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      scheduled: 'bg-blue-100 text-blue-800',
      'count-based': 'bg-purple-100 text-purple-800',
      manual: 'bg-green-100 text-green-800',
    };
    return styles[type] ?? 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">History: {taskName}</h2>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter ?? ''}
            onChange={(e) => setStatusFilter(e.target.value || undefined)}
            className="border rounded px-2 py-1 text-sm"
            aria-label="Filter by status"
          >
            <option value="">All</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </select>
          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-1 border rounded text-sm hover:bg-accent"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {isLoading && <div className="p-4 text-muted-foreground">Loading history...</div>}
      {error && <div className="p-4 text-destructive">Error: {error.message}</div>}

      {data && data.history.length === 0 && (
        <div className="p-8 text-center text-muted-foreground">
          <p>No runs have occurred yet.</p>
        </div>
      )}

      {data && data.history.length > 0 && (
        <div className="space-y-2">
          {data.history.map((event) => (
            <div key={event.id} className="border rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${triggerTypeBadge(event.trigger_type)}`}
                  >
                    {event.trigger_type}
                  </span>
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${
                      event.status === 'success'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {event.status}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {new Date(event.timestamp).toLocaleString()}
                </span>
              </div>
              <div className="mt-1 text-sm">
                {event.issue_url ? (
                  <a
                    href={event.issue_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Issue #{event.issue_number}
                  </a>
                ) : (
                  <span className="text-muted-foreground">No issue created</span>
                )}
                {event.sub_issues_created > 0 && (
                  <span className="ml-2 text-xs text-muted-foreground">
                    ({event.sub_issues_created} sub-issues)
                  </span>
                )}
              </div>
              {event.error_details && (
                <div className="mt-1 text-xs text-destructive bg-destructive/10 p-2 rounded">
                  {event.error_details}
                </div>
              )}
            </div>
          ))}
          {data.total > data.history.length && (
            <div className="text-center text-xs text-muted-foreground py-2">
              Showing {data.history.length} of {data.total} entries
            </div>
          )}
        </div>
      )}
    </div>
  );
}
