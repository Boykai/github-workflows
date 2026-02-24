/**
 * Notification Preferences settings section.
 *
 * Four toggle switches for per-event notification control.
 */

import { SettingsSection } from './SettingsSection';
import { useSettingsForm } from '@/hooks/useSettingsForm';
import type {
  NotificationPreferences as NotificationPreferencesType,
  UserPreferencesUpdate,
} from '@/types';

interface NotificationPreferencesProps {
  settings: NotificationPreferencesType;
  onSave: (update: UserPreferencesUpdate) => Promise<void>;
}

export function NotificationPreferences({ settings, onSave }: NotificationPreferencesProps) {
  const { localState, setField, isDirty } = useSettingsForm(settings);

  const handleSave = async () => {
    await onSave({
      notifications: {
        task_status_change: localState.task_status_change,
        agent_completion: localState.agent_completion,
        new_recommendation: localState.new_recommendation,
        chat_mention: localState.chat_mention,
      },
    });
  };

  return (
    <SettingsSection
      title="Notification Preferences"
      description="Control which events trigger notifications."
      isDirty={isDirty}
      onSave={handleSave}
    >
      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={localState.task_status_change}
            onChange={(e) => setField('task_status_change', e.target.checked)}
          />
          Task status changes
        </label>
      </div>

      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={localState.agent_completion}
            onChange={(e) => setField('agent_completion', e.target.checked)}
          />
          Agent completion
        </label>
      </div>

      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={localState.new_recommendation}
            onChange={(e) => setField('new_recommendation', e.target.checked)}
          />
          New recommendations
        </label>
      </div>

      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={localState.chat_mention}
            onChange={(e) => setField('chat_mention', e.target.checked)}
          />
          Chat mentions
        </label>
      </div>
    </SettingsSection>
  );
}
