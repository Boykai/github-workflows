/**
 * API client service for GitHub Projects Chat Interface.
 * Provides typed fetch wrapper with error handling.
 */

import type {
  APIError,
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
  WeatherData,
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

// ============ Weather API ============

// For demo purposes, we'll use a mock weather service
// In production, this would use OpenWeatherMap or similar API
export const weatherApi = {
  /**
   * Get current weather for user's location.
   * Uses browser geolocation and OpenWeatherMap API.
   */
  async getCurrentWeather(): Promise<WeatherData> {
    // For demo purposes, return mock data
    // In production, this would:
    // 1. Get user's location via geolocation API
    // 2. Call OpenWeatherMap API with coordinates
    // 3. Parse and return weather data
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock weather data
    const mockWeather: WeatherData = {
      location: 'San Francisco',
      temperature: 18,
      condition: 'Clear',
      description: 'Clear sky',
      icon: '01d', // OpenWeatherMap icon code for clear sky day
      humidity: 65,
      windSpeed: 12,
    };
    
    return mockWeather;
  },
};
