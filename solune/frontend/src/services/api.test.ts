import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  ApiError,
  onAuthExpired,
  authApi,
  projectsApi,
  tasksApi,
  chatApi,
  boardApi,
  settingsApi,
  workflowApi,
  metadataApi,
  signalApi,
  mcpApi,
  cleanupApi,
  choresApi,
  agentsApi,
  pipelinesApi,
  modelsApi,
  toolsApi,
  agentToolsApi,
  appsApi,
} from './api';

// ── Helpers ────────────────────────────────────────────────────────────

const mockFetch = vi.fn();

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    json: () => Promise.resolve(body),
    headers: new Headers(),
  } as unknown as Response;
}

// ── Setup ──────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.restoreAllMocks();
  global.fetch = mockFetch;
  mockFetch.mockReset();
  // Clear cookies so CSRF logic starts clean
  Object.defineProperty(document, 'cookie', { value: '', writable: true });
});

// ── Exports exist ──────────────────────────────────────────────────────

describe('api module exports', () => {
  it('exports ApiError as a class', () => {
    expect(ApiError).toBeDefined();
    expect(typeof ApiError).toBe('function');
    const err = new ApiError(404, { error: 'not found' });
    expect(err).toBeInstanceOf(Error);
    expect(err.status).toBe(404);
    expect(err.message).toBe('not found');
  });

  it('exports onAuthExpired as a function', () => {
    expect(typeof onAuthExpired).toBe('function');
  });

  const apiExports: Array<[string, object]> = [
    ['authApi', authApi],
    ['projectsApi', projectsApi],
    ['tasksApi', tasksApi],
    ['chatApi', chatApi],
    ['boardApi', boardApi],
    ['settingsApi', settingsApi],
    ['workflowApi', workflowApi],
    ['metadataApi', metadataApi],
    ['signalApi', signalApi],
    ['mcpApi', mcpApi],
    ['cleanupApi', cleanupApi],
    ['choresApi', choresApi],
    ['agentsApi', agentsApi],
    ['pipelinesApi', pipelinesApi],
    ['modelsApi', modelsApi],
    ['toolsApi', toolsApi],
    ['agentToolsApi', agentToolsApi],
    ['appsApi', appsApi],
  ];

  it.each(apiExports)('exports %s as an object', (_name, api) => {
    expect(api).toBeDefined();
    expect(typeof api).toBe('object');
  });
});

// ── URL / header construction ──────────────────────────────────────────

describe('request URL and header construction', () => {
  it('projectsApi.list builds GET /projects', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ projects: [] }));
    await projectsApi.list();

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/projects');
    expect(opts.method ?? 'GET').toBe('GET');
    expect(opts.credentials).toBe('include');
    expect(opts.headers['Content-Type']).toBe('application/json');
  });

  it('projectsApi.list(true) appends ?refresh=true', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ projects: [] }));
    await projectsApi.list(true);

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain('?refresh=true');
  });

  it('tasksApi.create sends POST with JSON body', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ id: '1', title: 't' }));
    await tasksApi.create({ title: 'new task', project_id: 'p1' } as never);

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/tasks');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toHaveProperty('title', 'new task');
  });

  it('appsApi.delete sends DELETE /apps/:name', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}, 204));
    await appsApi.delete('my-app');

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/apps/my-app');
    expect(opts.method).toBe('DELETE');
  });

  it('appsApi.list appends the status query when provided', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));
    await appsApi.list('active');

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/apps?status=active');
    expect(opts.method ?? 'GET').toBe('GET');
  });

  it('appsApi.start sends POST /apps/:name/start', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ status: 'active' }));
    await appsApi.start('my-app');

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/apps/my-app/start');
    expect(opts.method).toBe('POST');
  });

  it('appsApi.stop sends POST /apps/:name/stop', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ status: 'stopped' }));
    await appsApi.stop('my-app');

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/apps/my-app/stop');
    expect(opts.method).toBe('POST');
  });

  it('attaches CSRF token header on state-changing requests', async () => {
    document.cookie = 'csrf_token=abc123';
    mockFetch.mockResolvedValueOnce(jsonResponse({ message: 'ok' }));
    await authApi.logout();

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers['X-CSRF-Token']).toBe('abc123');
  });

  it('does not attach CSRF header on GET requests', async () => {
    document.cookie = 'csrf_token=abc123';
    mockFetch.mockResolvedValueOnce(jsonResponse({ projects: [] }));
    await projectsApi.list();

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers['X-CSRF-Token']).toBeUndefined();
  });
});

// ── Network error handling ─────────────────────────────────────────────

describe('network error handling', () => {
  it('projectsApi.list rejects when fetch throws', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await expect(projectsApi.list()).rejects.toThrow('Failed to fetch');
  });

  it('chatApi.getMessages rejects when fetch throws', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Network error'));
    await expect(chatApi.getMessages()).rejects.toThrow('Network error');
  });

  it('appsApi.list rejects when fetch throws', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Offline'));
    await expect(appsApi.list()).rejects.toThrow('Offline');
  });
});

// ── HTTP error responses ───────────────────────────────────────────────

describe('HTTP error responses', () => {
  it('throws ApiError on non-ok response with error body', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ error: 'forbidden' }, 403));
    await expect(projectsApi.get('p1')).rejects.toThrow(ApiError);

    try {
      mockFetch.mockResolvedValueOnce(jsonResponse({ error: 'forbidden' }, 403));
      await projectsApi.get('p1');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).status).toBe(403);
    }
  });

  it('throws ApiError with fallback message when body is not JSON', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.reject(new Error('invalid json')),
      headers: new Headers(),
    } as unknown as Response);

    await expect(settingsApi.getUserSettings()).rejects.toThrow(ApiError);
  });

  it('handles 204 No Content without throwing', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}, 204));
    const result = await appsApi.delete('x');
    expect(result).toEqual({});
  });

  it('merges rate_limit details into the ApiError payload', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse(
        {
          detail: 'Slow down',
          details: { source: 'github' },
          rate_limit: { remaining: 0, reset_at: 'later' },
        },
        429
      )
    );

    await expect(projectsApi.list()).rejects.toMatchObject({
      status: 429,
      error: {
        error: 'Slow down',
        details: {
          source: 'github',
          rate_limit: { remaining: 0, reset_at: 'later' },
        },
      },
    });
  });
});

// ── Auth expiry listener ───────────────────────────────────────────────

describe('onAuthExpired', () => {
  it('fires listeners on 401 from a non-auth endpoint', async () => {
    const listener = vi.fn();
    const unsub = onAuthExpired(listener);

    mockFetch.mockResolvedValueOnce(jsonResponse({ error: 'token expired' }, 401));
    await expect(projectsApi.list()).rejects.toThrow(ApiError);
    expect(listener).toHaveBeenCalledOnce();

    unsub();
  });

  it('unsubscribe prevents future calls', async () => {
    const listener = vi.fn();
    const unsub = onAuthExpired(listener);
    unsub();

    mockFetch.mockResolvedValueOnce(jsonResponse({ error: 'expired' }, 401));
    await expect(projectsApi.list()).rejects.toThrow(ApiError);
    expect(listener).not.toHaveBeenCalled();
  });

  it('does not fire listeners for auth endpoint 401 responses', async () => {
    const listener = vi.fn();
    const unsub = onAuthExpired(listener);

    mockFetch.mockResolvedValueOnce(jsonResponse({ error: 'expired' }, 401));
    await expect(authApi.getCurrentUser()).rejects.toThrow(ApiError);

    expect(listener).not.toHaveBeenCalled();
    unsub();
  });

  it('continues notifying remaining listeners when one throws', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const throwingListener = vi.fn(() => {
      throw new Error('listener boom');
    });
    const healthyListener = vi.fn();
    const unsubThrowing = onAuthExpired(throwingListener);
    const unsubHealthy = onAuthExpired(healthyListener);

    mockFetch.mockResolvedValueOnce(jsonResponse({ error: 'expired' }, 401));
    await expect(projectsApi.list()).rejects.toThrow(ApiError);

    expect(throwingListener).toHaveBeenCalledOnce();
    expect(healthyListener).toHaveBeenCalledOnce();
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Auth-expired listener threw:',
      expect.any(Error)
    );

    unsubThrowing();
    unsubHealthy();
    consoleErrorSpy.mockRestore();
  });
});
