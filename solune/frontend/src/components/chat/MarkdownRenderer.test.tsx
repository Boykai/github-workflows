import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { MarkdownRenderer } from './MarkdownRenderer';

describe('MarkdownRenderer', () => {
  it('renders plain markdown text', () => {
    render(<MarkdownRenderer content="Hello **world**" />);

    expect(screen.getByText('world')).toBeInTheDocument();
  });

  it('renders code blocks with a copy button', () => {
    const code = '```javascript\nconsole.log("hello");\n```';
    render(<MarkdownRenderer content={code} />);

    expect(screen.getByText('console.log("hello");')).toBeInTheDocument();
    expect(screen.getByText('javascript')).toBeInTheDocument();
    // CopyButton renders a button with the "Copy code" label
    expect(screen.getByRole('button', { name: /copy code/i })).toBeInTheDocument();
  });

  it('renders links with target="_blank"', () => {
    render(<MarkdownRenderer content="[Click here](https://example.com)" />);

    const link = screen.getByRole('link', { name: 'Click here' });
    expect(link).toHaveAttribute('href', 'https://example.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('renders tables', () => {
    const tableMarkdown = `
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
`;
    render(<MarkdownRenderer content={tableMarkdown} />);

    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('Header 1')).toBeInTheDocument();
    expect(screen.getByText('Cell 1')).toBeInTheDocument();
  });

  it('handles empty content', () => {
    const { container } = render(<MarkdownRenderer content="" />);

    // Should render the wrapper div without errors
    expect(container.querySelector('.prose')).toBeInTheDocument();
  });
});
