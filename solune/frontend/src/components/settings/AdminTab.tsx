/**
 * Admin Tab component.
 *
 * Consolidates GlobalSettings and ProjectSettings into the Admin tab.
 * Only visible to admin users (controlled by SettingsPage).
 */

import { GlobalSettings } from './GlobalSettings';
import { ProjectSettings } from './ProjectSettings';
import type { GlobalSettings as GlobalSettingsType, GlobalSettingsUpdate } from '@/types';

interface AdminTabProps {
  globalSettings: GlobalSettingsType | undefined;
  globalLoading: boolean;
  onGlobalSave: (update: GlobalSettingsUpdate) => Promise<void>;
  projects: Array<{ project_id: string; name: string }>;
  selectedProjectId?: string;
}

export function AdminTab({
  globalSettings,
  globalLoading,
  onGlobalSave,
  projects,
  selectedProjectId,
}: AdminTabProps) {
  return (
    <div className="flex flex-col gap-8">
      <GlobalSettings settings={globalSettings} isLoading={globalLoading} onSave={onGlobalSave} />
      <ProjectSettings projects={projects} selectedProjectId={selectedProjectId} />
    </div>
  );
}
