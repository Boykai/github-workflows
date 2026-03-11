import type { UseFormReturn } from 'react-hook-form';
import type { GlobalFormState } from './globalSettingsSchema';

interface WorkflowSettingsProps {
  form: UseFormReturn<GlobalFormState>;
}

export function WorkflowSettings({ form }: WorkflowSettingsProps) {
  const { register } = form;

  return (
    <>
      <h4 className="text-sm font-semibold text-foreground mt-4 border-b border-border pb-2">
        Workflow
      </h4>
      <div className="flex flex-col gap-2">
        <label htmlFor="global-repo" className="text-sm font-medium text-foreground">
          Default Repository
        </label>
        <input
          id="global-repo"
          type="text"
          className="celestial-focus flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
          placeholder="owner/repo"
          {...register('default_repository')}
        />
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="global-assignee" className="text-sm font-medium text-foreground">
          Default Assignee
        </label>
        <input
          id="global-assignee"
          type="text"
          className="celestial-focus flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
          {...register('default_assignee')}
        />
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="global-polling" className="text-sm font-medium text-foreground">
          Polling Interval (seconds)
        </label>
        <input
          id="global-polling"
          type="number"
          className="celestial-focus flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
          min="0"
          {...register('copilot_polling_interval', { valueAsNumber: true })}
        />
      </div>
    </>
  );
}
