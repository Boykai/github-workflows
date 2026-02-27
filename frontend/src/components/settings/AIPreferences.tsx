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
      <div className="flex flex-col gap-2">
        <label htmlFor="ai-provider" className="text-sm font-medium text-foreground">Provider</label>
        <select
          id="ai-provider"
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={localState.provider}
          onChange={(e) => setField('provider', e.target.value as AIProviderType)}
        >
          <option value="copilot">GitHub Copilot</option>
          <option value="azure_openai">Azure OpenAI</option>
        </select>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="ai-model" className="text-sm font-medium text-foreground">Model</label>
        <input
          id="ai-model"
          type="text"
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={localState.model}
          onChange={(e) => setField('model', e.target.value)}
          placeholder="e.g. gpt-4o"
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="ai-temperature" className="text-sm font-medium text-foreground">
          Temperature: {localState.temperature.toFixed(1)}
        </label>
        <input
          id="ai-temperature"
          type="range"
          className="w-full accent-primary"
          min="0"
          max="2"
          step="0.1"
          value={localState.temperature}
          onChange={(e) => setField('temperature', parseFloat(e.target.value))}
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>Precise (0)</span>
          <span>Creative (2)</span>
        </div>
      </div>
    </SettingsSection>
  );
}
