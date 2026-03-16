import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { FaqAccordion } from './FaqAccordion';
import type { FaqEntry } from '@/types';

const entries: FaqEntry[] = [
  {
    id: 'faq-1',
    question: 'How do I get started?',
    answer: 'Follow the onboarding tour.',
    category: 'getting-started',
  },
  {
    id: 'faq-2',
    question: 'How do I create a pipeline?',
    answer: 'Go to the Agents page.',
    category: 'agents-pipelines',
  },
];

describe('FaqAccordion', () => {
  it('renders category headings and questions', () => {
    render(<FaqAccordion entries={entries} />);
    expect(screen.getByText('Getting Started')).toBeInTheDocument();
    expect(screen.getByText('Agents & Pipelines')).toBeInTheDocument();
    expect(screen.getByText('How do I get started?')).toBeInTheDocument();
    expect(screen.getByText('How do I create a pipeline?')).toBeInTheDocument();
  });

  it('renders nothing when entries are empty', () => {
    const { container } = render(<FaqAccordion entries={[]} />);
    expect(container.querySelectorAll('button')).toHaveLength(0);
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<FaqAccordion entries={entries} />);
    await expectNoA11yViolations(container);
  });
});
