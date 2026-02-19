/**
 * Unit tests for API client service
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiError, authApi, projectsApi, tasksApi, chatApi, boardApi } from './api';

// Mock global fetch
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    json: () => Promise.resolve(data),
  };
}

function errorResponse(status: number, body?: unknown) {
  return {
    ok: false,
    status,
    statusText: 'Error',
    json: body !== undefined ? () => Promise.resolve(body) : () => Promise.reject(new Error('no json')),
  };
}

describe('ApiError', () => {
  it('should create an error with status and error properties', () => {
    const err = new ApiError(404, { error: 'Not found' });
    expect(err.status).toBe(404);
    expect(err.error).toEqual({ error: 'Not found' });
    expect(err.message).toBe('Not found');
    expect(err.name).toBe('ApiError');
    expect(err).toBeInstanceOf(Error);
  });
});

describe('request (via public APIs)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should include credentials and content-type header', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ messages: [] }));
    await chatApi.getMessages();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        credentials: 'include',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
  });

  it('should return parsed JSON on success', async () => {
    const data = { messages: [{ message_id: '1' }] };
    mockFetch.mockResolvedValue(jsonResponse(data));
    const result = await chatApi.getMessages();
    expect(result).toEqual(data);
  });

  it('should throw ApiError on non-OK response with JSON body', async () => {
    mockFetch.mockResolvedValue(errorResponse(400, { error: 'Bad request' }));
    await expect(chatApi.getMessages()).rejects.toThrow(ApiError);
    try {
      await chatApi.getMessages();
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(400);
      expect((err as ApiError).error).toEqual({ error: 'Bad request' });
    }
  });

  it('should handle JSON parse errors on error responses gracefully', async () => {
    mockFetch.mockResolvedValue(errorResponse(500));
    await expect(chatApi.getMessages()).rejects.toThrow(ApiError);
    try {
      await chatApi.getMessages();
    } catch (err) {
      expect((err as ApiError).status).toBe(500);
      expect((err as ApiError).error.error).toContain('HTTP 500');
    }
  });

  it('should return empty object for 204 responses', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 204,
      statusText: 'No Content',
      json: () => Promise.reject(new Error('no body')),
    });
    const result = await chatApi.cancelProposal('p1');
    expect(result).toEqual({});
  });
});

describe('authApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('login() sets window.location.href', () => {
    authApi.login();
    expect(window.location.href).toContain('/auth/github');
  });

  it('setSessionFromToken() calls POST with session token', async () => {
    const user = { github_user_id: '1', github_username: 'test' };
    mockFetch.mockResolvedValue(jsonResponse(user));
    const result = await authApi.setSessionFromToken('my-token');
    expect(result).toEqual(user);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/session?session_token=my-token'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('getCurrentUser() calls GET /auth/me', async () => {
    const user = { github_user_id: '1', github_username: 'test' };
    mockFetch.mockResolvedValue(jsonResponse(user));
    const result = await authApi.getCurrentUser();
    expect(result).toEqual(user);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/me'),
      expect.objectContaining({ credentials: 'include' })
    );
  });

  it('logout() calls POST /auth/logout', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ message: 'Logged out' }));
    const result = await authApi.logout();
    expect(result).toEqual({ message: 'Logged out' });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/logout'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});

describe('projectsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('list() fetches projects without refresh by default', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ projects: [] }));
    await projectsApi.list();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/projects$/),
      expect.any(Object)
    );
  });

  it('list(true) adds ?refresh=true', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ projects: [] }));
    await projectsApi.list(true);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/projects?refresh=true'),
      expect.any(Object)
    );
  });

  it('get() fetches a single project', async () => {
    const project = { project_id: 'PVT_1', name: 'Test' };
    mockFetch.mockResolvedValue(jsonResponse(project));
    const result = await projectsApi.get('PVT_1');
    expect(result).toEqual(project);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/projects/PVT_1'),
      expect.any(Object)
    );
  });

  it('select() calls POST to select project', async () => {
    const user = { github_user_id: '1', selected_project_id: 'PVT_1' };
    mockFetch.mockResolvedValue(jsonResponse(user));
    const result = await projectsApi.select('PVT_1');
    expect(result).toEqual(user);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/projects/PVT_1/select'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});

describe('tasksApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('listByProject() fetches tasks for a project', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ tasks: [] }));
    await tasksApi.listByProject('PVT_1');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/projects/PVT_1/tasks'),
      expect.any(Object)
    );
  });

  it('create() sends POST with task data', async () => {
    const task = { task_id: 'T1', title: 'New Task' };
    mockFetch.mockResolvedValue(jsonResponse(task));
    const result = await tasksApi.create({
      project_id: 'PVT_1',
      title: 'New Task',
      description: 'Desc',
    });
    expect(result).toEqual(task);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/tasks'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ project_id: 'PVT_1', title: 'New Task', description: 'Desc' }),
      })
    );
  });

  it('updateStatus() sends PATCH with status', async () => {
    const task = { task_id: 'T1', status: 'Done' };
    mockFetch.mockResolvedValue(jsonResponse(task));
    const result = await tasksApi.updateStatus('T1', 'Done');
    expect(result).toEqual(task);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/tasks/T1/status'),
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ status: 'Done' }),
      })
    );
  });
});

describe('chatApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('getMessages() fetches chat messages', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ messages: [] }));
    const result = await chatApi.getMessages();
    expect(result).toEqual({ messages: [] });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/messages'),
      expect.any(Object)
    );
  });

  it('clearMessages() sends DELETE', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ message: 'Cleared' }));
    await chatApi.clearMessages();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/messages'),
      expect.objectContaining({ method: 'DELETE' })
    );
  });

  it('sendMessage() sends POST with content', async () => {
    const msg = { message_id: '1', content: 'Hello' };
    mockFetch.mockResolvedValue(jsonResponse(msg));
    const result = await chatApi.sendMessage({ content: 'Hello' });
    expect(result).toEqual(msg);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/messages'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ content: 'Hello' }),
      })
    );
  });

  it('confirmProposal() sends POST with data', async () => {
    const proposal = { proposal_id: 'p1', status: 'confirmed' };
    mockFetch.mockResolvedValue(jsonResponse(proposal));
    const result = await chatApi.confirmProposal('p1', { edited_title: 'New Title' });
    expect(result).toEqual(proposal);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/proposals/p1/confirm'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ edited_title: 'New Title' }),
      })
    );
  });

  it('confirmProposal() sends empty object when no data', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ proposal_id: 'p1' }));
    await chatApi.confirmProposal('p1');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/proposals/p1/confirm'),
      expect.objectContaining({ body: JSON.stringify({}) })
    );
  });

  it('cancelProposal() sends DELETE', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 204,
      statusText: 'No Content',
      json: () => Promise.reject(new Error('no body')),
    });
    await chatApi.cancelProposal('p1');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/proposals/p1'),
      expect.objectContaining({ method: 'DELETE' })
    );
  });
});

describe('boardApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('listProjects() fetches board projects', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ projects: [] }));
    await boardApi.listProjects();
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/board\/projects$/),
      expect.any(Object)
    );
  });

  it('listProjects(true) adds ?refresh=true', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ projects: [] }));
    await boardApi.listProjects(true);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/board/projects?refresh=true'),
      expect.any(Object)
    );
  });

  it('getBoardData() fetches board data for a project', async () => {
    const data = { project: {}, columns: [] };
    mockFetch.mockResolvedValue(jsonResponse(data));
    const result = await boardApi.getBoardData('PVT_1');
    expect(result).toEqual(data);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/board\/projects\/PVT_1$/),
      expect.any(Object)
    );
  });

  it('getBoardData() with refresh adds ?refresh=true', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ project: {}, columns: [] }));
    await boardApi.getBoardData('PVT_1', true);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/board/projects/PVT_1?refresh=true'),
      expect.any(Object)
    );
  });
});
