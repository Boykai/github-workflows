/**
 * Unit tests for AgentConfigRow component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentConfigRow } from './AgentConfigRow';
import type { BoardColumn } from '@/types';

vi.mock('@/hooks/useAgentConfig');

vi.mock('./AgentColumnCell', () => ({
  AgentColumnCell: ({ status }: { status: string }) => (
    <div data-testid={`column-cell-${status}`}>{status}</div>
  ),
}));

vi.mock('./AgentSaveBar', () => ({
  AgentSaveBar: () => <div data-testid="save-bar">Save Bar</div>,
}));

function createColumns(): BoardColumn[] {
  return [
    {
      status: { option_id: 'o1', name: 'Todo', color: 'GRAY' },
      items: [],
      item_count: 0,
      estimate_total: 0,
    },
    {
      status: { option_id: 'o2', name: 'In Progress', color: 'BLUE' },
      items: [],
      item_count: 0,
      estimate_total: 0,
    },
  ];
}

function createAgentConfig(overrides: Partial<{
  isLoaded: boolean;
  isDirty: boolean;
  localMappings: Record<string, never[]>;
  isColumnDirty: (s: string) => boolean;
  removeAgent: () => void;
  reorderAgents: () => void;
  save: () => Promise<void>;
  discard: () => void;
  isSaving: boolean;
  saveError: string | null;
}> = {}) {
  return {
    localMappings: {} as Record<string, never[]>,
    isDirty: false,
    isColumnDirty: vi.fn(() => false),
    addAgent: vi.fn(),
    removeAgent: vi.fn(),
    reorderAgents: vi.fn(),
    applyPreset: vi.fn(),
    save: vi.fn().mockResolvedValue(undefined),
    discard: vi.fn(),
    isSaving: false,
    saveError: null,
    isLoaded: true,
    loadConfig: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

describe('AgentConfigRow', () => {
  it('renders loading skeleton when not loaded', () => {
    const { container } = render(
      <AgentConfigRow
        columns={createColumns()}
        agentConfig={createAgentConfig({ isLoaded: false }) as never}
      />
    );
    expect(container.querySelector('.agent-column-cell--skeleton')).not.toBeNull();
  });

  it('renders column cells when loaded', () => {
    render(
      <AgentConfigRow
        columns={createColumns()}
        agentConfig={createAgentConfig() as never}
      />
    );
    expect(screen.getByTestId('column-cell-Todo')).toBeDefined();
    expect(screen.getByTestId('column-cell-In Progress')).toBeDefined();
  });

  it('shows save bar when isDirty', () => {
    render(
      <AgentConfigRow
        columns={createColumns()}
        agentConfig={createAgentConfig({ isDirty: true }) as never}
      />
    );
    expect(screen.getByTestId('save-bar')).toBeDefined();
  });

  it('hides save bar when not isDirty', () => {
    render(
      <AgentConfigRow
        columns={createColumns()}
        agentConfig={createAgentConfig({ isDirty: false }) as never}
      />
    );
    expect(screen.queryByTestId('save-bar')).toBeNull();
  });

  it('toggle expand/collapse works', () => {
    render(
      <AgentConfigRow
        columns={createColumns()}
        agentConfig={createAgentConfig() as never}
      />
    );
    // Initially expanded - column cells visible
    expect(screen.getByTestId('column-cell-Todo')).toBeDefined();
    // Collapse
    fireEvent.click(screen.getByTitle('Collapse agent row'));
    expect(screen.queryByTestId('column-cell-Todo')).toBeNull();
    // Expand
    fireEvent.click(screen.getByTitle('Expand agent row'));
    expect(screen.getByTestId('column-cell-Todo')).toBeDefined();
  });
});
