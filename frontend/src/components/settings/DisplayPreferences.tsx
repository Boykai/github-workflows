/**
 * Display Preferences settings section.
 *
 * Allows user to configure theme, default view, and sidebar state.
 */

import { useState, useEffect } from 'react';
import { SettingsSection } from './SettingsSection';
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
  const [theme, setTheme] = useState<ThemeModeType>(settings.theme);
  const [defaultView, setDefaultView] = useState<DefaultViewType>(settings.default_view);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(settings.sidebar_collapsed);

  useEffect(() => {
    setTheme(settings.theme);
    setDefaultView(settings.default_view);
    setSidebarCollapsed(settings.sidebar_collapsed);
  }, [settings.theme, settings.default_view, settings.sidebar_collapsed]);

  const isDirty =
    theme !== settings.theme ||
    defaultView !== settings.default_view ||
    sidebarCollapsed !== settings.sidebar_collapsed;

  const handleSave = async () => {
    await onSave({
      display: { theme, default_view: defaultView, sidebar_collapsed: sidebarCollapsed },
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
          value={theme}
          onChange={(e) => setTheme(e.target.value as ThemeModeType)}
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>

      <div className="settings-field">
        <label htmlFor="display-view">Default View</label>
        <select
          id="display-view"
          value={defaultView}
          onChange={(e) => setDefaultView(e.target.value as DefaultViewType)}
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
            checked={sidebarCollapsed}
            onChange={(e) => setSidebarCollapsed(e.target.checked)}
          />
          Sidebar collapsed by default
        </label>
      </div>
    </SettingsSection>
  );
}
