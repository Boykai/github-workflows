/**
 * AI Preferences settings section.
 *
 * Allows user to configure AI provider, model, and temperature.
 */

import { SettingsSection } from './SettingsSection';
import { useSettingsForm } from '@/hooks/useSettingsForm';
import type {
  AIPreferences as AIPreferencesType,
  AIProviderType,
  UserPreferencesUpdate,
} from '@/types';

interface AIPreferencesProps {
  settings: AIPreferencesType;
  onSave: (update: UserPreferencesUpdate) => Promise<void>;
}

export function AIPreferences({ settings, onSave }: AIPreferencesProps) {
  const { localState, setField, isDirty } = useSettingsForm(settings);

  const handleSave = async () => {
    await onSave({
      ai: { provider: localState.provider, model: localState.model, temperature: localState.temperature },
    });
  };

  return (
    <SettingsSection
      title="AI Preferences"
      description="Configure the AI provider, model, and generation temperature."
      isDirty={isDirty}
      onSave={handleSave}
    >
      <div className="settings-field">
        <label htmlFor="ai-provider">Provider</label>
        <select
          id="ai-provider"
          value={localState.provider}
          onChange={(e) => setField('provider', e.target.value as AIProviderType)}
        >
          <option value="copilot">GitHub Copilot</option>
          <option value="azure_openai">Azure OpenAI</option>
        </select>
      </div>

      <div className="settings-field">
        <label htmlFor="ai-model">Model</label>
        <input
          id="ai-model"
          type="text"
          value={localState.model}
          onChange={(e) => setField('model', e.target.value)}
          placeholder="e.g. gpt-4o"
        />
      </div>

      <div className="settings-field">
        <label htmlFor="ai-temperature">
          Temperature: {localState.temperature.toFixed(1)}
        </label>
        <input
          id="ai-temperature"
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={localState.temperature}
          onChange={(e) => setField('temperature', parseFloat(e.target.value))}
        />
        <div className="settings-range-labels">
          <span>Precise (0)</span>
          <span>Creative (2)</span>
        </div>
      </div>
    </SettingsSection>
  );
}
