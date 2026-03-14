import type { UseFormReturn } from 'react-hook-form';
import type { GlobalFormState } from './globalSettingsSchema';

interface DisplaySettingsProps {
  form: UseFormReturn<GlobalFormState>;
}

export function DisplaySettings({ form }: DisplaySettingsProps) {
  const { register } = form;

  return (
    <>
      <h4 className="text-sm font-semibold text-foreground mt-4 border-b border-border pb-2">
        Display
      </h4>
      <div className="flex flex-col gap-2">
        <label htmlFor="global-theme" className="text-sm font-medium text-foreground">
          Theme
        </label>
        <select
          id="global-theme"
          className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none"
          {...register('theme')}
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="global-view" className="text-sm font-medium text-foreground">
          Default View
        </label>
        <select
          id="global-view"
          className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none"
          {...register('default_view')}
        >
          <option value="chat">Chat</option>
          <option value="board">Board</option>
          <option value="settings">Settings</option>
        </select>
      </div>
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
          <input
            type="checkbox"
            className="celestial-focus w-4 h-4 rounded border-input text-primary"
            {...register('sidebar_collapsed')}
          />
          Sidebar collapsed by default
        </label>
      </div>
    </>
  );
}
