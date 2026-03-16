/**
 * Integration tests for SettingsSection save state lifecycle.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
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
      expect(screen.getByText('Settings saved successfully.')).toBeInTheDocument();
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
      expect(screen.getByText('Could not save settings. Please try again.')).toBeInTheDocument();
    });
  });

  it('shows Saving… text during save', async () => {
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
    expect(screen.getByText('Saving…')).toBeInTheDocument();
    resolverFn?.();
  });

  it('hides save button when hideSave is true', () => {
    render(
      <SettingsSection title="Test" onSave={vi.fn()} hideSave={true}>
        <div>Content</div>
      </SettingsSection>
    );
    expect(screen.queryByRole('button', { name: 'Save Settings' })).not.toBeInTheDocument();
  });

  it('sets aria-expanded correctly on the collapse toggle', async () => {
    render(
      <SettingsSection title="Expandable" defaultCollapsed={true}>
        <div>Content</div>
      </SettingsSection>
    );

    const toggle = screen.getByRole('button', { name: /Expandable/i });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');

    await userEvent.setup().click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
  });

  it('renders status messages in an aria-live region', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <SettingsSection title="Test" onSave={onSave} isDirty={true}>
        <div>Content</div>
      </SettingsSection>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Save Settings' }));
    await waitFor(() => {
      const liveRegion = screen.getByText('Settings saved successfully.').closest('[aria-live]');
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
    });
  });
});
