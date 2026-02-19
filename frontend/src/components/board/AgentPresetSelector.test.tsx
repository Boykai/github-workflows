/**
 * Unit tests for AgentPresetSelector component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentPresetSelector } from './AgentPresetSelector';

const columnNames = ['Backlog', 'Ready', 'In Progress', 'In Review', 'Done'];
const emptyMappings: Record<string, { slug: string }[]> = {};

describe('AgentPresetSelector', () => {
  it('renders preset buttons (Custom, GitHub Copilot, Spec Kit)', () => {
    render(
      <AgentPresetSelector
        columnNames={columnNames}
        currentMappings={emptyMappings}
        onApplyPreset={vi.fn()}
      />
    );
    expect(screen.getByText('Custom')).toBeDefined();
    expect(screen.getByText('GitHub Copilot')).toBeDefined();
    expect(screen.getByText('Spec Kit')).toBeDefined();
  });

  it('shows confirmation dialog on click', () => {
    render(
      <AgentPresetSelector
        columnNames={columnNames}
        currentMappings={emptyMappings}
        onApplyPreset={vi.fn()}
      />
    );
    fireEvent.click(screen.getByText('GitHub Copilot'));
    expect(screen.getByRole('dialog')).toBeDefined();
    expect(screen.getByText(/Apply .* preset\?/)).toBeDefined();
  });

  it('clicking Cancel closes dialog', () => {
    render(
      <AgentPresetSelector
        columnNames={columnNames}
        currentMappings={emptyMappings}
        onApplyPreset={vi.fn()}
      />
    );
    fireEvent.click(screen.getByText('GitHub Copilot'));
    expect(screen.getByRole('dialog')).toBeDefined();
    fireEvent.click(screen.getByText('Cancel'));
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('clicking Apply calls onApplyPreset', () => {
    const onApplyPreset = vi.fn();
    render(
      <AgentPresetSelector
        columnNames={columnNames}
        currentMappings={emptyMappings}
        onApplyPreset={onApplyPreset}
      />
    );
    fireEvent.click(screen.getByText('GitHub Copilot'));
    fireEvent.click(screen.getByText('Apply Preset'));
    expect(onApplyPreset).toHaveBeenCalledOnce();
    // Should receive a mappings object with column keys
    const mappings = onApplyPreset.mock.calls[0][0];
    expect(mappings).toHaveProperty('In Progress');
    expect(mappings).toHaveProperty('In Review');
  });

  it('active preset button has active class', () => {
    // When all columns are empty, "Custom" matches
    render(
      <AgentPresetSelector
        columnNames={columnNames}
        currentMappings={{
          Backlog: [],
          Ready: [],
          'In Progress': [],
          'In Review': [],
          Done: [],
        }}
        onApplyPreset={vi.fn()}
      />
    );
    const customBtn = screen.getByText('Custom').closest('button')!;
    expect(customBtn.className).toContain('agent-preset-btn--active');
  });
});
