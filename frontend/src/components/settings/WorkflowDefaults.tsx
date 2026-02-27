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
      <div className="flex flex-col gap-2">
        <label htmlFor="workflow-repo" className="text-sm font-medium text-foreground">Default Repository</label>
        <input
          id="workflow-repo"
          type="text"
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={localState.default_repository}
          onChange={(e) => setField('default_repository', e.target.value)}
          placeholder="owner/repo"
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="workflow-assignee" className="text-sm font-medium text-foreground">Default Assignee</label>
        <input
          id="workflow-assignee"
          type="text"
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={localState.default_assignee}
          onChange={(e) => setField('default_assignee', e.target.value)}
          placeholder="GitHub username"
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="workflow-polling" className="text-sm font-medium text-foreground">
          Copilot Polling Interval (seconds, 0 to disable)
        </label>
        <input
          id="workflow-polling"
          type="number"
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          min="0"
          value={localState.copilot_polling_interval}
          onChange={(e) => setField('copilot_polling_interval', parseInt(e.target.value, 10) || 0)}
        />
      </div>
    </SettingsSection>
  );
}
