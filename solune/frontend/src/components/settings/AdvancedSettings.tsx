/**
 * Advanced Settings component.
 *
 * Collapsible wrapper containing secondary settings: Display Preferences,
 * Workflow Defaults, Notification Preferences, Project Settings, and
 * Global Settings. Collapsed by default to reduce visual noise.
 */

import { useState } from 'react';
import { DisplayPreferences } from './DisplayPreferences';
import { WorkflowDefaults } from './WorkflowDefaults';
import { NotificationPreferences } from './NotificationPreferences';
import { ProjectSettings } from './ProjectSettings';
import { GlobalSettings } from './GlobalSettings';
import { cn } from '@/lib/utils';
import type {
  EffectiveUserSettings,
  GlobalSettings as GlobalSettingsType,
  UserPreferencesUpdate,
  GlobalSettingsUpdate,
} from '@/types';

interface AdvancedSettingsProps {
  userSettings: EffectiveUserSettings;
  globalSettings: GlobalSettingsType | undefined;
  globalLoading: boolean;
  onUserSave: (update: UserPreferencesUpdate) => Promise<void>;
  onGlobalSave: (update: GlobalSettingsUpdate) => Promise<void>;
  projects?: Array<{ project_id: string; name: string }>;
  selectedProjectId?: string;
}

export function AdvancedSettings({
  userSettings,
  globalSettings,
  globalLoading,
  onUserSave,
  onGlobalSave,
  projects = [],
  selectedProjectId,
}: AdvancedSettingsProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="celestial-panel flex flex-col rounded-[1.25rem] border border-border/80 shadow-sm overflow-hidden">
      <button
        className="flex w-full items-center gap-3 bg-transparent p-5 text-left transition-colors hover:bg-background/28 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary"
        onClick={() => setExpanded((e) => !e)}
        type="button"
        aria-expanded={expanded}
        aria-controls="advanced-settings-content"
      >
        <span
          className={cn('text-xs text-muted-foreground transition-transform duration-200', expanded ? '' : '-rotate-90')}
        >
          ▼
        </span>
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold text-foreground">Advanced Settings</h3>
          <p className="text-sm text-muted-foreground">
            Display, workflow, notifications, project, and global settings.
          </p>
        </div>
      </button>

      {expanded && (
        <div
          id="advanced-settings-content"
          className="flex flex-col gap-8 border-t border-border p-5"
          role="region"
          aria-label="Advanced Settings"
        >
          <DisplayPreferences settings={userSettings.display} onSave={onUserSave} />

          <WorkflowDefaults settings={userSettings.workflow} onSave={onUserSave} />

          <NotificationPreferences settings={userSettings.notifications} onSave={onUserSave} />

          <ProjectSettings projects={projects} selectedProjectId={selectedProjectId} />

          <GlobalSettings
            settings={globalSettings}
            isLoading={globalLoading}
            onSave={onGlobalSave}
          />
        </div>
      )}
    </div>
  );
}
