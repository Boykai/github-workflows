/**
 * HousekeepingTaskForm — create/edit form for housekeeping tasks.
 */

import { useState, useEffect } from 'react';
import type { HousekeepingTask, HousekeepingTaskCreate, HousekeepingTaskUpdate } from '@/types';
import { useTemplateList, useCreateTask, useUpdateTask } from '@/hooks/useHousekeeping';

interface HousekeepingTaskFormProps {
  projectId: string;
  task?: HousekeepingTask | null;
  onClose: () => void;
}

export function HousekeepingTaskForm({ projectId, task, onClose }: HousekeepingTaskFormProps) {
  const { data: templateData } = useTemplateList();
  const createTask = useCreateTask();
  const updateTask = useUpdateTask();

  const [name, setName] = useState(task?.name ?? '');
  const [description, setDescription] = useState(task?.description ?? '');
  const [templateId, setTemplateId] = useState(task?.template_id ?? '');
  const [triggerType, setTriggerType] = useState<'time' | 'count'>(task?.trigger_type ?? 'time');
  const [triggerValue, setTriggerValue] = useState(task?.trigger_value ?? 'weekly');
  const [cooldownMinutes, setCooldownMinutes] = useState(task?.cooldown_minutes ?? 5);
  const [error, setError] = useState<string | null>(null);

  const templates = templateData?.templates;
  const isEditing = !!task;

  useEffect(() => {
    if (!templateId && templates && templates.length > 0) {
      setTemplateId(templates[0].id);
    }
  }, [templates, templateId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    if (!templateId) {
      setError('Template is required');
      return;
    }
    if (!triggerValue.trim()) {
      setError('Trigger value is required');
      return;
    }

    try {
      if (isEditing && task) {
        const data: HousekeepingTaskUpdate = {
          name,
          description: description || undefined,
          template_id: templateId,
          trigger_type: triggerType,
          trigger_value: triggerValue,
          cooldown_minutes: cooldownMinutes,
        };
        await updateTask.mutateAsync({ id: task.id, data });
      } else {
        const data: HousekeepingTaskCreate = {
          name,
          description: description || undefined,
          template_id: templateId,
          trigger_type: triggerType,
          trigger_value: triggerValue,
          cooldown_minutes: cooldownMinutes,
          project_id: projectId,
        };
        await createTask.mutateAsync(data);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save task');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4">
      <h2 className="text-lg font-semibold">{isEditing ? 'Edit Task' : 'Create Task'}</h2>

      {error && <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">{error}</div>}

      <div>
        <label htmlFor="task-name" className="block text-sm font-medium mb-1">Name</label>
        <input
          id="task-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full border rounded px-3 py-2 text-sm"
          maxLength={200}
          required
        />
      </div>

      <div>
        <label htmlFor="task-desc" className="block text-sm font-medium mb-1">Description</label>
        <textarea
          id="task-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full border rounded px-3 py-2 text-sm"
          maxLength={1000}
          rows={2}
        />
      </div>

      <div>
        <label htmlFor="task-template" className="block text-sm font-medium mb-1">Template</label>
        <select
          id="task-template"
          value={templateId}
          onChange={(e) => setTemplateId(e.target.value)}
          className="w-full border rounded px-3 py-2 text-sm"
          required
        >
          <option value="">Select a template...</option>
          {(templates ?? []).map((t) => (
            <option key={t.id} value={t.id}>
              {t.name} {t.category === 'built-in' ? '(Built-in)' : ''}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Trigger Type</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-1.5 text-sm">
            <input
              type="radio"
              name="triggerType"
              value="time"
              checked={triggerType === 'time'}
              onChange={() => {
                setTriggerType('time');
                setTriggerValue('weekly');
              }}
            />
            Time-based
          </label>
          <label className="flex items-center gap-1.5 text-sm">
            <input
              type="radio"
              name="triggerType"
              value="count"
              checked={triggerType === 'count'}
              onChange={() => {
                setTriggerType('count');
                setTriggerValue('10');
              }}
            />
            Count-based
          </label>
        </div>
      </div>

      <div>
        <label htmlFor="trigger-value" className="block text-sm font-medium mb-1">
          {triggerType === 'time' ? 'Schedule' : 'Issue Count Threshold'}
        </label>
        {triggerType === 'time' ? (
          <select
            id="trigger-value"
            value={triggerValue}
            onChange={(e) => setTriggerValue(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        ) : (
          <input
            id="trigger-value"
            type="number"
            min={1}
            value={triggerValue}
            onChange={(e) => setTriggerValue(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm"
            required
          />
        )}
      </div>

      <div>
        <label htmlFor="cooldown" className="block text-sm font-medium mb-1">
          Cooldown (minutes)
        </label>
        <input
          id="cooldown"
          type="number"
          min={1}
          value={cooldownMinutes}
          onChange={(e) => setCooldownMinutes(parseInt(e.target.value, 10) || 5)}
          className="w-full border rounded px-3 py-2 text-sm"
        />
      </div>

      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          disabled={createTask.isPending || updateTask.isPending}
          className="px-4 py-2 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90 disabled:opacity-50"
        >
          {createTask.isPending || updateTask.isPending
            ? 'Saving...'
            : isEditing
              ? 'Update Task'
              : 'Create Task'}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 border rounded text-sm hover:bg-accent"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
