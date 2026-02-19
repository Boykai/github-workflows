/**
 * AI Preferences settings section.
 *
 * Allows user to configure AI provider, model, and temperature.
 */

import { useState, useEffect } from 'react';
import { SettingsSection } from './SettingsSection';
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
  const [provider, setProvider] = useState<AIProviderType>(settings.provider);
  const [model, setModel] = useState(settings.model);
  const [temperature, setTemperature] = useState(settings.temperature);

  // Sync local state when settings change externally
  useEffect(() => {
    setProvider(settings.provider);
    setModel(settings.model);
    setTemperature(settings.temperature);
  }, [settings.provider, settings.model, settings.temperature]);

  const isDirty =
    provider !== settings.provider ||
    model !== settings.model ||
    temperature !== settings.temperature;

  const handleSave = async () => {
    await onSave({
      ai: { provider, model, temperature },
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
          value={provider}
          onChange={(e) => setProvider(e.target.value as AIProviderType)}
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
          value={model}
          onChange={(e) => setModel(e.target.value)}
          placeholder="e.g. gpt-4o"
        />
      </div>

      <div className="settings-field">
        <label htmlFor="ai-temperature">
          Temperature: {temperature.toFixed(1)}
        </label>
        <input
          id="ai-temperature"
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={temperature}
          onChange={(e) => setTemperature(parseFloat(e.target.value))}
        />
        <div className="settings-range-labels">
          <span>Precise (0)</span>
          <span>Creative (2)</span>
        </div>
      </div>
    </SettingsSection>
  );
}
