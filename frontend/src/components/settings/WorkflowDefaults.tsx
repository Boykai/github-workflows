/**
 * Workflow Defaults settings section.
 *
 * Allows user to configure default repository, assignee, and polling interval.
 */

import { SettingsSection } from './SettingsSection';
import { useSettingsForm } from '@/hooks/useSettingsForm';
import type {
  WorkflowDefaults as WorkflowDefaultsType,
  UserPreferencesUpdate,
} from '@/types';

interface WorkflowDefaultsProps {
  settings: WorkflowDefaultsType;
  onSave: (update: UserPreferencesUpdate) => Promise<void>;
}

// Internal shape with non-null `default_repository` for controlled inputs.
interface WorkflowFormState {
  default_repository: string;
  default_assignee: string;
  copilot_polling_interval: number;
}

function toFormState(s: WorkflowDefaultsType): WorkflowFormState {
  return {
    default_repository: s.default_repository ?? '',
    default_assignee: s.default_assignee,
    copilot_polling_interval: s.copilot_polling_interval,
  };
}

export function WorkflowDefaults({ settings, onSave }: WorkflowDefaultsProps) {
  const { localState, setField, isDirty } = useSettingsForm(toFormState(settings));

  const handleSave = async () => {
    await onSave({
      workflow: {
        default_repository: localState.default_repository || null,
        default_assignee: localState.default_assignee,
        copilot_polling_interval: localState.copilot_polling_interval,
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
          value={localState.default_repository}
          onChange={(e) => setField('default_repository', e.target.value)}
          placeholder="owner/repo"
        />
      </div>

      <div className="settings-field">
        <label htmlFor="workflow-assignee">Default Assignee</label>
        <input
          id="workflow-assignee"
          type="text"
          value={localState.default_assignee}
          onChange={(e) => setField('default_assignee', e.target.value)}
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
          value={localState.copilot_polling_interval}
          onChange={(e) => setField('copilot_polling_interval', parseInt(e.target.value, 10) || 0)}
        />
      </div>
    </SettingsSection>
  );
}
