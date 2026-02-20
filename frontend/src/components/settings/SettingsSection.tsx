/**
 * Reusable collapsible section wrapper for Settings page.
 *
 * Provides title, description, children slot, save button, and
 * loading/success/error states.
 */

import { useState, type ReactNode } from 'react';

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
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="settings-section">
      <button
        className="settings-section-header"
        onClick={() => setCollapsed((c) => !c)}
        type="button"
      >
        <span className={`settings-section-chevron ${collapsed ? 'collapsed' : ''}`}>
          ▼
        </span>
        <div className="settings-section-title-area">
          <h3 className="settings-section-title">{title}</h3>
          {description && (
            <p className="settings-section-description">{description}</p>
          )}
        </div>
      </button>

      {!collapsed && (
        <div className="settings-section-body">
          <div className="settings-section-content">{children}</div>

          {!hideSave && onSave && (
            <div className="settings-section-footer">
              <button
                className="settings-save-btn"
                onClick={handleSave}
                disabled={!isDirty || saving}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              {saveStatus === 'success' && (
                <span className="settings-save-status success">Saved!</span>
              )}
              {saveStatus === 'error' && (
                <span className="settings-save-status error">Failed to save</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
