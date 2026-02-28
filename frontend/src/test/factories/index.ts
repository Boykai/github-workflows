/**
 * Shared test data factories for frontend tests.
 *
 * Each factory returns a valid object with sensible defaults that can
 * be overridden via a partial parameter object.
 */

import type {
  ChatMessage,
  Project,
  StatusColumn,
  Task,
  User,
} from '@/types';

// ── User & Auth ────────────────────────────────────────────────────────────

export function createMockUser(overrides: Partial<User> = {}): User {
  return {
    github_user_id: '12345',
    github_username: 'testuser',
    github_avatar_url: 'https://avatar.example.com',
    selected_project_id: undefined,
    ...overrides,
  };
}

// ── Projects ───────────────────────────────────────────────────────────────

export function createMockStatusColumn(
  overrides: Partial<StatusColumn> = {},
): StatusColumn {
  return {
    field_id: 'PVTSSF_1',
    name: 'Todo',
    option_id: 'opt1',
    color: 'GRAY',
    ...overrides,
  };
}

export function createMockProject(overrides: Partial<Project> = {}): Project {
  return {
    project_id: 'PVT_123',
    owner_id: 'owner-123',
    owner_login: 'testuser',
    name: 'Test Project',
    type: 'user',
    url: 'https://github.com/users/testuser/projects/1',
    description: undefined,
    status_columns: [
      createMockStatusColumn(),
      createMockStatusColumn({ name: 'Done', option_id: 'opt2', color: 'GREEN' }),
    ],
    item_count: 0,
    cached_at: new Date().toISOString(),
    ...overrides,
  };
}

// ── Tasks ──────────────────────────────────────────────────────────────────

export function createMockTask(overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'TASK_1',
    project_id: 'PVT_123',
    github_item_id: 'item-123',
    title: 'Test Task',
    status: 'Todo',
    status_option_id: 'opt1',
    assignees: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

// ── Chat Messages ──────────────────────────────────────────────────────────

export function createMockChatMessage(
  overrides: Partial<ChatMessage> = {},
): ChatMessage {
  return {
    message_id: 'msg-1',
    session_id: 'session-1',
    sender_type: 'user',
    content: 'Hello, world!',
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

// ── Settings ───────────────────────────────────────────────────────────────

export interface MockSettings {
  ai: { provider: string; model: string; temperature: number };
  display: { theme: string; default_view: string; sidebar_collapsed: boolean };
  workflow: { auto_assign: boolean; default_status: string; polling_interval: number };
  notifications: { enabled: boolean; sound: boolean };
}

export function createMockSettings(
  overrides: Partial<MockSettings> = {},
): MockSettings {
  return {
    ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7 },
    display: { theme: 'dark', default_view: 'board', sidebar_collapsed: false },
    workflow: {
      auto_assign: true,
      default_status: 'Todo',
      polling_interval: 15,
    },
    notifications: { enabled: true, sound: false },
    ...overrides,
  };
}
