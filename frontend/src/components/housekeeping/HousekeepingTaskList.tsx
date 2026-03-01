/**
 * HousekeepingTaskList — displays housekeeping tasks with status, trigger info, and controls.
 */

import { useState } from 'react';
import type { HousekeepingTask } from '@/types';
import { useTaskList, useDeleteTask, useToggleTask } from '@/hooks/useHousekeeping';

interface HousekeepingTaskListProps {
  projectId: string;
  onEditTask?: (task: HousekeepingTask) => void;
  onViewHistory?: (task: HousekeepingTask) => void;
  onRunNow?: (task: HousekeepingTask) => void;
}

export function HousekeepingTaskList({
  projectId,
  onEditTask,
  onViewHistory,
  onRunNow,
}: HousekeepingTaskListProps) {
  const { data, isLoading, error } = useTaskList(projectId);
  const deleteTask = useDeleteTask();
  const toggleTask = useToggleTask();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  if (isLoading) return <div className="p-4 text-muted-foreground">Loading tasks...</div>;
  if (error) return <div className="p-4 text-destructive">Error loading tasks: {error.message}</div>;

  const tasks = data?.tasks ?? [];

  if (tasks.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <p className="text-lg">No housekeeping tasks configured</p>
        <p className="text-sm mt-1">Create a task to automate recurring maintenance.</p>
      </div>
    );
  }

  const handleDelete = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this task and its history?')) return;
    setDeletingId(taskId);
    try {
      await deleteTask.mutateAsync(taskId);
    } finally {
      setDeletingId(null);
    }
  };

  const handleToggle = (task: HousekeepingTask) => {
    toggleTask.mutate({ id: task.id, enabled: !task.enabled });
  };

  const formatTrigger = (task: HousekeepingTask) => {
    if (task.trigger_type === 'time') {
      const presets: Record<string, string> = {
        daily: 'Daily',
        weekly: 'Weekly',
        monthly: 'Monthly',
      };
      return presets[task.trigger_value.toLowerCase()] || `Cron: ${task.trigger_value}`;
    }
    return `Every ${task.trigger_value} issues`;
  };

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div
          key={task.id}
          className={`border rounded-lg p-4 ${task.enabled ? 'bg-card' : 'bg-muted opacity-75'}`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-medium">{task.name}</h3>
                {!task.enabled && (
                  <span className="text-xs px-2 py-0.5 rounded bg-yellow-100 text-yellow-800">
                    Paused
                  </span>
                )}
              </div>
              {task.description && (
                <p className="text-sm text-muted-foreground mt-1">{task.description}</p>
              )}
              <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                <span>Trigger: {formatTrigger(task)}</span>
                {task.template_name && <span>Template: {task.template_name}</span>}
                {task.last_triggered_at && (
                  <span>Last run: {new Date(task.last_triggered_at).toLocaleString()}</span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1 ml-4">
              <button
                onClick={() => handleToggle(task)}
                className="text-xs px-2 py-1 rounded hover:bg-accent"
                title={task.enabled ? 'Pause' : 'Resume'}
              >
                {task.enabled ? '⏸' : '▶️'}
              </button>
              {onRunNow && (
                <button
                  onClick={() => onRunNow(task)}
                  className="text-xs px-2 py-1 rounded hover:bg-accent"
                  title="Run Now"
                >
                  🚀
                </button>
              )}
              {onViewHistory && (
                <button
                  onClick={() => onViewHistory(task)}
                  className="text-xs px-2 py-1 rounded hover:bg-accent"
                  title="View History"
                >
                  📋
                </button>
              )}
              {onEditTask && (
                <button
                  onClick={() => onEditTask(task)}
                  className="text-xs px-2 py-1 rounded hover:bg-accent"
                  title="Edit"
                >
                  ✏️
                </button>
              )}
              <button
                onClick={() => handleDelete(task.id)}
                disabled={deletingId === task.id}
                className="text-xs px-2 py-1 rounded hover:bg-destructive/10 text-destructive"
                title="Delete"
              >
                {deletingId === task.id ? '...' : '🗑'}
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
