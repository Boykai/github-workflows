/**
 * Preferences Tab component.
 *
 * Consolidates Display, Workflow, Notification, and Signal settings
 * into card-grouped sections with per-section save buttons.
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
      <DisplayPreferences settings={userSettings.display} onSave={onUserSave} />
      <WorkflowDefaults settings={userSettings.workflow} onSave={onUserSave} />
      <NotificationPreferences settings={userSettings.notifications} onSave={onUserSave} />
      <SignalConnection />
    </div>
  );
}
