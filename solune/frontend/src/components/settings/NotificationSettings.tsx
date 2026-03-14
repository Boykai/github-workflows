import type { UseFormReturn } from 'react-hook-form';
import type { GlobalFormState } from './globalSettingsSchema';

interface NotificationSettingsProps {
  form: UseFormReturn<GlobalFormState>;
}

export function NotificationSettings({ form }: NotificationSettingsProps) {
  const { register } = form;

  return (
    <>
      <h4 className="text-sm font-semibold text-foreground mt-4 border-b border-border pb-2">
        Notifications
      </h4>
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
          <input
            type="checkbox"
            className="celestial-focus w-4 h-4 rounded border-input text-primary"
            {...register('task_status_change')}
          />{' '}
          Task status changes
        </label>
      </div>
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
          <input
            type="checkbox"
            className="celestial-focus w-4 h-4 rounded border-input text-primary"
            {...register('agent_completion')}
          />{' '}
          Agent completion
        </label>
      </div>
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
          <input
            type="checkbox"
            className="celestial-focus w-4 h-4 rounded border-input text-primary"
            {...register('new_recommendation')}
          />{' '}
          New recommendations
        </label>
      </div>
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
          <input
            type="checkbox"
            className="celestial-focus w-4 h-4 rounded border-input text-primary"
            {...register('chat_mention')}
          />{' '}
          Chat mentions
        </label>
      </div>
    </>
  );
}
