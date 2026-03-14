/**
 * Tests for ChoreScheduleConfig component.
 *
 * Covers: schedule type selection, value input, save action, validation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChoreScheduleConfig } from '../ChoreScheduleConfig';
import type { Chore } from '@/types';
import type { ReactNode } from 'react';

// ── Mock API ──

const mockUpdate = vi.fn();

vi.mock('@/services/api', () => ({
  choresApi: {
    update: (...args: unknown[]) => mockUpdate(...args),
    list: vi.fn().mockResolvedValue([]),
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

// ── Factory ──

function createChore(overrides: Partial<Chore> = {}): Chore {
  return {
    id: 'chore-1',
    project_id: 'PVT_1',
    name: 'Test Chore',
    template_path: '.github/ISSUE_TEMPLATE/test-chore.md',
    template_content: '# Test',
    schedule_type: null,
    schedule_value: null,
    status: 'active',
    last_triggered_at: null,
    last_triggered_count: 0,
    current_issue_number: null,
    current_issue_node_id: null,
    pr_number: null,
    pr_url: null,
    tracking_issue_number: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

// ── Tests ──

describe('ChoreScheduleConfig', () => {
  const onDone = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders schedule type dropdown and value input', () => {
    render(<ChoreScheduleConfig chore={createChore()} projectId="PVT_1" onDone={onDone} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByLabelText('Schedule type')).toBeInTheDocument();
    expect(screen.getByLabelText('Schedule value')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  it('shows error when no type selected', async () => {
    const user = userEvent.setup();

    render(<ChoreScheduleConfig chore={createChore()} projectId="PVT_1" onDone={onDone} />, {
      wrapper: createWrapper(),
    });

    await user.click(screen.getByText('Save'));

    expect(screen.getByText('Select a schedule type')).toBeInTheDocument();
    expect(mockUpdate).not.toHaveBeenCalled();
  });

  it('shows error when value is empty', async () => {
    const user = userEvent.setup();

    render(<ChoreScheduleConfig chore={createChore()} projectId="PVT_1" onDone={onDone} />, {
      wrapper: createWrapper(),
    });

    await user.selectOptions(screen.getByLabelText('Schedule type'), 'time');
    await user.click(screen.getByText('Save'));

    expect(screen.getByText('Value must be a positive integer')).toBeInTheDocument();
    expect(mockUpdate).not.toHaveBeenCalled();
  });

  it('saves time schedule successfully', async () => {
    const user = userEvent.setup();
    const chore = createChore();
    mockUpdate.mockResolvedValue({ ...chore, schedule_type: 'time', schedule_value: 14 });

    render(<ChoreScheduleConfig chore={chore} projectId="PVT_1" onDone={onDone} />, {
      wrapper: createWrapper(),
    });

    await user.selectOptions(screen.getByLabelText('Schedule type'), 'time');
    await user.type(screen.getByLabelText('Schedule value'), '14');
    await user.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith('PVT_1', 'chore-1', {
        schedule_type: 'time',
        schedule_value: 14,
      });
    });
  });

  it('saves count schedule successfully', async () => {
    const user = userEvent.setup();
    const chore = createChore();
    mockUpdate.mockResolvedValue({ ...chore, schedule_type: 'count', schedule_value: 5 });

    render(<ChoreScheduleConfig chore={chore} projectId="PVT_1" onDone={onDone} />, {
      wrapper: createWrapper(),
    });

    await user.selectOptions(screen.getByLabelText('Schedule type'), 'count');
    await user.type(screen.getByLabelText('Schedule value'), '5');
    await user.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith('PVT_1', 'chore-1', {
        schedule_type: 'count',
        schedule_value: 5,
      });
    });
  });

  it('pre-fills existing schedule values', () => {
    const chore = createChore({ schedule_type: 'time', schedule_value: 7 });

    render(<ChoreScheduleConfig chore={chore} projectId="PVT_1" onDone={onDone} />, {
      wrapper: createWrapper(),
    });

    const typeSelect = screen.getByLabelText('Schedule type') as HTMLSelectElement;
    const valueInput = screen.getByLabelText('Schedule value') as HTMLInputElement;

    expect(typeSelect.value).toBe('time');
    expect(valueInput.value).toBe('7');
  });

  it('shows API error on save failure', async () => {
    const user = userEvent.setup();
    mockUpdate.mockRejectedValue(new Error('Validation failed'));

    render(<ChoreScheduleConfig chore={createChore()} projectId="PVT_1" onDone={onDone} />, {
      wrapper: createWrapper(),
    });

    await user.selectOptions(screen.getByLabelText('Schedule type'), 'time');
    await user.type(screen.getByLabelText('Schedule value'), '14');
    await user.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(screen.getByText('Validation failed')).toBeInTheDocument();
    });
  });
});
