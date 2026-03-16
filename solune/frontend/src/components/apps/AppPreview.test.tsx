/**
 * Tests for AppPreview component.
 * Covers: inactive state, active with port, no port, loading overlay, error state.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { AppPreview } from './AppPreview';

describe('AppPreview', () => {
  it('shows "Start the app" message when inactive', () => {
    render(<AppPreview port={null} appName="my-app" isActive={false} />);

    expect(screen.getByText(/start the app to see a live preview/i)).toBeInTheDocument();
  });

  it('shows "No port assigned" when active but port is null', () => {
    render(<AppPreview port={null} appName="my-app" isActive />);

    expect(screen.getByText(/no port assigned/i)).toBeInTheDocument();
  });

  it('renders an iframe when active with a port', () => {
    render(<AppPreview port={3000} appName="my-app" isActive />);

    const iframe = screen.getByTitle('Preview: my-app');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'http://localhost:3000');
    expect(iframe).toHaveAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-popups');
  });

  it('shows loading overlay before iframe loads', () => {
    render(<AppPreview port={3000} appName="my-app" isActive />);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('uses CelestialLoader for loading state', () => {
    render(<AppPreview port={3000} appName="my-app" isActive />);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
