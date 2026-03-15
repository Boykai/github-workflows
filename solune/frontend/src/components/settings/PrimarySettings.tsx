/**
 * Primary Settings component.
 *
 * Renders the most important settings prominently at the top of the
 * Settings page: model provider, chat model (dynamic dropdown),
 * GitHub agent model (dynamic dropdown), and Signal connection.
 */

import { SettingsSection } from './SettingsSection';
import { DynamicDropdown } from './DynamicDropdown';
import { SignalConnection } from './SignalConnection';
import { useSettingsForm } from '@/hooks/useSettingsForm';
import { useModelOptions } from '@/hooks/useSettings';
import type { AIPreferences, AIProviderType, UserPreferencesUpdate } from '@/types';

/** Provider metadata — mirrors backend PROVIDER_METADATA */
const PROVIDER_INFO: Record<string, { label: string; supportsDynamic: boolean }> = {
  copilot: { label: 'GitHub Copilot', supportsDynamic: true },
  azure_openai: { label: 'Azure OpenAI', supportsDynamic: false },
};

interface PrimarySettingsProps {
  settings: AIPreferences;
  onSave: (update: UserPreferencesUpdate) => Promise<void>;
}

export function PrimarySettings({ settings, onSave }: PrimarySettingsProps) {
  const { localState, setField, isDirty } = useSettingsForm(settings);

  const providerInfo = PROVIDER_INFO[localState.provider] ?? {
    label: localState.provider,
    supportsDynamic: false,
  };

  // Fetch models for the current provider
  const {
    data: modelsResponse,
    isLoading: modelsLoading,
    refetch: refetchModels,
  } = useModelOptions(localState.provider);

  const handleProviderChange = (newProvider: AIProviderType) => {
    setField('provider', newProvider);
    // Clear model when switching provider to avoid stale selection
    setField('model', '');
  };

  const handleSave = async () => {
    await onSave({
      ai: {
        provider: localState.provider,
        model: localState.model,
        agent_model: localState.agent_model,
        temperature: localState.temperature,
      },
    });
  };

  return (
    <>
      {/* AI Model Configuration */}
      <SettingsSection
        title="AI Configuration"
        description="Select your AI provider and model. These are the most important settings for your experience."
        isDirty={isDirty}
        onSave={handleSave}
      >
        {/* Provider Selection */}
        <div className="flex flex-col gap-2">
          <label htmlFor="primary-provider" className="text-sm font-medium text-foreground">
            Model Provider
          </label>
          <select
            id="primary-provider"
            className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none"
            value={localState.provider}
            onChange={(e) => handleProviderChange(e.target.value as AIProviderType)}
            aria-label="Model Provider"
          >
            {Object.entries(PROVIDER_INFO).map(([key, info]) => (
              <option key={key} value={key}>
                {info.label}
              </option>
            ))}
          </select>
        </div>

        {/* Chat Model (dynamic) */}
        <DynamicDropdown
          id="primary-chat-model"
          label="Chat Model"
          value={localState.model}
          onChange={(val) => setField('model', val)}
          provider={localState.provider}
          supportsDynamic={providerInfo.supportsDynamic}
          modelsResponse={modelsResponse}
          isLoading={modelsLoading}
          onRetry={() => refetchModels()}
        />

        {/* Agent Model (Auto) — fallback for GitHub Copilot Agents */}
        <div className="flex flex-col gap-2">
          <DynamicDropdown
            id="primary-agent-model"
            label="Agent Model (Auto)"
            value={localState.agent_model}
            onChange={(val) => setField('agent_model', val)}
            provider={localState.provider}
            supportsDynamic={providerInfo.supportsDynamic}
            modelsResponse={modelsResponse}
            isLoading={modelsLoading}
            onRetry={() => refetchModels()}
          />
          <p className="text-xs text-muted-foreground">
            Fallback model for all GitHub Copilot Agents. Takes lower priority than pipeline model
            configuration.
          </p>
        </div>

        {/* Temperature */}
        <div className="flex flex-col gap-2">
          <label htmlFor="primary-temperature" className="text-sm font-medium text-foreground">
            Temperature: {localState.temperature.toFixed(1)}
          </label>
          <input
            id="primary-temperature"
            type="range"
            className="celestial-focus w-full accent-primary"
            min="0"
            max="2"
            step="0.1"
            value={localState.temperature}
            onChange={(e) => setField('temperature', parseFloat(e.target.value))}
            aria-label={`Temperature: ${localState.temperature.toFixed(1)}`}
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>Precise (0)</span>
            <span>Creative (2)</span>
          </div>
        </div>
      </SettingsSection>

      {/* Signal Connection */}
      <SignalConnection />
    </>
  );
}
