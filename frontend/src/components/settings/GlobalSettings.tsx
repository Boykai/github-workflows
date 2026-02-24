/**
 * Global Settings section for instance-wide defaults.
 *
 * Displays and edits all global settings: AI, display, workflow,
 * notifications, and allowed models.
 */

import { SettingsSection } from './SettingsSection';
import { useSettingsForm } from '@/hooks/useSettingsForm';
import type {
  GlobalSettings as GlobalSettingsType,
  GlobalSettingsUpdate,
  AIProviderType,
  ThemeModeType,
  DefaultViewType,
} from '@/types';

interface GlobalSettingsProps {
  settings: GlobalSettingsType | undefined;
  isLoading: boolean;
  onSave: (update: GlobalSettingsUpdate) => Promise<void>;
}

/** Flat form state derived from the nested GlobalSettingsType. */
interface GlobalFormState {
  provider: AIProviderType;
  model: string;
  temperature: number;
  theme: ThemeModeType;
  default_view: DefaultViewType;
  sidebar_collapsed: boolean;
  default_repository: string;
  default_assignee: string;
  copilot_polling_interval: number;
  task_status_change: boolean;
  agent_completion: boolean;
  new_recommendation: boolean;
  chat_mention: boolean;
  allowed_models: string;
}

const DEFAULTS: GlobalFormState = {
  provider: 'copilot',
  model: 'gpt-4o',
  temperature: 0.7,
  theme: 'light',
  default_view: 'chat',
  sidebar_collapsed: false,
  default_repository: '',
  default_assignee: '',
  copilot_polling_interval: 60,
  task_status_change: true,
  agent_completion: true,
  new_recommendation: true,
  chat_mention: true,
  allowed_models: '',
};

function flatten(s: GlobalSettingsType): GlobalFormState {
  return {
    provider: s.ai.provider,
    model: s.ai.model,
    temperature: s.ai.temperature,
    theme: s.display.theme,
    default_view: s.display.default_view,
    sidebar_collapsed: s.display.sidebar_collapsed,
    default_repository: s.workflow.default_repository ?? '',
    default_assignee: s.workflow.default_assignee,
    copilot_polling_interval: s.workflow.copilot_polling_interval,
    task_status_change: s.notifications.task_status_change,
    agent_completion: s.notifications.agent_completion,
    new_recommendation: s.notifications.new_recommendation,
    chat_mention: s.notifications.chat_mention,
    allowed_models: s.allowed_models.join(', '),
  };
}

export function GlobalSettings({ settings, isLoading, onSave }: GlobalSettingsProps) {
  const { localState: f, setField, isDirty } = useSettingsForm(
    settings ? flatten(settings) : DEFAULTS,
  );

  if (isLoading || !settings) {
    return (
      <SettingsSection title="Global Settings" description="Instance-wide defaults" hideSave>
        <p>Loading global settings...</p>
      </SettingsSection>
    );
  }

  const handleSave = async () => {
    const update: GlobalSettingsUpdate = {
      ai: { provider: f.provider, model: f.model, temperature: f.temperature },
      display: { theme: f.theme, default_view: f.default_view, sidebar_collapsed: f.sidebar_collapsed },
      workflow: {
        default_repository: f.default_repository || null,
        default_assignee: f.default_assignee,
        copilot_polling_interval: f.copilot_polling_interval,
      },
      notifications: {
        task_status_change: f.task_status_change,
        agent_completion: f.agent_completion,
        new_recommendation: f.new_recommendation,
        chat_mention: f.chat_mention,
      },
      allowed_models: f.allowed_models
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    };
    await onSave(update);
  };

  return (
    <SettingsSection
      title="Global Settings"
      description="Instance-wide defaults that apply to all users unless overridden."
      isDirty={isDirty}
      onSave={handleSave}
      defaultCollapsed
    >
      {/* AI Settings */}
      <h4 className="settings-subsection-title">AI</h4>
      <div className="settings-field">
        <label htmlFor="global-ai-provider">Provider</label>
        <select id="global-ai-provider" value={f.provider} onChange={(e) => setField('provider', e.target.value as AIProviderType)}>
          <option value="copilot">GitHub Copilot</option>
          <option value="azure_openai">Azure OpenAI</option>
        </select>
      </div>
      <div className="settings-field">
        <label htmlFor="global-ai-model">Model</label>
        <input id="global-ai-model" type="text" value={f.model} onChange={(e) => setField('model', e.target.value)} />
      </div>
      <div className="settings-field">
        <label htmlFor="global-ai-temp">Temperature: {f.temperature.toFixed(1)}</label>
        <input id="global-ai-temp" type="range" min="0" max="2" step="0.1" value={f.temperature} onChange={(e) => setField('temperature', parseFloat(e.target.value))} />
      </div>

      {/* Display */}
      <h4 className="settings-subsection-title">Display</h4>
      <div className="settings-field">
        <label htmlFor="global-theme">Theme</label>
        <select id="global-theme" value={f.theme} onChange={(e) => setField('theme', e.target.value as ThemeModeType)}>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
      <div className="settings-field">
        <label htmlFor="global-view">Default View</label>
        <select id="global-view" value={f.default_view} onChange={(e) => setField('default_view', e.target.value as DefaultViewType)}>
          <option value="chat">Chat</option>
          <option value="board">Board</option>
          <option value="settings">Settings</option>
        </select>
      </div>
      <div className="settings-field">
        <label>
          <input type="checkbox" checked={f.sidebar_collapsed} onChange={(e) => setField('sidebar_collapsed', e.target.checked)} />
          Sidebar collapsed by default
        </label>
      </div>

      {/* Workflow */}
      <h4 className="settings-subsection-title">Workflow</h4>
      <div className="settings-field">
        <label htmlFor="global-repo">Default Repository</label>
        <input id="global-repo" type="text" value={f.default_repository} onChange={(e) => setField('default_repository', e.target.value)} placeholder="owner/repo" />
      </div>
      <div className="settings-field">
        <label htmlFor="global-assignee">Default Assignee</label>
        <input id="global-assignee" type="text" value={f.default_assignee} onChange={(e) => setField('default_assignee', e.target.value)} />
      </div>
      <div className="settings-field">
        <label htmlFor="global-polling">Polling Interval (seconds)</label>
        <input id="global-polling" type="number" min="0" value={f.copilot_polling_interval} onChange={(e) => setField('copilot_polling_interval', parseInt(e.target.value, 10) || 0)} />
      </div>

      {/* Notifications */}
      <h4 className="settings-subsection-title">Notifications</h4>
      <div className="settings-field"><label><input type="checkbox" checked={f.task_status_change} onChange={(e) => setField('task_status_change', e.target.checked)} /> Task status changes</label></div>
      <div className="settings-field"><label><input type="checkbox" checked={f.agent_completion} onChange={(e) => setField('agent_completion', e.target.checked)} /> Agent completion</label></div>
      <div className="settings-field"><label><input type="checkbox" checked={f.new_recommendation} onChange={(e) => setField('new_recommendation', e.target.checked)} /> New recommendations</label></div>
      <div className="settings-field"><label><input type="checkbox" checked={f.chat_mention} onChange={(e) => setField('chat_mention', e.target.checked)} /> Chat mentions</label></div>

      {/* Allowed Models */}
      <h4 className="settings-subsection-title">Allowed Models</h4>
      <div className="settings-field">
        <label htmlFor="global-models">Comma-separated model identifiers</label>
        <input id="global-models" type="text" value={f.allowed_models} onChange={(e) => setField('allowed_models', e.target.value)} placeholder="gpt-4o, gpt-4" />
      </div>
    </SettingsSection>
  );
}
