/**
 * Reusable collapsible section wrapper for Settings page.
 *
 * Provides title, description, children slot, save button, and
 * loading/success/error states.
 */

import { useState, type ReactNode } from 'react';
import { TOAST_SUCCESS_MS, TOAST_ERROR_MS } from '@/constants';

interface SettingsSectionProps {
  title: string;
  description?: string;
  children: ReactNode;
  /** Whether the section content has been modified */
  isDirty?: boolean;
  /** Async save handler — returns on completion */
  onSave?: () => Promise<void>;
  /** If true, section is collapsed by default */
  defaultCollapsed?: boolean;
  /** If true, hide the save button (e.g. read-only sections or auto-save) */
  hideSave?: boolean;
}

export function SettingsSection({
  title,
  description,
  children,
  isDirty = false,
  onSave,
  defaultCollapsed = false,
  hideSave = false,
}: SettingsSectionProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleSave = async () => {
    if (!onSave) return;
    setSaving(true);
    setSaveStatus('idle');
    try {
      await onSave();
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), TOAST_SUCCESS_MS);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), TOAST_ERROR_MS);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col bg-card rounded-lg border border-border shadow-sm overflow-hidden">
      <button
        className="flex items-start gap-3 p-5 w-full text-left bg-transparent hover:bg-muted/50 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary"
        onClick={() => setCollapsed((c) => !c)}
        type="button"
      >
        <span className={`text-xs text-muted-foreground mt-1.5 transition-transform duration-200 ${collapsed ? '-rotate-90' : ''}`}>
          ▼
        </span>
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
      </button>

      {!collapsed && (
        <div className="flex flex-col border-t border-border">
          <div className="p-5 flex flex-col gap-6">{children}</div>

          {!hideSave && onSave && (
            <div className="flex items-center gap-4 p-5 pt-0">
              <button
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleSave}
                disabled={!isDirty || saving}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              {saveStatus === 'success' && (
                <span className="text-sm font-medium text-green-500">Saved!</span>
              )}
              {saveStatus === 'error' && (
                <span className="text-sm font-medium text-destructive">Failed to save</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
