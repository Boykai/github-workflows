/**
 * Reusable collapsible section wrapper for Settings page.
 *
 * Provides title, description, children slot, save button, and
 * loading/success/error states.
 */

import { useState, useId, type ReactNode } from 'react';
import { TOAST_SUCCESS_MS, TOAST_ERROR_MS } from '@/constants';
import { isRateLimitApiError } from '@/utils/rateLimit';
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
  const contentId = useId();
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error' | 'rate-limit'>('idle');

  const handleSave = async () => {
    if (!onSave) return;
    setSaving(true);
    setSaveStatus('idle');
    try {
      await onSave();
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), TOAST_SUCCESS_MS);
    } catch (err: unknown) {
      if (isRateLimitApiError(err)) {
        setSaveStatus('rate-limit');
      } else {
        setSaveStatus('error');
      }
      setTimeout(() => setSaveStatus('idle'), TOAST_ERROR_MS);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="celestial-panel flex flex-col rounded-[1.25rem] border border-border/80 shadow-sm overflow-hidden">
      <button
        className="flex w-full items-start gap-3 bg-transparent p-5 text-left transition-colors hover:bg-background/28 celestial-focus focus-visible:outline-none"
        onClick={() => setCollapsed((c) => !c)}
        type="button"
        aria-expanded={!collapsed}
        aria-controls={contentId}
        aria-label={collapsed ? `Expand ${title}` : `Collapse ${title}`}
      >
        <span
          aria-hidden="true"
          className={cn('text-xs text-muted-foreground mt-1.5 transition-transform duration-200', collapsed ? '-rotate-90' : '')}
        >
          ▼
        </span>
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
      </button>

      {!collapsed && (
        <div id={contentId} className="flex flex-col border-t border-border">
          <div className="p-5 flex flex-col gap-6">{children}</div>

          {!hideSave && onSave && (
            <div className="flex items-center gap-4 p-5 pt-0">
              <button
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-full hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed celestial-focus focus-visible:outline-none"
                onClick={handleSave}
                disabled={!isDirty || saving}
              >
                {saving ? 'Saving…' : 'Save Settings'}
              </button>
              {saveStatus === 'success' && (
                <span role="status" className="text-sm font-medium text-green-700 dark:text-green-400">
                  Saved!
                </span>
              )}
              {saveStatus === 'error' && (
                <span role="alert" className="text-sm font-medium text-destructive">
                  Could not save settings. Please try again.
                </span>
              )}
              {saveStatus === 'rate-limit' && (
                <span role="alert" className="text-sm font-medium text-destructive">
                  Too many requests. Please wait a moment and try again.
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
