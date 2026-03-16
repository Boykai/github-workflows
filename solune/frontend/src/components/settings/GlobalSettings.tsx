/**
 * Global Settings section for instance-wide defaults.
 *
 * Uses react-hook-form + zod for form state management.
 * Delegates each settings domain to a focused subcomponent.
 */

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { SettingsSection } from './SettingsSection';
import { AISettingsSection } from './AISettingsSection';
import { DisplaySettings } from './DisplaySettings';
import { WorkflowSettings } from './WorkflowSettings';
import { NotificationSettings } from './NotificationSettings';
import {
  globalSettingsSchema,
  DEFAULTS,
  flatten,
  toUpdate,
  type GlobalFormState,
} from './globalSettingsSchema';
import type { GlobalSettings as GlobalSettingsType, GlobalSettingsUpdate } from '@/types';

interface GlobalSettingsProps {
  settings: GlobalSettingsType | undefined;
  isLoading: boolean;
  onSave: (update: GlobalSettingsUpdate) => Promise<void>;
  /** Error from query or mutation */
  error?: Error | null;
  /** Whether the current error is a rate limit error */
  isRateLimitError?: boolean;
  /** Refetch the settings data */
  onRetry?: () => void;
}

export function GlobalSettings({
  settings,
  isLoading,
  onSave,
  error,
  isRateLimitError,
  onRetry,
}: GlobalSettingsProps) {
  const form = useForm<GlobalFormState>({
    resolver: zodResolver(globalSettingsSchema),
    defaultValues: settings ? flatten(settings) : DEFAULTS,
  });

  useEffect(() => {
    if (settings) {
      form.reset(flatten(settings));
    }
  }, [settings, form]);

  if (isLoading) {
    return (
      <SettingsSection title="Global Settings" description="Instance-wide defaults" hideSave>
        <div className="flex items-center justify-center py-8">
          <CelestialLoader size="md" label="Loading global settings…" />
        </div>
      </SettingsSection>
    );
  }

  if (error && !settings) {
    return (
      <SettingsSection title="Global Settings" description="Instance-wide defaults" hideSave>
        <div
          className="rounded-[1.15rem] border border-destructive/30 bg-destructive/10 p-4"
          role="alert"
        >
          <p className="text-sm font-medium text-destructive">
            {isRateLimitError
              ? 'Rate limit reached. Please wait a moment before retrying.'
              : 'Could not load global settings. Please try again.'}
          </p>
          {onRetry && (
            <button
              className="mt-2 text-sm font-medium text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded"
              onClick={onRetry}
              type="button"
            >
              Retry
            </button>
          )}
        </div>
      </SettingsSection>
    );
  }

  if (!settings) {
    return (
      <SettingsSection title="Global Settings" description="Instance-wide defaults" hideSave>
        <div className="flex items-center justify-center py-8">
          <CelestialLoader size="md" label="Loading global settings…" />
        </div>
      </SettingsSection>
    );
  }

  const handleSave = form.handleSubmit(async (values) => {
    await onSave(toUpdate(values));
  });

  return (
    <div className="celestial-fade-in">
      <SettingsSection
        title="Global Settings"
        description="Instance-wide defaults that apply to all users unless overridden."
        isDirty={form.formState.isDirty}
        onSave={handleSave}
        defaultCollapsed
      >
        <AISettingsSection form={form} />
        <DisplaySettings form={form} />
        <WorkflowSettings form={form} />
        <NotificationSettings form={form} />

        {/* Allowed Models */}
        <h4 className="text-sm font-semibold text-foreground mt-4 border-b border-border pb-2">
          Allowed Models
        </h4>
        <div className="flex flex-col gap-2">
          <label htmlFor="global-models" className="text-sm font-medium text-foreground">
            Comma-separated model identifiers
          </label>
          <input
            id="global-models"
            type="text"
            className="celestial-focus flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
            placeholder="gpt-4o, gpt-4"
            aria-describedby={form.formState.errors.allowed_models ? 'global-models-error' : undefined}
            {...form.register('allowed_models')}
          />
          {form.formState.errors.allowed_models && (
            <p id="global-models-error" className="text-xs text-destructive" role="alert">
              {form.formState.errors.allowed_models.message}
            </p>
          )}
        </div>
      </SettingsSection>
    </div>
  );
}
