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
      <div className="flex flex-col gap-2">
        <label htmlFor="display-theme" className="text-sm font-medium text-foreground">Theme</label>
        <select
          id="display-theme"
          className="flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={localState.theme}
          onChange={(e) => setField('theme', e.target.value as ThemeModeType)}
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="display-view" className="text-sm font-medium text-foreground">Default View</label>
        <select
          id="display-view"
          className="flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={localState.default_view}
          onChange={(e) => setField('default_view', e.target.value as DefaultViewType)}
        >
          <option value="chat">Chat</option>
          <option value="board">Board</option>
          <option value="settings">Settings</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
          <input
            type="checkbox"
            className="w-4 h-4 rounded border-input text-primary focus:ring-primary"
            checked={localState.sidebar_collapsed}
            onChange={(e) => setField('sidebar_collapsed', e.target.checked)}
          />
          Sidebar collapsed by default
        </label>
      </div>
    </SettingsSection>
  );
}
