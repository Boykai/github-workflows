/**
 * Unit tests for App component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import * as useAuthHook from '@/hooks/useAuth';
import * as useProjectsHook from '@/hooks/useProjects';
import * as useChatHook from '@/hooks/useChat';
import * as useWorkflowHook from '@/hooks/useWorkflow';

// Mock all the hooks
vi.mock('@/hooks/useAuth');
vi.mock('@/hooks/useProjects');
vi.mock('@/hooks/useChat');
vi.mock('@/hooks/useWorkflow');
vi.mock('@/components/auth/LoginButton', () => ({
  LoginButton: () => <button>Login with GitHub</button>,
}));
vi.mock('@/components/sidebar/ProjectSidebar', () => ({
  ProjectSidebar: () => <div>Project Sidebar</div>,
}));
vi.mock('@/components/chat/ChatInterface', () => ({
  ChatInterface: () => <div>Chat Interface</div>,
}));

describe('App Component', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const mockUseAuth = useAuthHook.useAuth as ReturnType<typeof vi.fn>;
  const mockUseProjects = useProjectsHook.useProjects as ReturnType<typeof vi.fn>;
  const mockUseChat = useChatHook.useChat as ReturnType<typeof vi.fn>;
  const mockUseWorkflow = useWorkflowHook.useWorkflow as ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    mockUseChat.mockReturnValue({
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

    mockUseWorkflow.mockReturnValue({
      confirmRecommendation: vi.fn(),
      rejectRecommendation: vi.fn(),
    });

    mockUseProjects.mockReturnValue({
      projects: [],
      selectedProject: null,
      tasks: [],
      isLoading: false,
      tasksLoading: false,
      selectProject: vi.fn(),
      refreshTasks: vi.fn(),
    });
  });

  it('should render Hello World message when authenticated', () => {
    // Mock authenticated state
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: '1', username: 'testuser', selected_project_id: '123' },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );

    // Check that "Hello World" is rendered
    const helloWorldElement = screen.getByText('Hello World');
    expect(helloWorldElement).toBeTruthy();
  });

  it('should not render Hello World message when not authenticated', () => {
    // Mock unauthenticated state
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );

    // Check that "Hello World" is NOT rendered
    const helloWorldElement = screen.queryByText('Hello World');
    expect(helloWorldElement).toBeNull();
  });
});
