import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook } from '@testing-library/react';
import { test, fc } from '@fast-check/vitest';
import React from 'react';
import { describe, expect, vi } from 'vitest';

import { useRealTimeSync } from '@/hooks/useRealTimeSync';
import { initialState, pipelineReducer } from '@/hooks/usePipelineReducer';
import { ProjectListResponseSchema } from '@/services/schemas/projects';

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static OPEN = 1;

  readyState = FakeWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(_url: string) {
    FakeWebSocket.instances.push(this);
  }

  close() {
    this.onclose?.();
  }

  emit(data: string) {
    this.onmessage?.({ data } as MessageEvent);
  }
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('JSON.parse fuzzing', () => {
  test.prop([fc.string()])('pipelineReducer DISCARD_EDITING never throws for arbitrary snapshots', (snapshot) => {
    expect(() =>
      pipelineReducer(
        { ...initialState, savedSnapshot: snapshot, pipeline: null },
        { type: 'DISCARD_EDITING' }
      )
    ).not.toThrow();
  });

  test.prop([fc.string()])('useRealTimeSync message handler never throws for arbitrary websocket payloads', (raw) => {
    vi.stubGlobal('WebSocket', FakeWebSocket as unknown as typeof WebSocket);
    FakeWebSocket.instances = [];

    const { unmount } = renderHook(() => useRealTimeSync('PVT_test'), { wrapper: createWrapper() });
    const instance = FakeWebSocket.instances[0];
    expect(instance).toBeDefined();

    expect(() => instance.emit(raw)).not.toThrow();

    unmount();
    vi.unstubAllGlobals();
  });

  test.prop([fc.constant({})])('project schema rejects valid-but-empty objects gracefully', (emptyObject) => {
    expect(() => ProjectListResponseSchema.parse(emptyObject)).toThrow();
  });
});