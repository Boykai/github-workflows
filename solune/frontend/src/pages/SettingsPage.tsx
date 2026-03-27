/**
 * Settings page layout.
 *
 * Reorganized for UX simplification: Primary settings (AI configuration,
 * Signal connection) at the top, Advanced settings collapsed below.
 * Includes unsaved changes warning (FR-037).
 */

import { useEffect, useCallback } from 'react';
import { CelestialLoadingProgress } from '@/components/common/CelestialLoadingProgress';
import { PrimarySettings } from '@/components/settings/PrimarySettings';
import { AdvancedSettings } from '@/components/settings/AdvancedSettings';
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
    [isDirty]
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

  if (userLoading || globalLoading) {
    return (
      <div className="flex h-full w-full max-w-4xl flex-col overflow-y-auto p-8 mx-auto">
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <CelestialLoadingProgress
            phases={[
              { label: 'Loading user settings…', complete: !userLoading },
              { label: 'Loading global settings…', complete: !globalLoading },
            ]}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="celestial-fade-in flex h-full w-full max-w-4xl flex-col overflow-y-auto rounded-[1.75rem] border border-border/70 bg-background/42 p-8 backdrop-blur-sm mx-auto">
      <div className="mb-8">
        <p className="mb-1 text-xs uppercase tracking-[0.24em] text-primary/80">
          Orbital Configuration
        </p>
        <h2 className="mb-2 text-3xl font-display font-medium tracking-[0.04em]">Settings</h2>
        <p className="text-muted-foreground">Configure your preferences for Solune.</p>
      </div>

      <div className="flex flex-col gap-8">
        {/* Primary Settings: AI Configuration + Signal Connection */}
        {userSettings && <PrimarySettings settings={userSettings.ai} onSave={handleUserSave} />}

        {/* Advanced Settings: Display, Workflow, Notifications, Project, Global */}
        {userSettings && (
          <AdvancedSettings
            userSettings={userSettings}
            globalSettings={globalSettings}
            globalLoading={globalLoading}
            onUserSave={handleUserSave}
            onGlobalSave={handleGlobalSave}
            projects={projects}
            selectedProjectId={selectedProjectId}
          />
        )}
      </div>
    </div>
  );
}
