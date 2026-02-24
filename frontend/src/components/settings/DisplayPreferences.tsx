/**
 * Display Preferences settings section.
 *
 * Allows user to configure theme, default view, and sidebar state.
 */

import { SettingsSection } from './SettingsSection';
import { useSettingsForm } from '@/hooks/useSettingsForm';
import type {
  DisplayPreferences as DisplayPreferencesType,
  ThemeModeType,
  DefaultViewType,
  UserPreferencesUpdate,
} from '@/types';

interface DisplayPreferencesProps {
  settings: DisplayPreferencesType;
  onSave: (update: UserPreferencesUpdate) => Promise<void>;
}

export function DisplayPreferences({ settings, onSave }: DisplayPreferencesProps) {
  const { localState, setField, isDirty } = useSettingsForm(settings);

  const handleSave = async () => {
    await onSave({
      display: { theme: localState.theme, default_view: localState.default_view, sidebar_collapsed: localState.sidebar_collapsed },
    });
  };

  return (
    <SettingsSection
      title="Display Preferences"
      description="Theme, default view, and sidebar configuration."
      isDirty={isDirty}
      onSave={handleSave}
    >
      <div className="settings-field">
        <label htmlFor="display-theme">Theme</label>
        <select
          id="display-theme"
          value={localState.theme}
          onChange={(e) => setField('theme', e.target.value as ThemeModeType)}
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>

      <div className="settings-field">
        <label htmlFor="display-view">Default View</label>
        <select
          id="display-view"
          value={localState.default_view}
          onChange={(e) => setField('default_view', e.target.value as DefaultViewType)}
        >
          <option value="chat">Chat</option>
          <option value="board">Board</option>
          <option value="settings">Settings</option>
        </select>
      </div>

      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={localState.sidebar_collapsed}
            onChange={(e) => setField('sidebar_collapsed', e.target.checked)}
          />
          Sidebar collapsed by default
        </label>
      </div>
    </SettingsSection>
  );
}
