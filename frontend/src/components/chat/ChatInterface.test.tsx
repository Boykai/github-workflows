/**
 * Unit tests for ChatInterface component - focusing on emoji button functionality
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';

describe('ChatInterface - Emoji Button', () => {
  beforeEach(() => {
    // Mock scrollIntoView which is not available in test environment
    Element.prototype.scrollIntoView = vi.fn();
  });
  const mockProps = {
    messages: [],
    pendingProposals: new Map(),
    pendingStatusChanges: new Map(),
    pendingRecommendations: new Map(),
    isSending: false,
    onSendMessage: vi.fn(),
    onConfirmProposal: vi.fn(),
    onConfirmStatusChange: vi.fn(),
    onConfirmRecommendation: vi.fn(),
    onRejectProposal: vi.fn(),
    onRejectRecommendation: vi.fn(),
    onNewChat: vi.fn(),
  };

  it('should render emoji button in the message composer', () => {
    render(<ChatInterface {...mockProps} />);
    
    const emojiButton = screen.getByRole('button', { name: /insert smiley face emoji/i });
    expect(emojiButton).toBeTruthy();
    expect(emojiButton.textContent).toBe('😊');
  });

  it('should insert emoji at cursor position when button is clicked', () => {
    render(<ChatInterface {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/describe a task to create/i) as HTMLTextAreaElement;
    const emojiButton = screen.getByRole('button', { name: /insert smiley face emoji/i });

    // Type some text
    fireEvent.change(textarea, { target: { value: 'Hello world' } });
    
    // Set cursor position (middle of text)
    textarea.selectionStart = 5;
    textarea.selectionEnd = 5;
    
    // Click emoji button
    fireEvent.click(emojiButton);
    
    // Check that emoji was inserted at cursor position
    expect(textarea.value).toBe('Hello😊 world');
  });

  it('should insert emoji at the end when no cursor position is set', () => {
    render(<ChatInterface {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/describe a task to create/i) as HTMLTextAreaElement;
    const emojiButton = screen.getByRole('button', { name: /insert smiley face emoji/i });

    // Type some text
    fireEvent.change(textarea, { target: { value: 'Hello' } });
    
    // Click emoji button (cursor should be at end by default)
    fireEvent.click(emojiButton);
    
    // Check that emoji was inserted at the end
    expect(textarea.value).toBe('Hello😊');
  });

  it('should insert emoji in empty textarea', () => {
    render(<ChatInterface {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/describe a task to create/i) as HTMLTextAreaElement;
    const emojiButton = screen.getByRole('button', { name: /insert smiley face emoji/i });

    // Click emoji button with empty textarea
    fireEvent.click(emojiButton);
    
    // Check that emoji was inserted
    expect(textarea.value).toBe('😊');
  });

  it('should be disabled when isSending is true', () => {
    render(<ChatInterface {...mockProps} isSending={true} />);
    
    const emojiButton = screen.getByRole('button', { name: /insert smiley face emoji/i });
    expect(emojiButton.hasAttribute('disabled')).toBe(true);
  });

  it('should be keyboard accessible', () => {
    render(<ChatInterface {...mockProps} />);
    
    const emojiButton = screen.getByRole('button', { name: /insert smiley face emoji/i });
    
    // Check that button has proper aria-label
    expect(emojiButton.getAttribute('aria-label')).toBe('Insert smiley face emoji');
    
    // Check that button has title for tooltip
    expect(emojiButton.getAttribute('title')).toBe('Insert smiley face emoji');
  });
});
