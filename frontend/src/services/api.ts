/**
 * API client service for Tim is Awesome.
 * Provides typed fetch wrapper with error handling.
 */

import type {
  APIError,
  AvailableAgent,
  ChatMessage,
  ChatMessageRequest,
  ChatMessagesResponse,
  AITaskProposal,
  ProposalConfirmRequest,
  Project,
  ProjectListResponse,
  Task,
  TaskCreateRequest,
  TaskListResponse,
  User,
  BoardProjectListResponse,
  BoardDataResponse,
  EffectiveUserSettings,
  UserPreferencesUpdate,
  GlobalSettings,
  GlobalSettingsUpdate,
  EffectiveProjectSettings,
  ProjectSettingsUpdate,
  WorkflowResult,
  WorkflowConfiguration,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    public error: APIError
  ) {
    super(error.error);
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error: APIError = await response.json().catch(() => ({
      error: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new ApiError(response.status, error);
  }

  // Handle empty responses (204 No Content)
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// ============ Auth API ============

export const authApi = {
  /**
   * Get GitHub OAuth login URL and redirect.
   * Goes through the nginx proxy to maintain same-origin for cookies.
   */
  login(): void {
    // Redirect through nginx proxy for OAuth flow
    // The backend will redirect to GitHub, then back to callback, then to frontend
    window.location.href = `${API_BASE_URL}/auth/github`;
  },

  /**
   * Exchange session token for cookie.
   * Called after OAuth callback to set cookie via the proxy.
   */
  setSessionFromToken(sessionToken: string): Promise<User> {
    return request<User>(`/auth/session?session_token=${sessionToken}`, {
      method: 'POST',
    });
  },

  /**
   * Get current authenticated user.
   */
  getCurrentUser(): Promise<User> {
    return request<User>('/auth/me');
  },

  /**
   * Logout current user.
   */
  logout(): Promise<{ message: string }> {
    return request<{ message: string }>('/auth/logout', { method: 'POST' });
  },
};

// ============ Projects API ============

export const projectsApi = {
  /**
   * List all accessible GitHub Projects.
   */
  list(refresh = false): Promise<ProjectListResponse> {
    const params = refresh ? '?refresh=true' : '';
    return request<ProjectListResponse>(`/projects${params}`);
  },

  /**
   * Get project details including items.
   */
  get(projectId: string): Promise<Project> {
    return request<Project>(`/projects/${projectId}`);
  },

  /**
   * Select a project as the active project.
   */
  select(projectId: string): Promise<User> {
    return request<User>(`/projects/${projectId}/select`, {
      method: 'POST',
    });
  },
};

// ============ Tasks API ============

export const tasksApi = {
  /**
   * List tasks for a project.
   */
  listByProject(projectId: string): Promise<TaskListResponse> {
    return request<TaskListResponse>(`/projects/${projectId}/tasks`);
  },

  /**
   * Create a new task.
   */
  create(data: TaskCreateRequest): Promise<Task> {
    return request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update task status.
   */
  updateStatus(taskId: string, status: string): Promise<Task> {
    return request<Task>(`/tasks/${taskId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },
};

// ============ Chat API ============

export const chatApi = {
  /**
   * Get chat messages for current session.
   */
  getMessages(): Promise<ChatMessagesResponse> {
    return request<ChatMessagesResponse>('/chat/messages');
  },

  /**
   * Clear all chat messages for current session.
   */
  clearMessages(): Promise<{ message: string }> {
    return request<{ message: string }>('/chat/messages', { method: 'DELETE' });
  },

  /**
   * Send a chat message.
   */
  sendMessage(data: ChatMessageRequest): Promise<ChatMessage> {
    return request<ChatMessage>('/chat/messages', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Confirm an AI task proposal.
   */
  confirmProposal(
    proposalId: string,
    data?: ProposalConfirmRequest
  ): Promise<AITaskProposal> {
    return request<AITaskProposal>(`/chat/proposals/${proposalId}/confirm`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });
  },

  /**
   * Cancel an AI task proposal.
   */
  cancelProposal(proposalId: string): Promise<void> {
    return request<void>(`/chat/proposals/${proposalId}`, {
      method: 'DELETE',
    });
  },
};

// ============ Board API ============

export const boardApi = {
  /**
   * List available projects for board display.
   */
  listProjects(refresh = false): Promise<BoardProjectListResponse> {
    const params = refresh ? '?refresh=true' : '';
    return request<BoardProjectListResponse>(`/board/projects${params}`);
  },

  /**
   * Get board data for a specific project.
   */
  getBoardData(projectId: string, refresh = false): Promise<BoardDataResponse> {
    const params = refresh ? '?refresh=true' : '';
    return request<BoardDataResponse>(`/board/projects/${projectId}${params}`);
  },
};

// ============ Settings API ============

export const settingsApi = {
  /**
   * Get authenticated user's effective settings (merged with global defaults).
   */
  getUserSettings(): Promise<EffectiveUserSettings> {
    return request<EffectiveUserSettings>('/settings/user');
  },

  /**
   * Update authenticated user's preferences (partial update).
   */
  updateUserSettings(data: UserPreferencesUpdate): Promise<EffectiveUserSettings> {
    return request<EffectiveUserSettings>('/settings/user', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get global/instance-level settings.
   */
  getGlobalSettings(): Promise<GlobalSettings> {
    return request<GlobalSettings>('/settings/global');
  },

  /**
   * Update global/instance-level settings (partial update).
   */
  updateGlobalSettings(data: GlobalSettingsUpdate): Promise<GlobalSettings> {
    return request<GlobalSettings>('/settings/global', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get effective project settings for authenticated user.
   */
  getProjectSettings(projectId: string): Promise<EffectiveProjectSettings> {
    return request<EffectiveProjectSettings>(`/settings/project/${projectId}`);
  },

  /**
   * Update per-project settings for authenticated user (partial update).
   */
  updateProjectSettings(
    projectId: string,
    data: ProjectSettingsUpdate
  ): Promise<EffectiveProjectSettings> {
    return request<EffectiveProjectSettings>(`/settings/project/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

// ============ Workflow API ============

export const workflowApi = {
  /**
   * Confirm an AI-generated issue recommendation.
   */
  confirmRecommendation(recommendationId: string): Promise<WorkflowResult> {
    return request<WorkflowResult>(
      `/workflow/recommendations/${recommendationId}/confirm`,
      { method: 'POST' },
    );
  },

  /**
   * Reject an AI-generated issue recommendation.
   */
  rejectRecommendation(recommendationId: string): Promise<void> {
    return request<void>(
      `/workflow/recommendations/${recommendationId}/reject`,
      { method: 'POST' },
    );
  },

  /**
   * Get the current workflow configuration.
   */
  getConfig(): Promise<WorkflowConfiguration> {
    return request<WorkflowConfiguration>('/workflow/config');
  },

  /**
   * Update workflow configuration.
   */
  updateConfig(config: WorkflowConfiguration): Promise<WorkflowConfiguration> {
    return request<WorkflowConfiguration>('/workflow/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },

  /**
   * List available agents.
   */
  listAgents(): Promise<{ agents: AvailableAgent[] }> {
    return request<{ agents: AvailableAgent[] }>('/workflow/agents');
  },
};
