/**
 * Integration tests for Button component interactive states.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { Button } from './button';

describe('Button', () => {
  it('renders with default variant', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Button variant="destructive">Delete</Button>);
    const btn = screen.getByRole('button', { name: 'Delete' });
    expect(btn.className).toContain('bg-destructive');

    rerender(<Button variant="outline">Outline</Button>);
    const outlineBtn = screen.getByRole('button', { name: 'Outline' });
    expect(outlineBtn.className).toContain('border');
  });

  it('renders in disabled state with correct styling', () => {
    render(<Button disabled>Disabled</Button>);
    const btn = screen.getByRole('button', { name: 'Disabled' });
    expect(btn).toBeDisabled();
    expect(btn.className).toContain('disabled:pointer-events-none');
    expect(btn.className).toContain('disabled:opacity-50');
  });

  it('includes focus-visible ring classes for accessibility', () => {
    render(<Button>Focus me</Button>);
    const btn = screen.getByRole('button', { name: 'Focus me' });
    expect(btn.className).toContain('focus-visible:ring-2');
  });

  it('applies size variants', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button', { name: 'Small' }).className).toContain('h-9');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button', { name: 'Large' }).className).toContain('h-11');

    rerender(<Button size="icon">Icon</Button>);
    expect(screen.getByRole('button', { name: 'Icon' }).className).toContain('w-10');
  });

  it('forwards ref correctly', () => {
    const ref = { current: null as HTMLButtonElement | null };
    render(<Button ref={ref}>Ref test</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });
});
