/**
 * TemplateLibrary — manage reusable issue templates.
 */

import { useState } from 'react';
import type { IssueTemplate } from '@/types';
import {
  useTemplateList,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useDuplicateTemplate,
} from '@/hooks/useHousekeeping';

export function TemplateLibrary() {
  const { data, isLoading, error } = useTemplateList();
  const createTemplate = useCreateTemplate();
  const updateTemplate = useUpdateTemplate();
  const deleteTemplate = useDeleteTemplate();
  const duplicateTemplate = useDuplicateTemplate();

  const [editing, setEditing] = useState<IssueTemplate | null>(null);
  const [creating, setCreating] = useState(false);
  const [formName, setFormName] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formBody, setFormBody] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  if (isLoading) return <div className="p-4 text-muted-foreground">Loading templates...</div>;
  if (error) return <div className="p-4 text-destructive">Error: {error.message}</div>;

  const templates = data?.templates ?? [];

  const resetForm = () => {
    setEditing(null);
    setCreating(false);
    setFormName('');
    setFormTitle('');
    setFormBody('');
    setFormError(null);
  };

  const startEdit = (tmpl: IssueTemplate) => {
    setEditing(tmpl);
    setCreating(false);
    setFormName(tmpl.name);
    setFormTitle(tmpl.title_pattern);
    setFormBody(tmpl.body_content);
    setFormError(null);
  };

  const startCreate = () => {
    setEditing(null);
    setCreating(true);
    setFormName('');
    setFormTitle('📋 {task_name} – {date}');
    setFormBody('');
    setFormError(null);
  };

  const handleSave = async () => {
    setFormError(null);
    if (!formName.trim() || !formTitle.trim() || !formBody.trim()) {
      setFormError('All fields are required');
      return;
    }

    try {
      if (editing) {
        await updateTemplate.mutateAsync({
          id: editing.id,
          data: { name: formName, title_pattern: formTitle, body_content: formBody },
        });
      } else {
        await createTemplate.mutateAsync({
          name: formName,
          title_pattern: formTitle,
          body_content: formBody,
        });
      }
      resetForm();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to save');
    }
  };

  const handleDelete = async (tmpl: IssueTemplate) => {
    if (!confirm(`Delete template "${tmpl.name}"?`)) return;
    try {
      await deleteTemplate.mutateAsync({ id: tmpl.id });
    } catch {
      // Error handled by mutation
    }
  };

  const handleDuplicate = async (tmpl: IssueTemplate) => {
    await duplicateTemplate.mutateAsync(tmpl.id);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Issue Templates</h2>
        <button
          onClick={startCreate}
          className="px-3 py-1.5 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90"
        >
          + New Template
        </button>
      </div>

      {(creating || editing) && (
        <div className="border rounded-lg p-4 space-y-3 bg-card">
          <h3 className="font-medium">{editing ? 'Edit Template' : 'New Template'}</h3>
          {formError && (
            <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">{formError}</div>
          )}
          <div>
            <label htmlFor="tmpl-name" className="block text-sm font-medium mb-1">Name</label>
            <input
              id="tmpl-name"
              type="text"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              maxLength={200}
            />
          </div>
          <div>
            <label htmlFor="tmpl-title" className="block text-sm font-medium mb-1">Title Pattern</label>
            <input
              id="tmpl-title"
              type="text"
              value={formTitle}
              onChange={(e) => setFormTitle(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              placeholder="e.g., 📋 {task_name} – {date}"
            />
          </div>
          <div>
            <label htmlFor="tmpl-body" className="block text-sm font-medium mb-1">Body Content (Markdown)</label>
            <textarea
              id="tmpl-body"
              value={formBody}
              onChange={(e) => setFormBody(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm font-mono"
              rows={6}
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={createTemplate.isPending || updateTemplate.isPending}
              className="px-4 py-2 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90 disabled:opacity-50"
            >
              {createTemplate.isPending || updateTemplate.isPending ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={resetForm}
              className="px-4 py-2 border rounded text-sm hover:bg-accent"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {templates.map((tmpl) => (
          <div key={tmpl.id} className="border rounded-lg p-3 flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{tmpl.name}</span>
                {tmpl.category === 'built-in' && (
                  <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                    Built-in
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">{tmpl.title_pattern}</p>
            </div>
            <div className="flex items-center gap-1 ml-2">
              <button
                onClick={() => handleDuplicate(tmpl)}
                className="text-xs px-2 py-1 rounded hover:bg-accent"
                title="Duplicate"
              >
                📄
              </button>
              {tmpl.category !== 'built-in' && (
                <>
                  <button
                    onClick={() => startEdit(tmpl)}
                    className="text-xs px-2 py-1 rounded hover:bg-accent"
                    title="Edit"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={() => handleDelete(tmpl)}
                    className="text-xs px-2 py-1 rounded hover:bg-destructive/10 text-destructive"
                    title="Delete"
                  >
                    🗑
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
