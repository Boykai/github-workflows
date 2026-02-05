/**
 * Project sidebar component showing task board with real-time sync.
 */

import { useState, useEffect, useRef } from 'react';
import type { Project, Task } from '@/types';
import { ProjectSelector } from './ProjectSelector';
import { TaskCard } from './TaskCard';
import { useRealTimeSync } from '@/hooks/useRealTimeSync';

interface ProjectSidebarProps {
  projects: Project[];
  selectedProject: Project | null;
  tasks: Task[];
  isLoading: boolean;
  tasksLoading: boolean;
  onProjectSelect: (projectId: string) => void;
}

export function ProjectSidebar({
  projects,
  selectedProject,
  tasks,
  isLoading,
  tasksLoading,
  onProjectSelect,
}: ProjectSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [recentlyUpdated, setRecentlyUpdated] = useState<Set<string>>(new Set());
  const previousTasksRef = useRef<Task[]>([]);

  // Real-time sync status
  const { status: syncStatus, lastUpdate } = useRealTimeSync(
    selectedProject?.project_id ?? null
  );

  // Track task changes for highlighting
  useEffect(() => {
    const previousIds = new Set(previousTasksRef.current.map((t) => t.task_id));
    const newIds = new Set(tasks.map((t) => t.task_id));

    // Find new or changed tasks
    const updated = new Set<string>();
    for (const task of tasks) {
      const prevTask = previousTasksRef.current.find((t) => t.task_id === task.task_id);
      if (!previousIds.has(task.task_id) || (prevTask && prevTask.status !== task.status)) {
        updated.add(task.task_id);
      }
    }

    if (updated.size > 0) {
      setRecentlyUpdated(updated);
      // Clear highlight after animation
      const timer = setTimeout(() => setRecentlyUpdated(new Set()), 2000);
      return () => clearTimeout(timer);
    }

    previousTasksRef.current = tasks;
  }, [tasks]);

  // Group tasks by status
  const tasksByStatus = groupTasksByStatus(tasks, selectedProject?.status_columns ?? []);

  // Format last update time
  const formatLastUpdate = () => {
    if (!lastUpdate) return '';
    const now = new Date();
    const diff = Math.floor((now.getTime() - lastUpdate.getTime()) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return lastUpdate.toLocaleTimeString();
  };

  return (
    <aside className={`project-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <h2>Welcome to Tech Connect 2026 - Project Board</h2>
        <button
          className="collapse-button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? '→' : '←'}
        </button>
      </div>

      {!isCollapsed && (
        <>
          {/* Sync Status Indicator (T060) */}
          {selectedProject && (
            <div className={`sync-status sync-status--${syncStatus}`}>
              <span className="sync-indicator" />
              <span className="sync-label">
                {syncStatus === 'connected' && 'Live'}
                {syncStatus === 'connecting' && 'Connecting...'}
                {syncStatus === 'polling' && 'Polling mode'}
                {syncStatus === 'disconnected' && 'Offline'}
              </span>
              {lastUpdate && (
                <span className="sync-time">Updated {formatLastUpdate()}</span>
              )}
            </div>
          )}

          <ProjectSelector
            projects={projects}
            selectedProjectId={selectedProject?.project_id ?? null}
            onSelect={onProjectSelect}
            isLoading={isLoading}
          />

          {selectedProject && (
            <div className="board-container">
              {tasksLoading ? (
                <div className="loading-tasks">Loading tasks...</div>
              ) : tasks.length === 0 ? (
                <div className="empty-board">
                  <p>No tasks yet. Start by describing a task in the chat!</p>
                </div>
              ) : (
                <div className="status-columns">
                  {Object.entries(tasksByStatus).map(([status, statusTasks]) => (
                    <div key={status} className="status-column">
                      <h3 className="column-header">
                        {status}
                        <span className="task-count">{statusTasks.length}</span>
                      </h3>
                      <div className="task-list">
                        {statusTasks.map((task) => (
                          <TaskCard
                            key={task.task_id}
                            task={task}
                            isHighlighted={recentlyUpdated.has(task.task_id)}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {!selectedProject && !isLoading && (
            <div className="no-project-selected">
              <p>Select a project to view its board</p>
            </div>
          )}
        </>
      )}
    </aside>
  );
}

interface StatusColumn {
  name: string;
}

function groupTasksByStatus(
  tasks: Task[],
  statusColumns: StatusColumn[]
): Record<string, Task[]> {
  // Initialize with all status columns (in order)
  const columnNames = statusColumns.map((c) => c.name);
  const defaultStatuses = columnNames.length > 0 ? columnNames : ['Todo', 'In Progress', 'Done'];

  const grouped: Record<string, Task[]> = {};
  for (const status of defaultStatuses) {
    grouped[status] = [];
  }

  // Group tasks
  for (const task of tasks) {
    const status = task.status;
    if (grouped[status]) {
      grouped[status].push(task);
    } else {
      // Unknown status - add it
      grouped[status] = [task];
    }
  }

  // Sort tasks within each status: newest first (descending by created_at)
  for (const status in grouped) {
    grouped[status].sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return dateB - dateA; // Descending order (newest first)
    });
  }

  return grouped;
}
