/**
 * Preferences Tab component.
 *
 * Consolidates user preference settings into a single tab:
 * - Display Preferences (theme, default view, sidebar)
 * - Workflow Defaults (default repo, assignee, polling interval)
 * - Notification Preferences (per-event toggles)
 * - Signal Connection (messaging integration)
 */

import { DisplayPreferences } from './DisplayPreferences';
import { WorkflowDefaults } from './WorkflowDefaults';
import { NotificationPreferences } from './NotificationPreferences';
import { SignalConnection } from './SignalConnection';
import type { EffectiveUserSettings, UserPreferencesUpdate } from '@/types';

interface PreferencesTabProps {
  userSettings: EffectiveUserSettings;
  onUserSave: (update: UserPreferencesUpdate) => Promise<void>;
}

export function PreferencesTab({ userSettings, onUserSave }: PreferencesTabProps) {
  return (
    <div className="flex flex-col gap-8">
      {/* Display Preferences */}
      <section aria-label="Display Preferences">
        <DisplayPreferences settings={userSettings.display} onSave={onUserSave} />
      </section>

      {/* Workflow Defaults */}
      <section aria-label="Workflow Defaults">
        <WorkflowDefaults settings={userSettings.workflow} onSave={onUserSave} />
      </section>

      {/* Notification Preferences */}
      <section aria-label="Notification Preferences">
        <NotificationPreferences settings={userSettings.notifications} onSave={onUserSave} />
      </section>

      {/* Signal Connection */}
      <section aria-label="Signal Connection">
        <SignalConnection />
      </section>
    </div>
  );
}
