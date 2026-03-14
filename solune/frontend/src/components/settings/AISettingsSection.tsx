import type { UseFormReturn } from 'react-hook-form';
import type { GlobalFormState } from './globalSettingsSchema';

interface AISettingsSectionProps {
  form: UseFormReturn<GlobalFormState>;
}

export function AISettingsSection({ form }: AISettingsSectionProps) {
  const { register, watch } = form;

  return (
    <>
      <h4 className="text-sm font-semibold text-foreground mt-4 border-b border-border pb-2">
        AI
      </h4>
      <div className="flex flex-col gap-2">
        <label htmlFor="global-ai-provider" className="text-sm font-medium text-foreground">
          Provider
        </label>
        <select
          id="global-ai-provider"
          className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none"
          {...register('provider')}
        >
          <option value="copilot">GitHub Copilot</option>
          <option value="azure_openai">Azure OpenAI</option>
        </select>
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="global-ai-model" className="text-sm font-medium text-foreground">
          Model
        </label>
        <input
          id="global-ai-model"
          type="text"
          className="celestial-focus flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
          {...register('model')}
        />
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="global-ai-temp" className="text-sm font-medium text-foreground">
          Temperature: {watch('temperature').toFixed(1)}
        </label>
        <input
          id="global-ai-temp"
          type="range"
          className="celestial-focus w-full accent-primary"
          min="0"
          max="2"
          step="0.1"
          {...register('temperature', { valueAsNumber: true })}
        />
      </div>
    </>
  );
}
