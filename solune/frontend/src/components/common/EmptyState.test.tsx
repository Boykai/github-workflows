import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { EmptyState } from './EmptyState';
import { Package } from '@/lib/icons';

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(
      <EmptyState
        icon={Package}
        title="No items yet"
        description="Create your first item to get started."
      />
    );
    expect(screen.getByText('No items yet')).toBeInTheDocument();
    expect(screen.getByText('Create your first item to get started.')).toBeInTheDocument();
  });

  it('renders CTA button when actionLabel and onAction are provided', () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        icon={Package}
        title="No items"
        description="Get started."
        actionLabel="Create item"
        onAction={handleAction}
      />
    );
    expect(screen.getByRole('button', { name: 'Create item' })).toBeInTheDocument();
  });

  it('calls onAction when CTA is clicked', async () => {
    const handleAction = vi.fn();
    const user = userEvent.setup();
    render(
      <EmptyState
        icon={Package}
        title="No items"
        description="Get started."
        actionLabel="Create item"
        onAction={handleAction}
      />
    );
    await user.click(screen.getByRole('button', { name: 'Create item' }));
    expect(handleAction).toHaveBeenCalledOnce();
  });

  it('does not render CTA when actionLabel is missing', () => {
    render(
      <EmptyState
        icon={Package}
        title="No items"
        description="Get started."
      />
    );
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
