/**
 * Unit tests for App component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

vi.mock('./App.css', () => ({}));

const mockUseAuth = vi.fn();
const mockUseProjects = vi.fn();
const mockUseChat = vi.fn();
const mockUseWorkflow = vi.fn();
const mockUseAppTheme = vi.fn();

vi.mock('@/hooks/useAuth', () => ({ useAuth: (...args: unknown[]) => mockUseAuth(...args) }));
vi.mock('@/hooks/useProjects', () => ({ useProjects: (...args: unknown[]) => mockUseProjects(...args) }));
vi.mock('@/hooks/useChat', () => ({ useChat: (...args: unknown[]) => mockUseChat(...args) }));
vi.mock('@/hooks/useWorkflow', () => ({ useWorkflow: (...args: unknown[]) => mockUseWorkflow(...args) }));
vi.mock('@/hooks/useAppTheme', () => ({ useAppTheme: (...args: unknown[]) => mockUseAppTheme(...args) }));

vi.mock('@/components/auth/LoginButton', () => ({
  LoginButton: () => <button>Login</button>,
}));
vi.mock('@/components/sidebar/ProjectSidebar', () => ({
  ProjectSidebar: () => <div data-testid="sidebar" />,
}));
vi.mock('@/components/chat/ChatInterface', () => ({
  ChatInterface: (props: Record<string, unknown>) => <div data-testid="chat" data-props={JSON.stringify(Object.keys(props))} />,
}));
vi.mock('@/pages/ProjectBoardPage', () => ({
  ProjectBoardPage: () => <div data-testid="board-page" />,
}));

function setupDefaultMocks(overrides: {
  auth?: Partial<ReturnType<typeof mockUseAuth>>;
  projects?: Partial<ReturnType<typeof mockUseProjects>>;
} = {}) {
  mockUseAuth.mockReturnValue({
    isAuthenticated: false,
    isLoading: false,
    user: null,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    refetch: vi.fn(),
    ...overrides.auth,
  });

  mockUseProjects.mockReturnValue({
    projects: [],
    selectedProject: { project_id: 'p1', name: 'Test' },
    tasks: [],
    isLoading: false,
    tasksLoading: false,
    selectProject: vi.fn(),
    refreshProjects: vi.fn(),
    refreshTasks: vi.fn(),
    error: null,
    ...overrides.projects,
  });

  mockUseChat.mockReturnValue({
    messages: [],
    isLoading: false,
    isSending: false,
    error: null,
    pendingProposals: new Map(),
    pendingStatusChanges: new Map(),
    pendingRecommendations: new Map(),
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
    getConfig: vi.fn(),
    updateConfig: vi.fn(),
    isLoading: false,
    error: null,
  });

  mockUseAppTheme.mockReturnValue({
    isDarkMode: false,
    toggleTheme: vi.fn(),
  });
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner when auth is loading', () => {
    setupDefaultMocks({ auth: { isLoading: true } });
    render(<App />);
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('shows login page when not authenticated', () => {
    setupDefaultMocks({ auth: { isAuthenticated: false } });
    render(<App />);
    expect(screen.getByText('Agent Projects')).toBeDefined();
    expect(screen.getByText('Login')).toBeDefined();
  });

  it('shows app with chat view when authenticated', () => {
    setupDefaultMocks({ auth: { isAuthenticated: true, user: { github_user_id: 'u1', github_username: 'test' } } });
    render(<App />);
    expect(screen.getByTestId('sidebar')).toBeDefined();
    expect(screen.getByTestId('chat')).toBeDefined();
  });

  it('navigation between chat and board views works', () => {
    setupDefaultMocks({ auth: { isAuthenticated: true, user: { github_user_id: 'u1', github_username: 'test' } } });
    render(<App />);
    // Default is chat view
    expect(screen.getByTestId('chat')).toBeDefined();
    // Navigate to board
    fireEvent.click(screen.getByText('Project Board'));
    expect(screen.getByTestId('board-page')).toBeDefined();
    // Navigate back to chat
    fireEvent.click(screen.getByText('Chat'));
    expect(screen.getByTestId('chat')).toBeDefined();
  });

  it('theme toggle button works', () => {
    const toggleTheme = vi.fn();
    mockUseAppTheme.mockReturnValue({ isDarkMode: false, toggleTheme });
    setupDefaultMocks({ auth: { isAuthenticated: true, user: { github_user_id: 'u1', github_username: 'test' } } });
    mockUseAppTheme.mockReturnValue({ isDarkMode: false, toggleTheme });
    render(<App />);
    fireEvent.click(screen.getByLabelText('Switch to dark mode'));
    expect(toggleTheme).toHaveBeenCalledOnce();
  });

  it('shows chat placeholder when no project selected', () => {
    setupDefaultMocks({
      auth: { isAuthenticated: true, user: { github_user_id: 'u1', github_username: 'test' } },
      projects: { selectedProject: null },
    });
    render(<App />);
    expect(screen.getByText('Select a project from the sidebar to start chatting')).toBeDefined();
  });

  it('handleConfirmProposal calls confirmProposal and refreshTasks', async () => {
    const confirmProposal = vi.fn().mockResolvedValue(undefined);
    const refreshTasks = vi.fn();
    setupDefaultMocks({
      auth: { isAuthenticated: true, user: { github_user_id: 'u1', github_username: 'test' } },
    });
    mockUseChat.mockReturnValue({
      messages: [],
      isLoading: false,
      isSending: false,
      error: null,
      pendingProposals: new Map(),
      pendingStatusChanges: new Map(),
      pendingRecommendations: new Map(),
      sendMessage: vi.fn(),
      confirmProposal,
      confirmStatusChange: vi.fn(),
      rejectProposal: vi.fn(),
      removePendingRecommendation: vi.fn(),
      clearChat: vi.fn(),
    });
    mockUseProjects.mockReturnValue({
      projects: [],
      selectedProject: { project_id: 'p1', name: 'Test' },
      tasks: [],
      isLoading: false,
      tasksLoading: false,
      selectProject: vi.fn(),
      refreshProjects: vi.fn(),
      refreshTasks,
      error: null,
    });

    // Unmock ChatInterface to capture onConfirmProposal
    // Instead, verify the mock ChatInterface receives the callback and call it
    let capturedProps: Record<string, unknown> = {};
    const { unmock } = await vi.hoisted(() => ({ unmock: false }));
    // Use a different approach: re-mock ChatInterface to capture props
    vi.mocked(await import('@/components/chat/ChatInterface')).ChatInterface = vi.fn(
      (props: Record<string, unknown>) => {
        capturedProps = props;
        return <div data-testid="chat" /> as React.ReactElement;
      }
    ) as unknown as typeof import('@/components/chat/ChatInterface').ChatInterface;

    render(<App />);

    // Call the onConfirmProposal callback
    if (capturedProps.onConfirmProposal) {
      await (capturedProps.onConfirmProposal as (id: string) => Promise<void>)('prop-1');
    }
    expect(confirmProposal).toHaveBeenCalledWith('prop-1');
    expect(refreshTasks).toHaveBeenCalled();
  });

  it('onConfirmRecommendation calls workflow confirm and removes pending', async () => {
    const confirmRecommendation = vi.fn().mockResolvedValue({ success: true });
    const removePendingRecommendation = vi.fn();
    const refreshTasks = vi.fn();
    setupDefaultMocks({
      auth: { isAuthenticated: true, user: { github_user_id: 'u1', github_username: 'test' } },
    });
    mockUseWorkflow.mockReturnValue({
      confirmRecommendation,
      rejectRecommendation: vi.fn(),
      getConfig: vi.fn(),
      updateConfig: vi.fn(),
      isLoading: false,
      error: null,
    });
    mockUseChat.mockReturnValue({
      messages: [],
      isLoading: false,
      isSending: false,
      error: null,
      pendingProposals: new Map(),
      pendingStatusChanges: new Map(),
      pendingRecommendations: new Map(),
      sendMessage: vi.fn(),
      confirmProposal: vi.fn(),
      confirmStatusChange: vi.fn(),
      rejectProposal: vi.fn(),
      removePendingRecommendation,
      clearChat: vi.fn(),
    });
    mockUseProjects.mockReturnValue({
      projects: [],
      selectedProject: { project_id: 'p1', name: 'Test' },
      tasks: [],
      isLoading: false,
      tasksLoading: false,
      selectProject: vi.fn(),
      refreshProjects: vi.fn(),
      refreshTasks,
      error: null,
    });

    let capturedProps: Record<string, unknown> = {};
    vi.mocked(await import('@/components/chat/ChatInterface')).ChatInterface = vi.fn(
      (props: Record<string, unknown>) => {
        capturedProps = props;
        return <div data-testid="chat" /> as React.ReactElement;
      }
    ) as unknown as typeof import('@/components/chat/ChatInterface').ChatInterface;

    render(<App />);

    if (capturedProps.onConfirmRecommendation) {
      await (capturedProps.onConfirmRecommendation as (id: string) => Promise<unknown>)('rec-1');
    }
    expect(confirmRecommendation).toHaveBeenCalledWith('rec-1');
    expect(removePendingRecommendation).toHaveBeenCalledWith('rec-1');
    expect(refreshTasks).toHaveBeenCalled();
  });

  it('onRejectRecommendation calls workflow reject and removes pending', async () => {
    const rejectRecommendation = vi.fn().mockResolvedValue(undefined);
    const removePendingRecommendation = vi.fn();
    setupDefaultMocks({
      auth: { isAuthenticated: true, user: { github_user_id: 'u1', github_username: 'test' } },
    });
    mockUseWorkflow.mockReturnValue({
      confirmRecommendation: vi.fn(),
      rejectRecommendation,
      getConfig: vi.fn(),
      updateConfig: vi.fn(),
      isLoading: false,
      error: null,
    });
    mockUseChat.mockReturnValue({
      messages: [],
      isLoading: false,
      isSending: false,
      error: null,
      pendingProposals: new Map(),
      pendingStatusChanges: new Map(),
      pendingRecommendations: new Map(),
      sendMessage: vi.fn(),
      confirmProposal: vi.fn(),
      confirmStatusChange: vi.fn(),
      rejectProposal: vi.fn(),
      removePendingRecommendation,
      clearChat: vi.fn(),
    });
    mockUseProjects.mockReturnValue({
      projects: [],
      selectedProject: { project_id: 'p1', name: 'Test' },
      tasks: [],
      isLoading: false,
      tasksLoading: false,
      selectProject: vi.fn(),
      refreshProjects: vi.fn(),
      refreshTasks: vi.fn(),
      error: null,
    });

    let capturedProps: Record<string, unknown> = {};
    vi.mocked(await import('@/components/chat/ChatInterface')).ChatInterface = vi.fn(
      (props: Record<string, unknown>) => {
        capturedProps = props;
        return <div data-testid="chat" /> as React.ReactElement;
      }
    ) as unknown as typeof import('@/components/chat/ChatInterface').ChatInterface;

    render(<App />);

    if (capturedProps.onRejectRecommendation) {
      await (capturedProps.onRejectRecommendation as (id: string) => Promise<void>)('rec-1');
    }
    expect(rejectRecommendation).toHaveBeenCalledWith('rec-1');
    expect(removePendingRecommendation).toHaveBeenCalledWith('rec-1');
  });
});
