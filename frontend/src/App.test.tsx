/**
 * Unit tests for App component - Title verification
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';
import * as useAuthModule from '@/hooks/useAuth';
import * as useProjectsModule from '@/hooks/useProjects';
import * as useChatModule from '@/hooks/useChat';
import * as useWorkflowModule from '@/hooks/useWorkflow';

// Mock all the hooks
vi.mock('@/hooks/useAuth');
vi.mock('@/hooks/useProjects');
vi.mock('@/hooks/useChat');
vi.mock('@/hooks/useWorkflow');
vi.mock('@/components/auth/LoginButton', () => ({
  LoginButton: () => <button>Login</button>,
}));
vi.mock('@/components/sidebar/ProjectSidebar', () => ({
  ProjectSidebar: () => <div>Project Sidebar</div>,
}));
vi.mock('@/components/chat/ChatInterface', () => ({
  ChatInterface: () => <div>Chat Interface</div>,
}));

describe('App Component - Tech Connect 2026 Branding', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays "Welcome to Tech Connect 2026" in login page title', () => {
    // Mock unauthenticated state
    vi.mocked(useAuthModule.useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
    });

    // Mock other hooks (they won't be called but need to be mocked)
    vi.mocked(useProjectsModule.useProjects).mockReturnValue({
      projects: [],
      selectedProject: null,
      tasks: [],
      isLoading: false,
      tasksLoading: false,
      selectProject: vi.fn(),
      refreshTasks: vi.fn(),
    });

    vi.mocked(useChatModule.useChat).mockReturnValue({
      messages: [],
      pendingProposals: [],
      pendingStatusChanges: [],
      pendingRecommendations: [],
      isSending: false,
      sendMessage: vi.fn(),
      confirmProposal: vi.fn(),
      confirmStatusChange: vi.fn(),
      rejectProposal: vi.fn(),
      removePendingRecommendation: vi.fn(),
      clearChat: vi.fn(),
    });

    vi.mocked(useWorkflowModule.useWorkflow).mockReturnValue({
      confirmRecommendation: vi.fn(),
      rejectRecommendation: vi.fn(),
    });

    render(<App />);

    // Check for the welcome message in the login title
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toBe('Welcome to Tech Connect 2026 - GitHub Projects Chat');
  });

  it('displays "Welcome to Tech Connect 2026" in main app header', () => {
    // Mock authenticated state
    vi.mocked(useAuthModule.useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { username: 'testuser', selected_project_id: null },
      login: vi.fn(),
      logout: vi.fn(),
    });

    vi.mocked(useProjectsModule.useProjects).mockReturnValue({
      projects: [],
      selectedProject: null,
      tasks: [],
      isLoading: false,
      tasksLoading: false,
      selectProject: vi.fn(),
      refreshTasks: vi.fn(),
    });

    vi.mocked(useChatModule.useChat).mockReturnValue({
      messages: [],
      pendingProposals: [],
      pendingStatusChanges: [],
      pendingRecommendations: [],
      isSending: false,
      sendMessage: vi.fn(),
      confirmProposal: vi.fn(),
      confirmStatusChange: vi.fn(),
      rejectProposal: vi.fn(),
      removePendingRecommendation: vi.fn(),
      clearChat: vi.fn(),
    });

    vi.mocked(useWorkflowModule.useWorkflow).mockReturnValue({
      confirmRecommendation: vi.fn(),
      rejectRecommendation: vi.fn(),
    });

    render(<App />);

    // Check for the welcome message in the main header
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toBe('Welcome to Tech Connect 2026 - GitHub Projects Chat');
  });
});
