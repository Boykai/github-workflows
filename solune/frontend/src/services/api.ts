/**
 * API client service for Solune.
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
  ModelsResponse,
  WorkflowResult,
  WorkflowConfiguration,
  SignalConnection,
  SignalLinkResponse,
  SignalLinkStatusResponse,
  SignalPreferences,
  SignalPreferencesUpdate,
  SignalBannersResponse,
  McpConfiguration,
  McpConfigurationListResponse,
  McpConfigurationCreate,
  CleanupPreflightResponse,
  CleanupExecuteRequest,
  CleanupExecuteResponse,
  CleanupHistoryResponse,
  Chore,
  ChoreCreate,
  ChoreTemplate,
  ChoreUpdate,
  ChoreStatus,
  ChoreTriggerResult,
  ChoreChatMessage,
  ChoreChatResponse,
  ChoreInlineUpdate,
  ChoreInlineUpdateResponse,
  ChoreCreateWithConfirmation,
  ChoreCreateResponse,
  EvaluateChoreTriggersResponse,
  ScheduleType,
  RepositoryMetadata,
  PipelineConfig,
  PipelineConfigCreate,
  PipelineConfigUpdate,
  PipelineConfigListResponse,
  PipelineIssueLaunchRequest,
  AIModel,
  PresetSeedResult,
  ProjectPipelineAssignment,
  McpToolConfig,
  McpToolConfigCreate,
  McpToolConfigUpdate,
  McpToolConfigListResponse,
  McpToolSyncResult,
  RepoMcpConfigResponse,
  RepoMcpServerConfig,
  RepoMcpServerUpdate,
  McpPresetListResponse,
  ToolChip,
  ToolDeleteResult,
  FileUploadResponse,
  PipelineStateInfo,
  PaginatedResponse,
  ActivityEvent,
} from '@/types';
import { BoardDataResponseSchema } from '@/services/schemas/board';
import { ChatMessagesResponseSchema } from '@/services/schemas/chat';
import { PipelineStateInfoSchema } from '@/services/schemas/pipeline';
import { ProjectListResponseSchema } from '@/services/schemas/projects';
import { EffectiveUserSettingsSchema } from '@/services/schemas/settings';
import { validateResponse } from '@/services/schemas/validate';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const STATE_CHANGING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

/** Read the CSRF double-submit cookie set by the backend. */
function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public error: APIError
  ) {
    super(error.error);
    this.name = 'ApiError';
  }
}

/**
 * Listeners notified when any API call receives a 401 response.
 * Used by useAuth to auto-logout when the session/token expires.
 */
type AuthExpiredListener = () => void;
const authExpiredListeners = new Set<AuthExpiredListener>();

export function onAuthExpired(listener: AuthExpiredListener): () => void {
  authExpiredListeners.add(listener);
  return () => {
    authExpiredListeners.delete(listener);
  };
}

function normalizeApiError(response: Response, payload: unknown): APIError {
  const fallbackMessage = `HTTP ${response.status}: ${response.statusText}`;

  if (!payload || typeof payload !== 'object') {
    return { error: fallbackMessage };
  }

  const raw = payload as Record<string, unknown>;
  const details =
    raw.details && typeof raw.details === 'object'
      ? { ...(raw.details as Record<string, unknown>) }
      : undefined;

  if (raw.rate_limit && typeof raw.rate_limit === 'object') {
    const mergedDetails = details ?? {};
    mergedDetails.rate_limit = raw.rate_limit;

    return {
      error:
        typeof raw.error === 'string'
          ? raw.error
          : typeof raw.detail === 'string'
            ? raw.detail
            : fallbackMessage,
      details: mergedDetails,
    };
  }

  return {
    error:
      typeof raw.error === 'string'
        ? raw.error
        : typeof raw.detail === 'string'
          ? raw.detail
          : fallbackMessage,
    details,
  };
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const method = (options.method ?? 'GET').toUpperCase();
  const csrfHeaders: Record<string, string> = {};
  if (STATE_CHANGING_METHODS.has(method)) {
    const token = getCsrfToken();
    if (token) {
      csrfHeaders['X-CSRF-Token'] = token;
    }
  }

  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...csrfHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const error = normalizeApiError(response, payload);

    // Auto-logout: if any non-auth endpoint returns 401, the session or
    // GitHub token has expired.  Notify listeners (useAuth) so the UI
    // clears cached credentials and shows the login screen.
    if (response.status === 401 && !endpoint.startsWith('/auth/')) {
      // Notify auth-expired subscribers (e.g. useAuth) so the UI can
      // clear cached credentials.  Each listener is wrapped in try/catch
      // so a throwing subscriber cannot prevent remaining listeners from
      // running or mask the ApiError that is thrown below.
      authExpiredListeners.forEach((fn) => {
        try {
          fn();
        } catch (listenerError) {
          console.error('Auth-expired listener threw:', listenerError);
        }
      });
    }

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
  async list(refresh = false): Promise<ProjectListResponse> {
    const params = refresh ? '?refresh=true' : '';
    const data = await request<ProjectListResponse>(`/projects${params}`);
    return validateResponse(ProjectListResponseSchema, data, 'projectsApi.list');
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

  /**
   * Create a standalone GitHub Project V2.
   */
  create(data: CreateProjectRequest): Promise<CreateProjectResponse> {
    return request<CreateProjectResponse>('/projects/create', {
      method: 'POST',
      body: JSON.stringify(data),
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
  async getMessages(): Promise<ChatMessagesResponse> {
    const data = await request<ChatMessagesResponse>('/chat/messages');
    return validateResponse(ChatMessagesResponseSchema, data, 'chatApi.getMessages');
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
  confirmProposal(proposalId: string, data?: ProposalConfirmRequest): Promise<AITaskProposal> {
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

  /**
   * Upload a file for attachment to a future GitHub Issue.
   */
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${API_BASE_URL}/chat/upload`;
    const csrfToken = getCsrfToken();
    const response = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {},
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Upload failed' }));
      throw new ApiError(response.status, { error: errorData.error || 'Upload failed' });
    }

    return response.json();
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
  async getBoardData(projectId: string, refresh = false): Promise<BoardDataResponse> {
    const params = refresh ? '?refresh=true' : '';
    const data = await request<BoardDataResponse>(`/board/projects/${projectId}${params}`);
    return validateResponse(BoardDataResponseSchema, data, 'boardApi.getBoardData');
  },

  /**
   * Get board data with per-column pagination.
   */
  async getBoardDataPaginated(
    projectId: string,
    columnLimit: number,
    columnCursors?: Record<string, string>,
    refresh = false,
  ): Promise<BoardDataResponse> {
    const qs = new URLSearchParams({ column_limit: String(columnLimit) });
    if (refresh) qs.set('refresh', 'true');
    if (columnCursors && Object.keys(columnCursors).length > 0) {
      qs.set('column_cursors', JSON.stringify(columnCursors));
    }
    const data = await request<BoardDataResponse>(`/board/projects/${projectId}?${qs}`);
    return validateResponse(BoardDataResponseSchema, data, 'boardApi.getBoardDataPaginated');
  },

  /**
   * Update a board item's status by name.
   */
  updateItemStatus(
    projectId: string,
    itemId: string,
    status: string,
  ): Promise<{ success: boolean }> {
    return request<{ success: boolean }>(
      `/board/projects/${projectId}/items/${itemId}/status`,
      {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      },
    );
  },
};

// ============ Settings API ============

export const settingsApi = {
  /**
   * Get authenticated user's effective settings (merged with global defaults).
   */
  async getUserSettings(): Promise<EffectiveUserSettings> {
    const data = await request<EffectiveUserSettings>('/settings/user');
    return validateResponse(EffectiveUserSettingsSchema, data, 'settingsApi.getUserSettings');
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

  /**
   * Fetch available models for a provider (dynamic dropdown population).
   *
   * Accepts an optional `RequestInit` so callers (e.g. TanStack Query) can
   * pass an `AbortSignal` for request cancellation.
   */
  fetchModels(provider: string, forceRefresh = false, init?: RequestInit): Promise<ModelsResponse> {
    const params = forceRefresh ? '?force_refresh=true' : '';
    return request<ModelsResponse>(`/settings/models/${provider}${params}`, init);
  },
};

// ============ Workflow API ============

export const workflowApi = {
  /**
   * Confirm an AI-generated issue recommendation.
   */
  confirmRecommendation(recommendationId: string): Promise<WorkflowResult> {
    return request<WorkflowResult>(`/workflow/recommendations/${recommendationId}/confirm`, {
      method: 'POST',
    });
  },

  /**
   * Reject an AI-generated issue recommendation.
   */
  rejectRecommendation(recommendationId: string): Promise<void> {
    return request<void>(`/workflow/recommendations/${recommendationId}/reject`, {
      method: 'POST',
    });
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

  async getPipelineState(issueNumber: number): Promise<PipelineStateInfo> {
    const data = await request<PipelineStateInfo>(`/workflow/pipeline-states/${issueNumber}`);
    return validateResponse(PipelineStateInfoSchema, data, 'workflowApi.getPipelineState');
  },
};

// ============ Metadata API ============

export const metadataApi = {
  /**
   * Get cached repository metadata (labels, branches, milestones, collaborators).
   */
  getMetadata(owner: string, repo: string): Promise<RepositoryMetadata> {
    return request<RepositoryMetadata>(`/metadata/${owner}/${repo}`);
  },

  /**
   * Force-refresh repository metadata from the GitHub API.
   */
  refreshMetadata(owner: string, repo: string): Promise<RepositoryMetadata> {
    return request<RepositoryMetadata>(`/metadata/${owner}/${repo}/refresh`, {
      method: 'POST',
    });
  },
};

// ============ Signal API ============

export const signalApi = {
  /**
   * Get current Signal connection status.
   */
  getConnection(): Promise<SignalConnection> {
    return request<SignalConnection>('/signal/connection');
  },

  /**
   * Initiate Signal QR code linking flow.
   */
  initiateLink(deviceName = 'Solune'): Promise<SignalLinkResponse> {
    return request<SignalLinkResponse>('/signal/connection/link', {
      method: 'POST',
      body: JSON.stringify({ device_name: deviceName }),
    });
  },

  /**
   * Poll linking status after QR code display.
   */
  checkLinkStatus(): Promise<SignalLinkStatusResponse> {
    return request<SignalLinkStatusResponse>('/signal/connection/link/status');
  },

  /**
   * Disconnect Signal account.
   */
  disconnect(): Promise<{ message: string }> {
    return request<{ message: string }>('/signal/connection', {
      method: 'DELETE',
    });
  },

  /**
   * Get Signal notification preferences.
   */
  getPreferences(): Promise<SignalPreferences> {
    return request<SignalPreferences>('/signal/preferences');
  },

  /**
   * Update Signal notification preferences.
   */
  updatePreferences(data: SignalPreferencesUpdate): Promise<SignalPreferences> {
    return request<SignalPreferences>('/signal/preferences', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get active Signal conflict banners.
   */
  getBanners(): Promise<SignalBannersResponse> {
    return request<SignalBannersResponse>('/signal/banners');
  },

  /**
   * Dismiss a conflict banner.
   */
  dismissBanner(bannerId: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/signal/banners/${bannerId}/dismiss`, {
      method: 'POST',
    });
  },
};

// ============ MCP Configuration API ============

export const mcpApi = {
  /**
   * List all MCP configurations for the authenticated user.
   */
  listMcps(): Promise<McpConfigurationListResponse> {
    return request<McpConfigurationListResponse>('/settings/mcps');
  },

  /**
   * Add a new MCP configuration.
   */
  createMcp(data: McpConfigurationCreate): Promise<McpConfiguration> {
    return request<McpConfiguration>('/settings/mcps', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete an MCP configuration by ID.
   */
  deleteMcp(mcpId: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/settings/mcps/${mcpId}`, {
      method: 'DELETE',
    });
  },
};

// ============ Cleanup API ============

export const cleanupApi = {
  /**
   * Perform a preflight check: fetch branches, PRs, and project board issues.
   */
  preflight(owner: string, repo: string, projectId: string): Promise<CleanupPreflightResponse> {
    return request<CleanupPreflightResponse>('/cleanup/preflight', {
      method: 'POST',
      body: JSON.stringify({ owner, repo, project_id: projectId }),
    });
  },

  /**
   * Execute the cleanup operation: delete branches, close PRs, and delete orphaned issues.
   */
  execute(data: CleanupExecuteRequest): Promise<CleanupExecuteResponse> {
    return request<CleanupExecuteResponse>('/cleanup/execute', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get audit trail of past cleanup operations.
   */
  history(owner: string, repo: string, limit = 10): Promise<CleanupHistoryResponse> {
    return request<CleanupHistoryResponse>(
      `/cleanup/history?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}&limit=${limit}`
    );
  },
};

// ============ Chores API ============

export const choresApi = {
  /**
   * Idempotently seed built-in chore presets for a project.
   */
  seedPresets(projectId: string): Promise<{ created: number }> {
    return request<{ created: number }>(`/chores/${projectId}/seed-presets`, {
      method: 'POST',
    });
  },

  /**
   * List all chores for a project.
   */
  list(projectId: string): Promise<Chore[]> {
    return request<Chore[]>(`/chores/${projectId}`);
  },

  /**
   * List chores with cursor-based pagination and optional server-side filters.
   */
  listPaginated(
    projectId: string,
    params: { limit: number; cursor?: string; status?: ChoreStatus; scheduleType?: ScheduleType | 'unscheduled'; search?: string; sort?: 'name' | 'updated_at' | 'created_at' | 'attention'; order?: 'asc' | 'desc' },
  ): Promise<PaginatedResponse<Chore>> {
    const qs = new URLSearchParams({ limit: String(params.limit) });
    if (params.cursor) qs.set('cursor', params.cursor);
    if (params.status) qs.set('status', params.status);
    if (params.scheduleType) qs.set('schedule_type', params.scheduleType);
    if (params.search) qs.set('search', params.search);
    if (params.sort) qs.set('sort', params.sort);
    if (params.order) qs.set('order', params.order);
    return request<PaginatedResponse<Chore>>(`/chores/${projectId}?${qs}`);
  },

  /**
   * List available chore templates from the repo's .github/ISSUE_TEMPLATE/.
   */
  listTemplates(projectId: string): Promise<ChoreTemplate[]> {
    return request<ChoreTemplate[]>(`/chores/${projectId}/templates`);
  },

  /**
   * List ALL chore names for a project — unpaginated, unfiltered.
   * Used for accurate template membership checks.
   */
  listChoreNames(projectId: string): Promise<string[]> {
    return request<string[]>(`/chores/${projectId}/chore-names`);
  },

  /**
   * Create a new chore.
   */
  create(projectId: string, data: ChoreCreate): Promise<Chore> {
    return request<Chore>(`/chores/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update a chore (schedule, status).
   */
  update(projectId: string, choreId: string, data: ChoreUpdate): Promise<Chore> {
    return request<Chore>(`/chores/${projectId}/${choreId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a chore.
   */
  delete(
    projectId: string,
    choreId: string
  ): Promise<{ deleted: boolean; closed_issue_number: number | null }> {
    return request<{ deleted: boolean; closed_issue_number: number | null }>(
      `/chores/${projectId}/${choreId}`,
      { method: 'DELETE' }
    );
  },

  /**
   * Manually trigger a chore.
   */
  trigger(
    projectId: string,
    choreId: string,
    parentIssueCount?: number
  ): Promise<ChoreTriggerResult> {
    return request<ChoreTriggerResult>(`/chores/${projectId}/${choreId}/trigger`, {
      method: 'POST',
      ...(parentIssueCount !== undefined
        ? { body: JSON.stringify({ parent_issue_count: parentIssueCount }) }
        : {}),
    });
  },

  /**
   * Send a chat message for sparse-input template refinement.
   */
  chat(projectId: string, data: ChoreChatMessage): Promise<ChoreChatResponse> {
    return request<ChoreChatResponse>(`/chores/${projectId}/chat`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Inline update a chore definition (creates a PR on save).
   */
  inlineUpdate(
    projectId: string,
    choreId: string,
    data: ChoreInlineUpdate
  ): Promise<ChoreInlineUpdateResponse> {
    return request<ChoreInlineUpdateResponse>(`/chores/${projectId}/${choreId}/inline-update`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Create a new chore with auto-merge flow.
   */
  createWithAutoMerge(
    projectId: string,
    data: ChoreCreateWithConfirmation
  ): Promise<ChoreCreateResponse> {
    return request<ChoreCreateResponse>(`/chores/${projectId}/create-with-merge`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Evaluate all active chore triggers.
   */
  evaluateTriggers(
    projectId?: string,
    parentIssueCount?: number
  ): Promise<EvaluateChoreTriggersResponse> {
    return request<EvaluateChoreTriggersResponse>('/chores/evaluate-triggers', {
      method: 'POST',
      body: JSON.stringify(
        projectId
          ? {
              project_id: projectId,
              ...(parentIssueCount !== undefined ? { parent_issue_count: parentIssueCount } : {}),
            }
          : {}
      ),
    });
  },
};

// ── Agents API ─────────────────────────────────────────────────────────

export type AgentStatus = 'active' | 'pending_pr' | 'pending_deletion';
export type AgentSource = 'local' | 'repo' | 'both';

export interface AgentConfig {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon_name: string | null;
  system_prompt: string;
  default_model_id: string;
  default_model_name: string;
  status: AgentStatus;
  tools: string[];
  status_column: string | null;
  github_issue_number: number | null;
  github_pr_number: number | null;
  branch_name: string | null;
  source: AgentSource;
  created_at: string | null;
}

export interface AgentCreate {
  name: string;
  description?: string;
  icon_name?: string | null;
  system_prompt: string;
  tools?: string[];
  status_column?: string;
  default_model_id?: string;
  default_model_name?: string;
  raw?: boolean;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  icon_name?: string | null;
  system_prompt?: string;
  tools?: string[];
  default_model_id?: string;
  default_model_name?: string;
}

export interface AgentCreateResult {
  agent: AgentConfig;
  pr_url: string;
  pr_number: number;
  issue_number: number | null;
  branch_name: string;
}

export interface AgentDeleteResult {
  success: boolean;
  pr_url: string;
  pr_number: number;
  issue_number: number | null;
}

export interface AgentPendingCleanupResult {
  success: boolean;
  deleted_count: number;
}

export interface AgentChatMessage {
  message: string;
  session_id?: string | null;
}

export interface AgentPreviewResponse {
  name: string;
  slug: string;
  description: string;
  system_prompt: string;
  status_column: string;
  tools: string[];
}

export interface AgentChatResponse {
  reply: string;
  session_id: string;
  is_complete: boolean;
  preview: AgentPreviewResponse | null;
}

export interface BulkModelUpdateResult {
  success: boolean;
  updated_count: number;
  failed_count: number;
  updated_agents: string[];
  failed_agents: string[];
  target_model_id: string;
  target_model_name: string;
}

export interface AgentMcpSyncResult {
  success: boolean;
  files_updated: number;
  files_skipped: number;
  files_unchanged: number;
  warnings: string[];
  errors: string[];
  synced_mcps: string[];
}

export const agentsApi = {
  list(projectId: string): Promise<AgentConfig[]> {
    return request<AgentConfig[]>(`/agents/${projectId}`);
  },

  listPaginated(
    projectId: string,
    params: { limit: number; cursor?: string },
  ): Promise<PaginatedResponse<AgentConfig>> {
    const qs = new URLSearchParams({ limit: String(params.limit) });
    if (params.cursor) qs.set('cursor', params.cursor);
    return request<PaginatedResponse<AgentConfig>>(`/agents/${projectId}?${qs}`);
  },

  pending(projectId: string): Promise<AgentConfig[]> {
    return request<AgentConfig[]>(`/agents/${projectId}/pending`);
  },

  clearPending(projectId: string): Promise<AgentPendingCleanupResult> {
    return request<AgentPendingCleanupResult>(`/agents/${projectId}/pending`, {
      method: 'DELETE',
    });
  },

  create(projectId: string, data: AgentCreate): Promise<AgentCreateResult> {
    return request<AgentCreateResult>(`/agents/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update(projectId: string, agentId: string, data: AgentUpdate): Promise<AgentCreateResult> {
    return request<AgentCreateResult>(`/agents/${projectId}/${agentId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  delete(projectId: string, agentId: string): Promise<AgentDeleteResult> {
    return request<AgentDeleteResult>(`/agents/${projectId}/${agentId}`, {
      method: 'DELETE',
    });
  },

  chat(projectId: string, data: AgentChatMessage): Promise<AgentChatResponse> {
    return request<AgentChatResponse>(`/agents/${projectId}/chat`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  bulkUpdateModels(
    projectId: string,
    targetModelId: string,
    targetModelName: string
  ): Promise<BulkModelUpdateResult> {
    return request<BulkModelUpdateResult>(`/agents/${projectId}/bulk-model`, {
      method: 'PATCH',
      body: JSON.stringify({ target_model_id: targetModelId, target_model_name: targetModelName }),
    });
  },

  syncMcps(projectId: string): Promise<AgentMcpSyncResult> {
    return request<AgentMcpSyncResult>(`/agents/${projectId}/sync-mcps`, {
      method: 'POST',
    });
  },
};

// ============ Pipelines API ============

export const pipelinesApi = {
  list(projectId: string, sort?: string, order?: string): Promise<PipelineConfigListResponse> {
    const params = new URLSearchParams();
    if (sort) params.set('sort', sort);
    if (order) params.set('order', order);
    const qs = params.toString();
    return request<PipelineConfigListResponse>(`/pipelines/${projectId}${qs ? `?${qs}` : ''}`);
  },

  listPaginated(
    projectId: string,
    params: { limit: number; cursor?: string },
    sort?: string,
    order?: string,
  ): Promise<PipelineConfigListResponse & { next_cursor: string | null; has_more: boolean; total_count: number | null }> {
    const qs = new URLSearchParams({ limit: String(params.limit) });
    if (params.cursor) qs.set('cursor', params.cursor);
    if (sort) qs.set('sort', sort);
    if (order) qs.set('order', order);
    return request<PipelineConfigListResponse & { next_cursor: string | null; has_more: boolean; total_count: number | null }>(`/pipelines/${projectId}?${qs}`);
  },

  get(projectId: string, pipelineId: string): Promise<PipelineConfig> {
    return request<PipelineConfig>(`/pipelines/${projectId}/${pipelineId}`);
  },

  create(projectId: string, data: PipelineConfigCreate): Promise<PipelineConfig> {
    return request<PipelineConfig>(`/pipelines/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update(
    projectId: string,
    pipelineId: string,
    data: PipelineConfigUpdate
  ): Promise<PipelineConfig> {
    return request<PipelineConfig>(`/pipelines/${projectId}/${pipelineId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete(projectId: string, pipelineId: string): Promise<{ success: boolean; deleted_id: string }> {
    return request<{ success: boolean; deleted_id: string }>(
      `/pipelines/${projectId}/${pipelineId}`,
      {
        method: 'DELETE',
      }
    );
  },

  seedPresets(projectId: string): Promise<PresetSeedResult> {
    return request<PresetSeedResult>(`/pipelines/${projectId}/seed-presets`, {
      method: 'POST',
    });
  },

  getAssignment(projectId: string): Promise<ProjectPipelineAssignment> {
    return request<ProjectPipelineAssignment>(`/pipelines/${projectId}/assignment`);
  },

  setAssignment(projectId: string, pipelineId: string): Promise<ProjectPipelineAssignment> {
    return request<ProjectPipelineAssignment>(`/pipelines/${projectId}/assignment`, {
      method: 'PUT',
      body: JSON.stringify({ pipeline_id: pipelineId }),
    });
  },

  launch(projectId: string, data: PipelineIssueLaunchRequest): Promise<WorkflowResult> {
    return request<WorkflowResult>(`/pipelines/${projectId}/launch`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  listRuns(
    pipelineId: string,
    params?: { limit?: number; offset?: number; status?: string },
  ): Promise<{
    runs: Array<Record<string, unknown>>;
    total: number;
    limit: number;
    offset: number;
  }> {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    if (params?.status) qs.set('status', params.status);
    const qsStr = qs.toString();
    return request<{
      runs: Array<Record<string, unknown>>;
      total: number;
      limit: number;
      offset: number;
    }>(
      `/pipelines/${pipelineId}/runs${qsStr ? `?${qsStr}` : ''}`,
    );
  },

  getRun(
    pipelineId: string,
    runId: string,
  ): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>(`/pipelines/${pipelineId}/runs/${runId}`);
  },
};

// ============ Models API ============

export const modelsApi = {
  async list(forceRefresh = false): Promise<AIModel[]> {
    const response = await settingsApi.fetchModels('copilot', forceRefresh);
    // Treat non-success responses with no models as an error so TanStack Query
    // retries on subsequent mounts rather than permanently caching an empty list.
    if (response.status !== 'success' && !response.models?.length) {
      throw new Error(response.message ?? `Unable to load models: ${response.status}`);
    }
    return (response.models ?? []).map((model) => ({
      id: model.id,
      name: model.name,
      provider: model.provider,
    }));
  },
};

// ============ Tools API (027-mcp-tools-page) ============

export const toolsApi = {
  getRepoConfig(projectId: string): Promise<RepoMcpConfigResponse> {
    return request<RepoMcpConfigResponse>(`/tools/${projectId}/repo-config`);
  },

  updateRepoServer(
    projectId: string,
    serverName: string,
    data: RepoMcpServerUpdate
  ): Promise<RepoMcpServerConfig> {
    return request<RepoMcpServerConfig>(
      `/tools/${projectId}/repo-config/${encodeURIComponent(serverName)}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    );
  },

  deleteRepoServer(projectId: string, serverName: string): Promise<RepoMcpServerConfig> {
    return request<RepoMcpServerConfig>(
      `/tools/${projectId}/repo-config/${encodeURIComponent(serverName)}`,
      {
        method: 'DELETE',
      }
    );
  },

  listPresets(): Promise<McpPresetListResponse> {
    return request<McpPresetListResponse>('/tools/presets');
  },

  list(projectId: string): Promise<McpToolConfigListResponse> {
    return request<McpToolConfigListResponse>(`/tools/${projectId}`);
  },

  listPaginated(
    projectId: string,
    params: { limit: number; cursor?: string },
  ): Promise<McpToolConfigListResponse & { next_cursor: string | null; has_more: boolean; total_count: number | null }> {
    const qs = new URLSearchParams({ limit: String(params.limit) });
    if (params.cursor) qs.set('cursor', params.cursor);
    return request<McpToolConfigListResponse & { next_cursor: string | null; has_more: boolean; total_count: number | null }>(`/tools/${projectId}?${qs}`);
  },

  get(projectId: string, toolId: string): Promise<McpToolConfig> {
    return request<McpToolConfig>(`/tools/${projectId}/${toolId}`);
  },

  create(projectId: string, data: McpToolConfigCreate): Promise<McpToolConfig> {
    return request<McpToolConfig>(`/tools/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update(projectId: string, toolId: string, data: McpToolConfigUpdate): Promise<McpToolConfig> {
    return request<McpToolConfig>(`/tools/${projectId}/${toolId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  sync(projectId: string, toolId: string): Promise<McpToolSyncResult> {
    return request<McpToolSyncResult>(`/tools/${projectId}/${toolId}/sync`, {
      method: 'POST',
    });
  },

  delete(projectId: string, toolId: string, confirm = false): Promise<ToolDeleteResult> {
    const qs = confirm ? '?confirm=true' : '';
    return request<ToolDeleteResult>(`/tools/${projectId}/${toolId}${qs}`, {
      method: 'DELETE',
    });
  },
};

// ============ Agent Tools API (027-mcp-tools-page) ============

export const agentToolsApi = {
  getTools(projectId: string, agentId: string): Promise<{ tools: ToolChip[] }> {
    return request<{ tools: ToolChip[] }>(`/agents/${projectId}/${agentId}/tools`);
  },

  updateTools(
    projectId: string,
    agentId: string,
    toolIds: string[]
  ): Promise<{ tools: ToolChip[] }> {
    return request<{ tools: ToolChip[] }>(`/agents/${projectId}/${agentId}/tools`, {
      method: 'PUT',
      body: JSON.stringify({ tool_ids: toolIds }),
    });
  },
};

// ============ Apps API (041-solune-rebrand-app-builder) ============

import type {
  App,
  AppAssetInventory,
  AppCreate,
  AppUpdate,
  AppStatusResponse,
  AppStatus,
  DeleteAppResult,
  Owner,
  CreateProjectRequest,
  CreateProjectResponse,
} from '@/types/apps';

export const appsApi = {
  list(status?: AppStatus): Promise<App[]> {
    const qs = status ? `?status=${status}` : '';
    return request<App[]>(`/apps${qs}`);
  },

  listPaginated(
    params: { limit: number; cursor?: string },
    status?: AppStatus,
  ): Promise<PaginatedResponse<App>> {
    const qs = new URLSearchParams({ limit: String(params.limit) });
    if (params.cursor) qs.set('cursor', params.cursor);
    if (status) qs.set('status', status);
    return request<PaginatedResponse<App>>(`/apps?${qs}`);
  },

  create(data: AppCreate): Promise<App> {
    return request<App>('/apps', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  get(appName: string): Promise<App> {
    return request<App>(`/apps/${appName}`);
  },

  update(appName: string, data: AppUpdate): Promise<App> {
    return request<App>(`/apps/${appName}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete(appName: string, force?: boolean): Promise<DeleteAppResult | void> {
    const qs = force ? '?force=true' : '';
    return request<DeleteAppResult | void>(`/apps/${appName}${qs}`, { method: 'DELETE' });
  },

  assets(appName: string): Promise<AppAssetInventory> {
    return request<AppAssetInventory>(`/apps/${appName}/assets`);
  },

  start(appName: string): Promise<AppStatusResponse> {
    return request<AppStatusResponse>(`/apps/${appName}/start`, { method: 'POST' });
  },

  stop(appName: string): Promise<AppStatusResponse> {
    return request<AppStatusResponse>(`/apps/${appName}/stop`, { method: 'POST' });
  },

  status(appName: string): Promise<AppStatusResponse> {
    return request<AppStatusResponse>(`/apps/${appName}/status`);
  },

  owners(): Promise<Owner[]> {
    return request<Owner[]>('/apps/owners');
  },
};

// ============ Activity API (054-activity-audit-trail) ============

export const activityApi = {
  feed(
    projectId: string,
    params?: { limit?: number; cursor?: string; event_type?: string },
  ): Promise<PaginatedResponse<ActivityEvent>> {
    const qs = new URLSearchParams({ project_id: projectId });
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.cursor) qs.set('cursor', params.cursor);
    if (params?.event_type) qs.set('event_type', params.event_type);
    return request<PaginatedResponse<ActivityEvent>>(`/activity?${qs}`);
  },

  entityHistory(
    projectId: string,
    entityType: string,
    entityId: string,
    params?: { limit?: number; cursor?: string },
  ): Promise<PaginatedResponse<ActivityEvent>> {
    const qs = new URLSearchParams({ project_id: projectId });
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.cursor) qs.set('cursor', params.cursor);
    const qsStr = qs.toString();
    return request<PaginatedResponse<ActivityEvent>>(
      `/activity/${entityType}/${entityId}${qsStr ? `?${qsStr}` : ''}`,
    );
  },
};
