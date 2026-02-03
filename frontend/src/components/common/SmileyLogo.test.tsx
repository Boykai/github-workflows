/**
 * Unit tests for SmileyLogo component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SmileyLogo } from './SmileyLogo';

describe('SmileyLogo', () => {
  it('renders the smiley logo', () => {
    render(<SmileyLogo />);
    const logo = screen.getByLabelText('Smiley face logo');
    expect(logo).toBeTruthy();
  });

  it('displays tooltip text on title attribute', () => {
    render(<SmileyLogo />);
    const logoContainer = screen.getByTitle('Welcome!');
    expect(logoContainer).toBeTruthy();
  });

  it('renders with default size of 32', () => {
    render(<SmileyLogo />);
    const svg = screen.getByLabelText('Smiley face logo');
    expect(svg.getAttribute('width')).toBe('32');
    expect(svg.getAttribute('height')).toBe('32');
  });

  it('renders with custom size when provided', () => {
    render(<SmileyLogo size={48} />);
    const svg = screen.getByLabelText('Smiley face logo');
    expect(svg.getAttribute('width')).toBe('48');
    expect(svg.getAttribute('height')).toBe('48');
  });

  it('has correct viewBox for scalability', () => {
    render(<SmileyLogo />);
    const svg = screen.getByLabelText('Smiley face logo');
    expect(svg.getAttribute('viewBox')).toBe('0 0 100 100');
  });
});
