/**
 * Notification Preferences settings section.
 *
 * Four toggle switches for per-event notification control.
 */

import { useState, useEffect } from 'react';
import { SettingsSection } from './SettingsSection';
import type {
  NotificationPreferences as NotificationPreferencesType,
  UserPreferencesUpdate,
} from '@/types';

interface NotificationPreferencesProps {
  settings: NotificationPreferencesType;
  onSave: (update: UserPreferencesUpdate) => Promise<void>;
}

export function NotificationPreferences({ settings, onSave }: NotificationPreferencesProps) {
  const [taskStatusChange, setTaskStatusChange] = useState(settings.task_status_change);
  const [agentCompletion, setAgentCompletion] = useState(settings.agent_completion);
  const [newRecommendation, setNewRecommendation] = useState(settings.new_recommendation);
  const [chatMention, setChatMention] = useState(settings.chat_mention);

  useEffect(() => {
    setTaskStatusChange(settings.task_status_change);
    setAgentCompletion(settings.agent_completion);
    setNewRecommendation(settings.new_recommendation);
    setChatMention(settings.chat_mention);
  }, [
    settings.task_status_change,
    settings.agent_completion,
    settings.new_recommendation,
    settings.chat_mention,
  ]);

  const isDirty =
    taskStatusChange !== settings.task_status_change ||
    agentCompletion !== settings.agent_completion ||
    newRecommendation !== settings.new_recommendation ||
    chatMention !== settings.chat_mention;

  const handleSave = async () => {
    await onSave({
      notifications: {
        task_status_change: taskStatusChange,
        agent_completion: agentCompletion,
        new_recommendation: newRecommendation,
        chat_mention: chatMention,
      },
    });
  };

  return (
    <SettingsSection
      title="Notification Preferences"
      description="Control which events trigger notifications."
      isDirty={isDirty}
      onSave={handleSave}
    >
      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={taskStatusChange}
            onChange={(e) => setTaskStatusChange(e.target.checked)}
          />
          Task status changes
        </label>
      </div>

      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={agentCompletion}
            onChange={(e) => setAgentCompletion(e.target.checked)}
          />
          Agent completion
        </label>
      </div>

      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={newRecommendation}
            onChange={(e) => setNewRecommendation(e.target.checked)}
          />
          New recommendations
        </label>
      </div>

      <div className="settings-field">
        <label>
          <input
            type="checkbox"
            checked={chatMention}
            onChange={(e) => setChatMention(e.target.checked)}
          />
          Chat mentions
        </label>
      </div>
    </SettingsSection>
  );
}
