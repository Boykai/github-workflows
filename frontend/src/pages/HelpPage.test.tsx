/**
 * Tests for the HelpPage component.
 *
 * Covers: hero rendering, getting started section, FAQ display,
 * category filtering, accordion expand/collapse, support channels,
 * pipeline overview, and celestial theme classes.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { HelpPage } from './HelpPage';

describe('HelpPage', () => {
  it('renders the hero with eyebrow and title', () => {
    render(<HelpPage />);
    expect(screen.getByText('Support Center')).toBeInTheDocument();
    expect(screen.getByText('Help & guidance for Solune.')).toBeInTheDocument();
  });

  it('renders FAQ stats in the hero', () => {
    render(<HelpPage />);
    expect(screen.getByText('FAQ topics')).toBeInTheDocument();
    expect(screen.getByText('Categories')).toBeInTheDocument();
  });

  it('renders the Getting Started section', () => {
    render(<HelpPage />);
    expect(screen.getByText('Getting Started')).toBeInTheDocument();
    expect(screen.getByText(/Clone & configure/)).toBeInTheDocument();
    expect(screen.getByText(/Start the app/)).toBeInTheDocument();
    expect(screen.getByText(/Sign in/)).toBeInTheDocument();
  });

  it('renders the FAQ section with all items by default', () => {
    render(<HelpPage />);
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
    expect(screen.getByText('How do I create a GitHub OAuth App?')).toBeInTheDocument();
    expect(screen.getByText('What is the agent pipeline?')).toBeInTheDocument();
    expect(screen.getByText('How do I contribute to this project?')).toBeInTheDocument();
  });

  it('renders category filter chips', () => {
    render(<HelpPage />);
    expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Setup' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Usage' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pipeline' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Contributing' })).toBeInTheDocument();
  });

  it('filters FAQ items by category', async () => {
    const user = userEvent.setup();
    render(<HelpPage />);

    await user.click(screen.getByRole('button', { name: 'Pipeline' }));

    // Pipeline questions should be visible
    expect(screen.getByText('What is the agent pipeline?')).toBeInTheDocument();
    expect(screen.getByText('Why is my pipeline not advancing?')).toBeInTheDocument();

    // Setup question should not be visible
    expect(screen.queryByText('How do I create a GitHub OAuth App?')).not.toBeInTheDocument();
  });

  it('shows all FAQ items when All filter is clicked', async () => {
    const user = userEvent.setup();
    render(<HelpPage />);

    // First filter to a category
    await user.click(screen.getByRole('button', { name: 'Setup' }));
    expect(screen.queryByText('What is the agent pipeline?')).not.toBeInTheDocument();

    // Click All to reset
    await user.click(screen.getByRole('button', { name: 'All' }));
    expect(screen.getByText('What is the agent pipeline?')).toBeInTheDocument();
    expect(screen.getByText('How do I create a GitHub OAuth App?')).toBeInTheDocument();
  });

  it('expands and collapses FAQ accordion items', async () => {
    const user = userEvent.setup();
    render(<HelpPage />);

    const faqButton = screen.getByRole('button', { name: /How do I create a GitHub OAuth App/ });
    expect(faqButton).toHaveAttribute('aria-expanded', 'false');

    await user.click(faqButton);
    expect(faqButton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/Go to GitHub Developer Settings/)).toBeInTheDocument();

    await user.click(faqButton);
    expect(faqButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('renders the Support Channels section', () => {
    render(<HelpPage />);
    expect(screen.getByText('Support Channels')).toBeInTheDocument();
    expect(screen.getByText('GitHub Issues')).toBeInTheDocument();
    expect(screen.getByText('GitHub Discussions')).toBeInTheDocument();
  });

  it('renders the Agent Pipeline overview section', () => {
    render(<HelpPage />);
    expect(screen.getByText('Agent Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Backlog')).toBeInTheDocument();
    expect(screen.getByText('In Review')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();
  });

  it('renders external links with correct attributes', () => {
    render(<HelpPage />);
    const issuesLink = screen.getByRole('link', { name: /GitHub Issues/ });
    expect(issuesLink).toHaveAttribute('target', '_blank');
    expect(issuesLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('applies celestial-fade-in animation class', () => {
    const { container } = render(<HelpPage />);
    expect(container.querySelector('.celestial-fade-in')).toBeInTheDocument();
  });

  it('applies celestial-panel class to content panels', () => {
    const { container } = render(<HelpPage />);
    const panels = container.querySelectorAll('.celestial-panel');
    expect(panels.length).toBeGreaterThanOrEqual(3);
  });

  it('renders hero action buttons', () => {
    render(<HelpPage />);
    const startedLink = screen.getByRole('link', { name: 'Getting started' });
    expect(startedLink).toHaveAttribute('href', '#getting-started');

    const faqLink = screen.getByRole('link', { name: 'Browse FAQ' });
    expect(faqLink).toHaveAttribute('href', '#faq');
  });
});
