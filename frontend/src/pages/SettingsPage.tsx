/**
 * Settings page layout.
 *
 * Renders all settings sections: AI Preferences, Display Preferences,
 * Workflow Defaults, Notification Preferences, Project (placeholder),
 * and Global Settings. Includes unsaved changes warning (FR-037).
 */

import { useEffect, useCallback } from 'react';
import { AIPreferences } from '@/components/settings/AIPreferences';
import { DisplayPreferences } from '@/components/settings/DisplayPreferences';
import { GlobalSettings } from '@/components/settings/GlobalSettings';
import { NotificationPreferences } from '@/components/settings/NotificationPreferences';
import { ProjectSettings } from '@/components/settings/ProjectSettings';
import { SignalConnection } from '@/components/settings/SignalConnection';
import { WorkflowDefaults } from '@/components/settings/WorkflowDefaults';
import { useUserSettings, useGlobalSettings } from '@/hooks/useSettings';
import type { UserPreferencesUpdate, GlobalSettingsUpdate } from '@/types';

/**
 * Hook to warn user about unsaved changes when navigating away.
 * Attaches `beforeunload` listener when any section reports dirty state.
 */
function useUnsavedChangesWarning(isDirty: boolean) {
  const handleBeforeUnload = useCallback(
    (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
      }
    },
    [isDirty],
  );

  useEffect(() => {
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [handleBeforeUnload]);
}

interface SettingsPageProps {
  projects?: Array<{ project_id: string; name: string }>;
  selectedProjectId?: string;
}

export function SettingsPage({ projects = [], selectedProjectId }: SettingsPageProps) {
  const {
    settings: userSettings,
    isLoading: userLoading,
    updateSettings: updateUserSettings,
    isUpdating: isUserUpdating,
  } = useUserSettings();

  const {
    settings: globalSettings,
    isLoading: globalLoading,
    updateSettings: updateGlobalSettings,
    isUpdating: isGlobalUpdating,
  } = useGlobalSettings();

  // Track whether any mutation is in-flight as proxy for dirty state
  // (Individual dirty tracking is handled within each SettingsSection)
  useUnsavedChangesWarning(isUserUpdating || isGlobalUpdating);

  const handleUserSave = async (update: UserPreferencesUpdate) => {
    await updateUserSettings(update);
  };

  const handleGlobalSave = async (update: GlobalSettingsUpdate) => {
    await updateGlobalSettings(update);
  };

  if (userLoading) {
    return (
      <div className="flex flex-col h-full p-8 overflow-y-auto max-w-4xl mx-auto w-full">
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full p-8 overflow-y-auto max-w-4xl mx-auto w-full">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight mb-2">Settings</h2>
        <p className="text-muted-foreground">Configure your preferences for Agent Projects.</p>
      </div>

      <div className="flex flex-col gap-8">
        {/* AI Preferences (US3) */}
        {userSettings && (
          <AIPreferences settings={userSettings.ai} onSave={handleUserSave} />
        )}

        {/* Display Preferences (US5) */}
        {userSettings && (
          <DisplayPreferences settings={userSettings.display} onSave={handleUserSave} />
        )}

        {/* Workflow Defaults (US6) */}
        {userSettings && (
          <WorkflowDefaults settings={userSettings.workflow} onSave={handleUserSave} />
        )}

        {/* Notification Preferences (US7) */}
        {userSettings && (
          <NotificationPreferences settings={userSettings.notifications} onSave={handleUserSave} />
        )}

        {/* Signal Integration (011-signal-chat-integration) */}
        <SignalConnection />

        {/* Project Settings (US8) */}
        <ProjectSettings
          projects={projects}
          selectedProjectId={selectedProjectId}
        />

        {/* Global Settings (US9) */}
        <GlobalSettings
          settings={globalSettings}
          isLoading={globalLoading}
          onSave={handleGlobalSave}
        />
      </div>
    </div>
  );
}
