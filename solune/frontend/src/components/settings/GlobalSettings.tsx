/**
 * Global Settings section for instance-wide defaults.
 *
 * Uses react-hook-form + zod for form state management.
 * Delegates each settings domain to a focused subcomponent.
 */

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
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
}

export function GlobalSettings({ settings, isLoading, onSave }: GlobalSettingsProps) {
  const form = useForm<GlobalFormState>({
    resolver: zodResolver(globalSettingsSchema),
    defaultValues: settings ? flatten(settings) : DEFAULTS,
  });

  useEffect(() => {
    if (settings) {
      form.reset(flatten(settings));
    }
  }, [settings, form]);

  if (isLoading || !settings) {
    return (
      <SettingsSection title="Global Settings" description="Instance-wide defaults" hideSave>
        <p>Loading global settings...</p>
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
            {...form.register('allowed_models')}
          />
        </div>
      </SettingsSection>
    </div>
  );
}
