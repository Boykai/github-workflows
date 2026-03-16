import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { AppCard } from './AppCard';
import type { App } from '@/types/apps';

const baseApp: App = {
  name: 'test-app',
  display_name: 'Test App',
  description: 'A test application',
  directory_path: '/apps/test-app',
  associated_pipeline_id: null,
  status: 'stopped',
  repo_type: 'same-repo',
  external_repo_url: null,
  port: 3000,
  error_message: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const handlers = {
  onSelect: vi.fn(),
  onStart: vi.fn(),
  onStop: vi.fn(),
  onDelete: vi.fn(),
};

describe('AppCard', () => {
  it('renders the app name and description', () => {
    render(<AppCard app={baseApp} {...handlers} />);
    expect(screen.getByText('Test App')).toBeInTheDocument();
    expect(screen.getByText('A test application')).toBeInTheDocument();
  });

  it('shows the status badge', () => {
    render(<AppCard app={baseApp} {...handlers} />);
    expect(screen.getByText('Stopped')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<AppCard app={baseApp} {...handlers} />);
    await expectNoA11yViolations(container);
  });
});
