/**
 * Workflow Defaults settings section.
 *
 * Allows user to configure default repository, assignee, and polling interval.
 */

import { useState, useEffect } from 'react';
import { SettingsSection } from './SettingsSection';
import type {
  WorkflowDefaults as WorkflowDefaultsType,
  UserPreferencesUpdate,
} from '@/types';

interface WorkflowDefaultsProps {
  settings: WorkflowDefaultsType;
  onSave: (update: UserPreferencesUpdate) => Promise<void>;
}

export function WorkflowDefaults({ settings, onSave }: WorkflowDefaultsProps) {
  const [defaultRepo, setDefaultRepo] = useState(settings.default_repository ?? '');
  const [defaultAssignee, setDefaultAssignee] = useState(settings.default_assignee);
  const [pollingInterval, setPollingInterval] = useState(settings.copilot_polling_interval);

  useEffect(() => {
    setDefaultRepo(settings.default_repository ?? '');
    setDefaultAssignee(settings.default_assignee);
    setPollingInterval(settings.copilot_polling_interval);
  }, [settings.default_repository, settings.default_assignee, settings.copilot_polling_interval]);

  const isDirty =
    (defaultRepo || null) !== (settings.default_repository || null) ||
    defaultAssignee !== settings.default_assignee ||
    pollingInterval !== settings.copilot_polling_interval;

  const handleSave = async () => {
    await onSave({
      workflow: {
        default_repository: defaultRepo || null,
        default_assignee: defaultAssignee,
        copilot_polling_interval: pollingInterval,
      },
    });
  };

  return (
    <SettingsSection
      title="Workflow Defaults"
      description="Default repository, assignee, and Copilot polling interval."
      isDirty={isDirty}
      onSave={handleSave}
    >
      <div className="settings-field">
        <label htmlFor="workflow-repo">Default Repository</label>
        <input
          id="workflow-repo"
          type="text"
          value={defaultRepo}
          onChange={(e) => setDefaultRepo(e.target.value)}
          placeholder="owner/repo"
        />
      </div>

      <div className="settings-field">
        <label htmlFor="workflow-assignee">Default Assignee</label>
        <input
          id="workflow-assignee"
          type="text"
          value={defaultAssignee}
          onChange={(e) => setDefaultAssignee(e.target.value)}
          placeholder="GitHub username"
        />
      </div>

      <div className="settings-field">
        <label htmlFor="workflow-polling">
          Copilot Polling Interval (seconds, 0 to disable)
        </label>
        <input
          id="workflow-polling"
          type="number"
          min="0"
          value={pollingInterval}
          onChange={(e) => setPollingInterval(parseInt(e.target.value, 10) || 0)}
        />
      </div>
    </SettingsSection>
  );
}
