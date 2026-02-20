/**
 * Global Settings section for instance-wide defaults.
 *
 * Displays and edits all global settings: AI, display, workflow,
 * notifications, and allowed models.
 */

import { useState, useEffect } from 'react';
import { SettingsSection } from './SettingsSection';
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

export function GlobalSettings({ settings, isLoading, onSave }: GlobalSettingsProps) {
  // AI
  const [provider, setProvider] = useState<AIProviderType>('copilot');
  const [model, setModel] = useState('gpt-4o');
  const [temperature, setTemperature] = useState(0.7);
  // Display
  const [theme, setTheme] = useState<ThemeModeType>('light');
  const [defaultView, setDefaultView] = useState<DefaultViewType>('chat');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  // Workflow
  const [defaultRepo, setDefaultRepo] = useState('');
  const [defaultAssignee, setDefaultAssignee] = useState('');
  const [pollingInterval, setPollingInterval] = useState(60);
  // Notifications
  const [taskStatusChange, setTaskStatusChange] = useState(true);
  const [agentCompletion, setAgentCompletion] = useState(true);
  const [newRecommendation, setNewRecommendation] = useState(true);
  const [chatMention, setChatMention] = useState(true);
  // Allowed models
  const [allowedModels, setAllowedModels] = useState('');

  useEffect(() => {
    if (!settings) return;
    setProvider(settings.ai.provider);
    setModel(settings.ai.model);
    setTemperature(settings.ai.temperature);
    setTheme(settings.display.theme);
    setDefaultView(settings.display.default_view);
    setSidebarCollapsed(settings.display.sidebar_collapsed);
    setDefaultRepo(settings.workflow.default_repository ?? '');
    setDefaultAssignee(settings.workflow.default_assignee);
    setPollingInterval(settings.workflow.copilot_polling_interval);
    setTaskStatusChange(settings.notifications.task_status_change);
    setAgentCompletion(settings.notifications.agent_completion);
    setNewRecommendation(settings.notifications.new_recommendation);
    setChatMention(settings.notifications.chat_mention);
    setAllowedModels(settings.allowed_models.join(', '));
  }, [settings]);

  if (isLoading || !settings) {
    return (
      <SettingsSection title="Global Settings" description="Instance-wide defaults" hideSave>
        <p>Loading global settings...</p>
      </SettingsSection>
    );
  }

  const isDirty =
    provider !== settings.ai.provider ||
    model !== settings.ai.model ||
    temperature !== settings.ai.temperature ||
    theme !== settings.display.theme ||
    defaultView !== settings.display.default_view ||
    sidebarCollapsed !== settings.display.sidebar_collapsed ||
    (defaultRepo || null) !== (settings.workflow.default_repository || null) ||
    defaultAssignee !== settings.workflow.default_assignee ||
    pollingInterval !== settings.workflow.copilot_polling_interval ||
    taskStatusChange !== settings.notifications.task_status_change ||
    agentCompletion !== settings.notifications.agent_completion ||
    newRecommendation !== settings.notifications.new_recommendation ||
    chatMention !== settings.notifications.chat_mention ||
    allowedModels !== settings.allowed_models.join(', ');

  const handleSave = async () => {
    const update: GlobalSettingsUpdate = {
      ai: { provider, model, temperature },
      display: { theme, default_view: defaultView, sidebar_collapsed: sidebarCollapsed },
      workflow: {
        default_repository: defaultRepo || null,
        default_assignee: defaultAssignee,
        copilot_polling_interval: pollingInterval,
      },
      notifications: {
        task_status_change: taskStatusChange,
        agent_completion: agentCompletion,
        new_recommendation: newRecommendation,
        chat_mention: chatMention,
      },
      allowed_models: allowedModels
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
        <select id="global-ai-provider" value={provider} onChange={(e) => setProvider(e.target.value as AIProviderType)}>
          <option value="copilot">GitHub Copilot</option>
          <option value="azure_openai">Azure OpenAI</option>
        </select>
      </div>
      <div className="settings-field">
        <label htmlFor="global-ai-model">Model</label>
        <input id="global-ai-model" type="text" value={model} onChange={(e) => setModel(e.target.value)} />
      </div>
      <div className="settings-field">
        <label htmlFor="global-ai-temp">Temperature: {temperature.toFixed(1)}</label>
        <input id="global-ai-temp" type="range" min="0" max="2" step="0.1" value={temperature} onChange={(e) => setTemperature(parseFloat(e.target.value))} />
      </div>

      {/* Display */}
      <h4 className="settings-subsection-title">Display</h4>
      <div className="settings-field">
        <label htmlFor="global-theme">Theme</label>
        <select id="global-theme" value={theme} onChange={(e) => setTheme(e.target.value as ThemeModeType)}>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
      <div className="settings-field">
        <label htmlFor="global-view">Default View</label>
        <select id="global-view" value={defaultView} onChange={(e) => setDefaultView(e.target.value as DefaultViewType)}>
          <option value="chat">Chat</option>
          <option value="board">Board</option>
          <option value="settings">Settings</option>
        </select>
      </div>
      <div className="settings-field">
        <label>
          <input type="checkbox" checked={sidebarCollapsed} onChange={(e) => setSidebarCollapsed(e.target.checked)} />
          Sidebar collapsed by default
        </label>
      </div>

      {/* Workflow */}
      <h4 className="settings-subsection-title">Workflow</h4>
      <div className="settings-field">
        <label htmlFor="global-repo">Default Repository</label>
        <input id="global-repo" type="text" value={defaultRepo} onChange={(e) => setDefaultRepo(e.target.value)} placeholder="owner/repo" />
      </div>
      <div className="settings-field">
        <label htmlFor="global-assignee">Default Assignee</label>
        <input id="global-assignee" type="text" value={defaultAssignee} onChange={(e) => setDefaultAssignee(e.target.value)} />
      </div>
      <div className="settings-field">
        <label htmlFor="global-polling">Polling Interval (seconds)</label>
        <input id="global-polling" type="number" min="0" value={pollingInterval} onChange={(e) => setPollingInterval(parseInt(e.target.value, 10) || 0)} />
      </div>

      {/* Notifications */}
      <h4 className="settings-subsection-title">Notifications</h4>
      <div className="settings-field"><label><input type="checkbox" checked={taskStatusChange} onChange={(e) => setTaskStatusChange(e.target.checked)} /> Task status changes</label></div>
      <div className="settings-field"><label><input type="checkbox" checked={agentCompletion} onChange={(e) => setAgentCompletion(e.target.checked)} /> Agent completion</label></div>
      <div className="settings-field"><label><input type="checkbox" checked={newRecommendation} onChange={(e) => setNewRecommendation(e.target.checked)} /> New recommendations</label></div>
      <div className="settings-field"><label><input type="checkbox" checked={chatMention} onChange={(e) => setChatMention(e.target.checked)} /> Chat mentions</label></div>

      {/* Allowed Models */}
      <h4 className="settings-subsection-title">Allowed Models</h4>
      <div className="settings-field">
        <label htmlFor="global-models">Comma-separated model identifiers</label>
        <input id="global-models" type="text" value={allowedModels} onChange={(e) => setAllowedModels(e.target.value)} placeholder="gpt-4o, gpt-4" />
      </div>
    </SettingsSection>
  );
}
