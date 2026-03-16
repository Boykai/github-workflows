/**
 * Settings page layout — 4-tab organisation.
 *
 * Tabs: Essential | Secrets | Preferences | Admin
 * URL hash routing: #essential, #secrets, #preferences, #admin
 * Includes unsaved changes warning (FR-037).
 */

import { useState, useEffect, useCallback } from 'react';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { EssentialSettings } from '@/components/settings/EssentialSettings';
import { SecretsManager } from '@/components/settings/SecretsManager';
import { PreferencesTab } from '@/components/settings/PreferencesTab';
import { AdminTab } from '@/components/settings/AdminTab';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { useUserSettings, useGlobalSettings } from '@/hooks/useSettings';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import type { UserPreferencesUpdate, GlobalSettingsUpdate } from '@/types';

const VALID_TABS = ['essential', 'secrets', 'preferences', 'admin'] as const;
type TabValue = (typeof VALID_TABS)[number];

function getInitialTab(): TabValue {
  const hash = window.location.hash.replace('#', '') as TabValue;
  return VALID_TABS.includes(hash) ? hash : 'essential';
}

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

export function SettingsPage({ projects: propProjects, selectedProjectId: propSelectedProjectId }: SettingsPageProps) {
  const { user } = useAuth();
  const { projects: hookProjects, selectedProject } = useProjects(user?.selected_project_id);

  // Use provided props or fall back to hook-fetched projects
  const projects = propProjects ?? hookProjects?.map((p) => ({ project_id: p.project_id, name: p.name })) ?? [];
  const selectedProjectId = propSelectedProjectId ?? selectedProject?.project_id;

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

  useUnsavedChangesWarning(isUserUpdating || isGlobalUpdating);

  // Tab state with URL hash sync
  const [activeTab, setActiveTab] = useState<TabValue>(getInitialTab);

  // Admin check: compare user's github_user_id against globalSettings.admin_github_user_id
  const isAdmin =
    !!user &&
    !!globalSettings?.admin_github_user_id &&
    String(user.github_user_id) === String(globalSettings.admin_github_user_id);

  // If hash is #admin but user is not admin, fall back to essential
  useEffect(() => {
    if (activeTab === 'admin' && !isAdmin && !globalLoading) {
      setActiveTab('essential');
      window.history.replaceState(null, '', '#essential');
    }
  }, [activeTab, isAdmin, globalLoading]);

  // Listen for hash changes (back/forward navigation)
  useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.replace('#', '') as TabValue;
      if (VALID_TABS.includes(hash)) {
        setActiveTab(hash);
      }
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const handleTabChange = (value: string) => {
    const tab = value as TabValue;
    setActiveTab(tab);
    window.history.replaceState(null, '', `#${tab}`);
  };

  const handleUserSave = async (update: UserPreferencesUpdate) => {
    await updateUserSettings(update);
  };

  const handleGlobalSave = async (update: GlobalSettingsUpdate) => {
    await updateGlobalSettings(update);
  };

  if (userLoading) {
    return (
      <div className="flex h-full w-full max-w-4xl flex-col overflow-y-auto p-8 mx-auto">
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <CelestialLoader size="md" label="Loading settings…" />
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

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="essential">Essential</TabsTrigger>
          <TabsTrigger value="secrets">Secrets</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
          {isAdmin && <TabsTrigger value="admin">Admin</TabsTrigger>}
        </TabsList>

        <TabsContent value="essential">
          {userSettings && (
            <div className="flex flex-col gap-8 mt-4">
              <EssentialSettings settings={userSettings.ai} onSave={handleUserSave} />
            </div>
          )}
        </TabsContent>

        <TabsContent value="secrets">
          <div className="flex flex-col gap-8 mt-4">
            <SecretsManager projects={hookProjects} />
          </div>
        </TabsContent>

        <TabsContent value="preferences">
          {userSettings && (
            <div className="flex flex-col gap-8 mt-4">
              <PreferencesTab userSettings={userSettings} onUserSave={handleUserSave} />
            </div>
          )}
        </TabsContent>

        {isAdmin && (
          <TabsContent value="admin">
            <div className="flex flex-col gap-8 mt-4">
              <AdminTab
                globalSettings={globalSettings}
                globalLoading={globalLoading}
                onGlobalSave={handleGlobalSave}
                projects={projects}
                selectedProjectId={selectedProjectId}
              />
            </div>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
