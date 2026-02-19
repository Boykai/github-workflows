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
  ChatInterface: () => <div data-testid="chat" />,
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
});
