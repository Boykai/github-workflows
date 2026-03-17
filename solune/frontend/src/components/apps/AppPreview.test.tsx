import { describe, it, expect } from 'vitest';
import { fireEvent, render, screen } from '@/test/test-utils';
import { AppPreview } from './AppPreview';

describe('AppPreview', () => {
  it('shows a start prompt when the app is inactive', () => {
    render(<AppPreview port={3000} appName="demo-app" isActive={false} />);

    expect(screen.getByText('Start the app to see a live preview')).toBeInTheDocument();
    expect(screen.queryByTitle('Preview: demo-app')).not.toBeInTheDocument();
  });

  it('shows a missing port message for active apps without a port', () => {
    render(<AppPreview port={null} appName="demo-app" isActive />);

    expect(screen.getByText('No port assigned')).toBeInTheDocument();
  });

  it('renders a sandboxed iframe for active apps with a port', () => {
    render(<AppPreview port={3000} appName="demo-app" isActive />);

    const iframe = screen.getByTitle('Preview: demo-app');
    expect(iframe).toHaveAttribute('src', 'http://localhost:3000');
    expect(iframe).toHaveAttribute(
      'sandbox',
      'allow-scripts allow-same-origin allow-forms allow-popups'
    );
  });

  it('removes the loading overlay after the iframe loads', () => {
    const { container } = render(<AppPreview port={3000} appName="demo-app" isActive />);

    expect(container.querySelector('.animate-spin')).toBeTruthy();

    fireEvent.load(screen.getByTitle('Preview: demo-app'));

    expect(container.querySelector('.animate-spin')).toBeNull();
  });
});