/**
 * Task card component for displaying tasks in sidebar.
 */

import type { Task } from '@/types';

interface TaskCardProps {
  task: Task;
  onClick?: () => void;
  isHighlighted?: boolean;
}

export function TaskCard({ task, onClick, isHighlighted }: TaskCardProps) {
  const cardClasses = [
    'task-card',
    isHighlighted ? 'task-card--highlighted' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={cardClasses} onClick={onClick} role="button" tabIndex={0}>
      <div className="task-header">
        <span className={`status-badge status-${task.status.toLowerCase().replace(/\s+/g, '-')}`}>
          {task.status}
        </span>
      </div>
      <h4 className="task-title">{task.title}</h4>
      {task.description && (
        <p className="task-description">{truncateDescription(task.description)}</p>
      )}
    </div>
  );
}

function truncateDescription(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
}
