/**
 * Integration tests for Card component rendering and structure.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './card';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('Card', () => {
  it('renders card with all sections', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Title</CardTitle>
          <CardDescription>Test description</CardDescription>
        </CardHeader>
        <CardContent>Content here</CardContent>
        <CardFooter>Footer here</CardFooter>
      </Card>
    );

    expect(screen.getByRole('heading', { name: 'Test Title' })).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
    expect(screen.getByText('Content here')).toBeInTheDocument();
    expect(screen.getByText('Footer here')).toBeInTheDocument();
  });

  it('applies border and shadow styling', () => {
    const { container } = render(<Card>Card content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('rounded-[1.25rem]');
    expect(card.className).toContain('border');
    expect(card.className).toContain('shadow-sm');
  });

  it('renders CardTitle as h3 heading', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>My Title</CardTitle>
        </CardHeader>
      </Card>
    );
    const heading = screen.getByRole('heading', { level: 3, name: 'My Title' });
    expect(heading).toBeInTheDocument();
  });

  it('forwards ref on Card', () => {
    const ref = { current: null as HTMLDivElement | null };
    render(<Card ref={ref}>Ref test</Card>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Test Title</CardTitle>
          <CardDescription>Test description</CardDescription>
        </CardHeader>
        <CardContent>Content here</CardContent>
        <CardFooter>Footer here</CardFooter>
      </Card>
    );
    await expectNoA11yViolations(container);
  });
});
