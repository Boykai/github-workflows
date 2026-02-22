/**
 * Test setup for Vitest
 */
import '@testing-library/react';
import { vi, type Mock } from 'vitest';

// ─── crypto.randomUUID stub ──────────────────────────────────────────────
// happy-dom may not implement crypto.randomUUID; stub once globally.
if (typeof globalThis.crypto === 'undefined') {
  // @ts-expect-error - partial crypto shim
  globalThis.crypto = {};
}
if (typeof globalThis.crypto.randomUUID !== 'function') {
  let _counter = 0;
  globalThis.crypto.randomUUID = () =>
    `00000000-0000-4000-8000-${String(++_counter).padStart(12, '0')}` as `${string}-${string}-${string}-${string}-${string}`;
}

// ─── Mock WebSocket ──────────────────────────────────────────────────────

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;

  constructor(public url: string) {
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 10);
  }

  send(_data: string) {
    // Mock send
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }
}

// @ts-expect-error - Override global WebSocket
global.WebSocket = MockWebSocket;

// ─── Mock window.location / window.history ───────────────────────────────

Object.defineProperty(window, 'location', {
  value: {
    protocol: 'http:',
    host: 'localhost:5173',
    href: 'http://localhost:5173/',
    pathname: '/',
    search: '',
    hash: '',
  },
  writable: true,
});

Object.defineProperty(window, 'history', {
  value: {
    replaceState: vi.fn(),
    pushState: vi.fn(),
  },
  writable: true,
});

// ─── createMockApi() — typed API mock factory ────────────────────────────
// Produces a deep mock of every namespace in `@/services/api` so tests can
// `vi.mock('@/services/api', () => createMockApi())` in one line.

export interface MockApiShape {
  ApiError: typeof import('@/services/api').ApiError;
  authApi: {
    login: Mock;
    setSessionFromToken: Mock;
    getCurrentUser: Mock;
    logout: Mock;
  };
  projectsApi: {
    list: Mock;
    get: Mock;
    select: Mock;
  };
  tasksApi: {
    listByProject: Mock;
    create: Mock;
    updateStatus: Mock;
  };
  chatApi: {
    getMessages: Mock;
    clearMessages: Mock;
    sendMessage: Mock;
    confirmProposal: Mock;
    cancelProposal: Mock;
  };
  boardApi: {
    listProjects: Mock;
    getBoardData: Mock;
  };
  settingsApi: {
    getUserSettings: Mock;
    updateUserSettings: Mock;
    getGlobalSettings: Mock;
    updateGlobalSettings: Mock;
    getProjectSettings: Mock;
    updateProjectSettings: Mock;
  };
}

/**
 * Create a fully-mocked version of the API service module.
 *
 * Usage in a test file:
 * ```ts
 * import { createMockApi } from '@/test/setup';
 * vi.mock('@/services/api', () => createMockApi());
 * ```
 */
export function createMockApi(): MockApiShape {
  return {
    ApiError: class extends Error {
      constructor(
        public status: number,
        public error: { error: string },
      ) {
        super(error.error);
        this.name = 'ApiError';
      }
    },
    authApi: {
      login: vi.fn(),
      setSessionFromToken: vi.fn(),
      getCurrentUser: vi.fn(),
      logout: vi.fn(),
    },
    projectsApi: {
      list: vi.fn(),
      get: vi.fn(),
      select: vi.fn(),
    },
    tasksApi: {
      listByProject: vi.fn(),
      create: vi.fn(),
      updateStatus: vi.fn(),
    },
    chatApi: {
      getMessages: vi.fn(),
      clearMessages: vi.fn(),
      sendMessage: vi.fn(),
      confirmProposal: vi.fn(),
      cancelProposal: vi.fn(),
    },
    boardApi: {
      listProjects: vi.fn(),
      getBoardData: vi.fn(),
    },
    settingsApi: {
      getUserSettings: vi.fn(),
      updateUserSettings: vi.fn(),
      getGlobalSettings: vi.fn(),
      updateGlobalSettings: vi.fn(),
      getProjectSettings: vi.fn(),
      updateProjectSettings: vi.fn(),
    },
  };
}
