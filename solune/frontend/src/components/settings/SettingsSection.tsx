/**
 * Reusable collapsible section wrapper for Settings page.
 *
 * Provides title, description, children slot, save button, and
 * loading/success/error states.
 */

import { useState, type ReactNode } from 'react';
import { TOAST_SUCCESS_MS, TOAST_ERROR_MS } from '@/constants';
import { cn } from '@/lib/utils';

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
  /** Optional error message to display (e.g. from mutation) */
  saveError?: string | null;
  /** Called when the user dismisses the error */
  onDismissError?: () => void;
}

export function SettingsSection({
  title,
  description,
  children,
  isDirty = false,
  onSave,
  defaultCollapsed = false,
  hideSave = false,
  saveError = null,
  onDismissError,
}: SettingsSectionProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSave = async () => {
    if (!onSave) return;
    setSaving(true);
    setSaveStatus('idle');
    setLocalError(null);
    try {
      await onSave();
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), TOAST_SUCCESS_MS);
    } catch {
      setSaveStatus('error');
      setLocalError('Could not save settings. Please try again.');
      setTimeout(() => {
        setSaveStatus('idle');
        setLocalError(null);
      }, TOAST_ERROR_MS);
    } finally {
      setSaving(false);
    }
  };

  const displayError = saveError ?? localError;

  return (
    <div className="celestial-panel flex flex-col rounded-[1.25rem] border border-border/80 shadow-sm overflow-hidden">
      <button
        className="flex w-full items-start gap-3 bg-transparent p-5 text-left transition-colors hover:bg-background/28 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary"
        onClick={() => setCollapsed((c) => !c)}
        type="button"
        aria-expanded={!collapsed}
      >
        <span
          className={cn('text-xs text-muted-foreground mt-1.5 transition-transform duration-200', collapsed ? '-rotate-90' : '')}
          aria-hidden="true"
        >
          ▼
        </span>
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
      </button>

      {!collapsed && (
        <div className="flex flex-col border-t border-border">
          <div className="p-5 flex flex-col gap-6">{children}</div>

          {!hideSave && onSave && (
            <div className="flex items-center gap-4 p-5 pt-0">
              <button
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-full hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleSave}
                disabled={!isDirty || saving}
              >
                {saving ? 'Saving…' : 'Save Settings'}
              </button>
              {saveStatus === 'success' && (
                <span className="text-sm font-medium text-green-700 dark:text-green-400" role="status">
                  Settings saved successfully.
                </span>
              )}
              {displayError && (
                <span className="text-sm font-medium text-destructive" role="alert">
                  {displayError}
                  {onDismissError && (
                    <button
                      className="ml-2 text-xs underline hover:no-underline"
                      onClick={onDismissError}
                      type="button"
                    >
                      Dismiss
                    </button>
                  )}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
