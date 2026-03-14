/**
 * Tests for AddChoreModal component.
 *
 * Covers: modal open/close, form validation, rich content submission flow.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AddChoreModal } from '../AddChoreModal';
import type { ReactNode } from 'react';

// ── Mock API ──

const mockCreate = vi.fn();
const mockCreateWithAutoMerge = vi.fn();
const mockChat = vi.fn();
const mockPipelinesList = vi.fn();

vi.mock('@/services/api', () => ({
  choresApi: {
    create: (...args: unknown[]) => mockCreate(...args),
    createWithAutoMerge: (...args: unknown[]) => mockCreateWithAutoMerge(...args),
    chat: (...args: unknown[]) => mockChat(...args),
    list: vi.fn().mockResolvedValue([]),
    listTemplates: vi.fn().mockResolvedValue([]),
  },
  pipelinesApi: {
    list: (...args: unknown[]) => mockPipelinesList(...args),
  },
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public error: { error: string }
    ) {
      super(error.error);
    }
  },
}));

// ── Wrapper ──

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

// ── Tests ──

describe('AddChoreModal', () => {
  const onClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockPipelinesList.mockResolvedValue({ pipelines: [] });
  });

  it('does not render when isOpen is false', () => {
    render(<AddChoreModal projectId="PVT_1" isOpen={false} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    expect(screen.queryByText('Add Chore')).not.toBeInTheDocument();
  });

  it('renders modal when isOpen is true', () => {
    render(<AddChoreModal projectId="PVT_1" isOpen={true} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('Add Chore')).toBeInTheDocument();
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Template Content')).toBeInTheDocument();
  });

  it('shows validation error when name is empty', async () => {
    const user = userEvent.setup();

    render(<AddChoreModal projectId="PVT_1" isOpen={true} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    await user.click(screen.getByText('Create Chore'));

    expect(screen.getByText('Name is required')).toBeInTheDocument();
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it('shows validation error when template content is empty', async () => {
    const user = userEvent.setup();

    render(<AddChoreModal projectId="PVT_1" isOpen={true} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    await user.type(screen.getByLabelText('Name'), 'Bug Bash');
    await user.click(screen.getByText('Create Chore'));

    expect(screen.getByText('Template content is required')).toBeInTheDocument();
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    mockCreateWithAutoMerge.mockResolvedValue({
      chore: { id: 'chore-1', name: 'Bug Bash', project_id: 'PVT_1' },
      pr_merged: true,
    });

    render(<AddChoreModal projectId="PVT_1" isOpen={true} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    await user.type(screen.getByLabelText('Name'), 'Bug Bash');
    await user.type(screen.getByLabelText('Template Content'), '## Overview\nRun a bug bash');
    await user.click(screen.getByText('Create Chore'));

    // Step 1: Confirmation modal appears
    await waitFor(() => {
      expect(screen.getByText('I Understand, Continue')).toBeInTheDocument();
    });
    await user.click(screen.getByText('I Understand, Continue'));

    // Step 2: Final confirmation
    await waitFor(() => {
      expect(screen.getByText('Yes, Create Chore')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Yes, Create Chore'));

    await waitFor(() => {
      expect(mockCreateWithAutoMerge).toHaveBeenCalledWith('PVT_1', {
        name: 'Bug Bash',
        template_content: '## Overview\nRun a bug bash',
        ai_enhance_enabled: true,
        agent_pipeline_id: '',
        auto_merge: true,
      });
    });
  });

  it('calls onClose when Cancel is clicked', async () => {
    const user = userEvent.setup();

    render(<AddChoreModal projectId="PVT_1" isOpen={true} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    await user.click(screen.getByText('Cancel'));

    expect(onClose).toHaveBeenCalled();
  });

  it('shows API error on submission failure', async () => {
    const user = userEvent.setup();
    mockCreateWithAutoMerge.mockRejectedValue(new Error('Duplicate chore name'));

    render(<AddChoreModal projectId="PVT_1" isOpen={true} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    await user.type(screen.getByLabelText('Name'), 'Test');
    await user.type(
      screen.getByLabelText('Template Content'),
      '## Overview\n\n- Step one\n- Step two\n- Step three\n\nDetailed content here'
    );
    await user.click(screen.getByText('Create Chore'));

    // Walk through double-confirmation
    await waitFor(() => {
      expect(screen.getByText('I Understand, Continue')).toBeInTheDocument();
    });
    await user.click(screen.getByText('I Understand, Continue'));

    await waitFor(() => {
      expect(screen.getByText('Yes, Create Chore')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Yes, Create Chore'));

    await waitFor(() => {
      expect(screen.getByText('Duplicate chore name')).toBeInTheDocument();
    });
  });

  it('routes sparse input to chat flow instead of direct creation', async () => {
    const user = userEvent.setup();
    mockChat.mockResolvedValue({
      message: 'Tell me more about the bug bash.',
      conversation_id: 'conv-abc',
      template_ready: false,
      template_content: null,
    });

    render(<AddChoreModal projectId="PVT_1" isOpen={true} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    await user.type(screen.getByLabelText('Name'), 'Bug Bash');
    await user.type(screen.getByLabelText('Template Content'), 'run a bug bash');
    await user.click(screen.getByText('Create Chore'));

    // Should show chat flow header, not submit directly
    await waitFor(() => {
      expect(screen.getByText('Build Template — Bug Bash')).toBeInTheDocument();
    });
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it('submits rich input directly without chat flow', async () => {
    const user = userEvent.setup();
    mockCreateWithAutoMerge.mockResolvedValue({
      chore: { id: 'chore-1', name: 'Dep Update', project_id: 'PVT_1' },
      pr_merged: true,
    });

    const richContent =
      '## Dependency Update\n\n- Check outdated packages\n- Run npm audit\n- Update major versions';

    render(<AddChoreModal projectId="PVT_1" isOpen={true} onClose={onClose} />, {
      wrapper: createWrapper(),
    });

    await user.type(screen.getByLabelText('Name'), 'Dep Update');
    await user.type(screen.getByLabelText('Template Content'), richContent);
    await user.click(screen.getByText('Create Chore'));

    // Step 1: Confirmation modal appears
    await waitFor(() => {
      expect(screen.getByText('I Understand, Continue')).toBeInTheDocument();
    });
    await user.click(screen.getByText('I Understand, Continue'));

    // Step 2: Final confirmation
    await waitFor(() => {
      expect(screen.getByText('Yes, Create Chore')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Yes, Create Chore'));

    await waitFor(() => {
      expect(mockCreateWithAutoMerge).toHaveBeenCalledWith('PVT_1', {
        name: 'Dep Update',
        template_content: richContent,
        ai_enhance_enabled: true,
        agent_pipeline_id: '',
        auto_merge: true,
      });
    });
    // Should NOT show chat flow
    expect(screen.queryByText(/Build Template/)).not.toBeInTheDocument();
  });
});
