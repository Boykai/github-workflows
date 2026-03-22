/**
 * Integration tests for SettingsSection save state lifecycle.
 */

import { act, fireEvent, render, screen, userEvent, waitFor } from '@/test/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SettingsSection } from './SettingsSection';

describe('SettingsSection', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders title and description', () => {
    render(
      <SettingsSection title="AI Settings" description="Configure AI preferences">
        <div>Content</div>
      </SettingsSection>
    );
    expect(screen.getByRole('heading', { name: 'AI Settings' })).toBeInTheDocument();
    expect(screen.getByText('Configure AI preferences')).toBeInTheDocument();
  });

  it('renders children content when expanded', () => {
    render(
      <SettingsSection title="Test">
        <div>Child content</div>
      </SettingsSection>
    );
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('collapses and expands on header click', async () => {
    render(
      <SettingsSection title="Collapsible" defaultCollapsed={true}>
        <div>Hidden content</div>
      </SettingsSection>
    );
    expect(screen.queryByText('Hidden content')).not.toBeInTheDocument();

    await userEvent.setup().click(screen.getByRole('button', { name: /Collapsible/i }));
    expect(screen.getByText('Hidden content')).toBeInTheDocument();
  });

  it('disables save button when not dirty', () => {
    render(
      <SettingsSection title="Test" onSave={vi.fn()} isDirty={false}>
        <div>Content</div>
      </SettingsSection>
    );
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
  });

  it('enables save button when dirty', () => {
    render(
      <SettingsSection title="Test" onSave={vi.fn()} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
  });

  it('shows success message after save', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <SettingsSection title="Test" onSave={onSave} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => {
      expect(screen.getByText('Saved!')).toBeInTheDocument();
    });
  });

  it('shows error message after failed save', async () => {
    const onSave = vi.fn().mockRejectedValue(new Error('fail'));
    render(
      <SettingsSection title="Test" onSave={onSave} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => {
      expect(screen.getByText('Failed to save')).toBeInTheDocument();
    });
  });

  it('shows Saving... text during save', async () => {
    let resolverFn: (() => void) | undefined;
    const onSave = vi.fn().mockImplementation(
      () =>
        new Promise<void>((r) => {
          resolverFn = r;
        })
    );
    render(
      <SettingsSection title="Test" onSave={onSave} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Save' }));
    expect(screen.getByText('Saving...')).toBeInTheDocument();
    await act(async () => {
      resolverFn?.();
    });
  });

  it('clears the save-status timer on unmount', async () => {
    vi.useFakeTimers();
    const onSave = vi.fn().mockResolvedValue(undefined);
    const { unmount } = render(
      <SettingsSection title="Test" onSave={onSave} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Save' }));
      await Promise.resolve();
    });

    expect(screen.getByText('Saved!')).toBeInTheDocument();
    expect(vi.getTimerCount()).toBe(1);

    unmount();

    expect(vi.getTimerCount()).toBe(0);
  });

  it('hides save button when hideSave is true', () => {
    render(
      <SettingsSection title="Test" onSave={vi.fn()} hideSave={true}>
        <div>Content</div>
      </SettingsSection>
    );
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
  });
});
