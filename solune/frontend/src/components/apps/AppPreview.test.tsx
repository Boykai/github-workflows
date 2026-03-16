import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { AppPreview } from './AppPreview';

describe('AppPreview', () => {
  it('shows "Start the app" message when app is not active', () => {
    render(<AppPreview port={null} appName="my-app" isActive={false} />);

    expect(screen.getByText('Start the app to see a live preview')).toBeInTheDocument();
    expect(screen.queryByTitle(/preview/i)).not.toBeInTheDocument();
  });

  it('shows "No port assigned" when app is active but port is null', () => {
    render(<AppPreview port={null} appName="my-app" isActive={true} />);

    expect(screen.getByText('No port assigned')).toBeInTheDocument();
    expect(screen.queryByTitle(/preview/i)).not.toBeInTheDocument();
  });

  it('renders an iframe when the app is active and has a port', () => {
    render(<AppPreview port={3000} appName="my-app" isActive={true} />);

    const iframe = screen.getByTitle('Preview: my-app');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'http://localhost:3000');
  });

  it('applies sandbox attributes to the iframe for security', () => {
    render(<AppPreview port={3000} appName="my-app" isActive={true} />);

    const iframe = screen.getByTitle('Preview: my-app');
    expect(iframe).toHaveAttribute(
      'sandbox',
      'allow-scripts allow-same-origin allow-forms allow-popups'
    );
  });

  it('decorative icons have aria-hidden', () => {
    render(<AppPreview port={null} appName="my-app" isActive={false} />);

    const svgs = document.querySelectorAll('svg');
    svgs.forEach((svg) => {
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });
  });
});
