/**
 * Integration tests for Input component interactive states.
 */

import { describe, it, expect } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { Input } from './input';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('Input', () => {
  it('renders with placeholder text', () => {
    render(<Input placeholder="Enter text..." />);
    expect(screen.getByPlaceholderText('Enter text...')).toBeInTheDocument();
  });

  it('accepts and displays user input', async () => {
    const user = userEvent.setup();
    render(<Input placeholder="Type here" />);
    const input = screen.getByPlaceholderText('Type here');
    await user.type(input, 'Hello');
    expect(input).toHaveValue('Hello');
  });

  it('renders in disabled state', () => {
    render(<Input disabled placeholder="Disabled" />);
    const input = screen.getByPlaceholderText('Disabled');
    expect(input).toBeDisabled();
    expect(input.className).toContain('disabled:cursor-not-allowed');
    expect(input.className).toContain('disabled:opacity-50');
  });

  it('includes celestial-focus class for accessible focus ring', () => {
    render(<Input placeholder="Focus test" />);
    const input = screen.getByPlaceholderText('Focus test');
    expect(input.className).toContain('celestial-focus');
  });

  it('forwards ref correctly', () => {
    const ref = { current: null as HTMLInputElement | null };
    render(<Input ref={ref} placeholder="Ref" />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it('applies custom className', () => {
    render(<Input className="custom-class" placeholder="Custom" />);
    expect(screen.getByPlaceholderText('Custom').className).toContain('custom-class');
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<Input placeholder="A11y test" />);
    await expectNoA11yViolations(container);
  });
});
