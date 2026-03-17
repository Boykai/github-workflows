import { describe, it, expect } from 'vitest';
import { ChatMessagesResponseSchema } from './chat';

const baseMessage = {
  message_id: 'msg-1',
  session_id: 'sess-1',
  sender_type: 'user' as const,
  content: 'Hello',
  timestamp: '2024-01-01T00:00:00Z',
};

describe('ChatMessagesResponseSchema', () => {
  it('parses valid messages array', () => {
    const data = { messages: [baseMessage] };
    const result = ChatMessagesResponseSchema.parse(data);
    expect(result.messages).toHaveLength(1);
    expect(result.messages[0].content).toBe('Hello');
  });

  it('parses empty messages array', () => {
    const result = ChatMessagesResponseSchema.parse({ messages: [] });
    expect(result.messages).toEqual([]);
  });

  it('accepts all sender_type values', () => {
    for (const sender of ['user', 'assistant', 'system'] as const) {
      const data = { messages: [{ ...baseMessage, sender_type: sender }] };
      expect(ChatMessagesResponseSchema.parse(data).messages[0].sender_type).toBe(sender);
    }
  });

  it('accepts optional status field', () => {
    for (const status of ['pending', 'sent', 'failed'] as const) {
      const data = { messages: [{ ...baseMessage, status }] };
      expect(ChatMessagesResponseSchema.parse(data).messages[0].status).toBe(status);
    }
  });

  it('parses message with task_create action', () => {
    const msg = {
      ...baseMessage,
      sender_type: 'assistant' as const,
      action_type: 'task_create' as const,
      action_data: {
        proposal_id: 'prop-1',
        status: 'pending' as const,
        proposed_title: 'New task',
      },
    };
    const result = ChatMessagesResponseSchema.parse({ messages: [msg] });
    expect(result.messages[0].action_type).toBe('task_create');
  });

  it('parses message with status_update action', () => {
    const msg = {
      ...baseMessage,
      action_type: 'status_update' as const,
      action_data: { task_id: 'task-1', new_status: 'Done' },
    };
    const result = ChatMessagesResponseSchema.parse({ messages: [msg] });
    expect(result.messages[0].action_type).toBe('status_update');
  });

  it('parses message with project_select action', () => {
    const msg = {
      ...baseMessage,
      action_type: 'project_select' as const,
      action_data: { project_id: 'proj-1', project_name: 'My Project' },
    };
    const result = ChatMessagesResponseSchema.parse({ messages: [msg] });
    expect(result.messages[0].action_type).toBe('project_select');
  });

  it('parses message with issue_create action', () => {
    const msg = {
      ...baseMessage,
      action_type: 'issue_create' as const,
      action_data: {
        recommendation_id: 'rec-1',
        proposed_title: 'New feature',
        user_story: 'As a user...',
        ui_ux_description: 'A button...',
        functional_requirements: ['req-1'],
        status: 'pending' as const,
      },
    };
    const result = ChatMessagesResponseSchema.parse({ messages: [msg] });
    expect(result.messages[0].action_type).toBe('issue_create');
  });

  it('rejects invalid sender_type', () => {
    const data = { messages: [{ ...baseMessage, sender_type: 'bot' }] };
    expect(() => ChatMessagesResponseSchema.parse(data)).toThrow();
  });

  it('rejects missing required fields', () => {
    const { content: _, ...incomplete } = baseMessage;
    expect(() => ChatMessagesResponseSchema.parse({ messages: [incomplete] })).toThrow();
  });

  it('accepts all action_type enum values', () => {
    for (const at of ['task_create', 'status_update', 'project_select', 'issue_create'] as const) {
      // Just verifying the enum values don't throw when used as action_type
      // (action_data must match, but task_id satisfies the union for status_update)
      const msg = {
        ...baseMessage,
        action_type: at,
        action_data:
          at === 'status_update'
            ? { task_id: 't-1' }
            : at === 'task_create'
              ? { proposal_id: 'p-1', status: 'pending' }
              : at === 'project_select'
                ? { project_id: 'p-1', project_name: 'P' }
                : {
                    recommendation_id: 'r-1',
                    proposed_title: 'T',
                    user_story: 'U',
                    ui_ux_description: 'D',
                    functional_requirements: [],
                    status: 'pending',
                  },
      };
      expect(() => ChatMessagesResponseSchema.parse({ messages: [msg] })).not.toThrow();
    }
  });
});
