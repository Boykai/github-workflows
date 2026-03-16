/**
 * Integration tests for SettingsSection save state lifecycle.
 */

import { describe, it, expect, vi } from 'vitest';
import { act, render, screen, userEvent, waitFor } from '@/test/test-utils';
import { ApiError } from '@/services/api';
import { SettingsSection } from './SettingsSection';

describe('SettingsSection', () => {
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
    const toggle = screen.getByRole('button', { name: 'Expand Collapsible' });

    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Hidden content')).not.toBeInTheDocument();

    await userEvent.setup().click(toggle);

    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Hidden content')).toBeInTheDocument();
  });

  it('disables save button when not dirty', () => {
    render(
      <SettingsSection title="Test" onSave={vi.fn()} isDirty={false}>
        <div>Content</div>
      </SettingsSection>
    );
    expect(screen.getByRole('button', { name: 'Save Settings' })).toBeDisabled();
  });

  it('enables save button when dirty', () => {
    render(
      <SettingsSection title="Test" onSave={vi.fn()} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );
    expect(screen.getByRole('button', { name: 'Save Settings' })).toBeEnabled();
  });

  it('shows success message after save', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <SettingsSection title="Test" onSave={onSave} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Save Settings' }));
    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent('Saved!');
    });
  });

  it('shows error message after failed save', async () => {
    const onSave = vi.fn().mockRejectedValue(new Error('fail'));
    render(
      <SettingsSection title="Test" onSave={onSave} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Save Settings' }));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Could not save settings. Please try again.'
      );
    });
  });

  it('shows a rate-limit message after rate-limited save failures', async () => {
    const onSave = vi.fn().mockRejectedValue(
      new ApiError(429, { error: 'Too many requests' })
    );

    render(
      <SettingsSection title="Test" onSave={onSave} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Save Settings' }));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Too many requests. Please wait a moment and try again.'
      );
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

    await userEvent.setup().click(screen.getByRole('button', { name: 'Save Settings' }));
    expect(screen.getByRole('button', { name: 'Saving…' })).toBeDisabled();
    await act(async () => {
      resolverFn?.();
    });
  });

  it('hides save button when hideSave is true', () => {
    render(
      <SettingsSection title="Test" onSave={vi.fn()} hideSave={true}>
        <div>Content</div>
      </SettingsSection>
    );
    expect(screen.queryByRole('button', { name: 'Save Settings' })).not.toBeInTheDocument();
  });
});
