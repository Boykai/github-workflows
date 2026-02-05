/**
 * Unit tests for the EmojiPicker component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EmojiPicker } from './EmojiPicker';

describe('EmojiPicker', () => {
  it('renders emoji picker button', () => {
    const mockOnSelect = vi.fn();
    render(<EmojiPicker onEmojiSelect={mockOnSelect} />);
    
    const button = screen.getByLabelText('Open emoji picker');
    expect(button).toBeTruthy();
  });

  it('opens panel when button is clicked', () => {
    const mockOnSelect = vi.fn();
    render(<EmojiPicker onEmojiSelect={mockOnSelect} />);
    
    const button = screen.getByLabelText('Open emoji picker');
    fireEvent.click(button);
    
    expect(screen.getByText('Positive')).toBeTruthy();
    expect(screen.getByText('Actions')).toBeTruthy();
  });

  it('displays sunshine emoji in picker', () => {
    const mockOnSelect = vi.fn();
    render(<EmojiPicker onEmojiSelect={mockOnSelect} />);
    
    const button = screen.getByLabelText('Open emoji picker');
    fireEvent.click(button);
    
    const sunshineButton = screen.getByLabelText('Sunshine');
    expect(sunshineButton).toBeTruthy();
    expect(sunshineButton.textContent).toBe('☀️');
  });

  it('calls onEmojiSelect when emoji is clicked', () => {
    const mockOnSelect = vi.fn();
    render(<EmojiPicker onEmojiSelect={mockOnSelect} />);
    
    const button = screen.getByLabelText('Open emoji picker');
    fireEvent.click(button);
    
    const sunshineButton = screen.getByLabelText('Sunshine');
    fireEvent.click(sunshineButton);
    
    expect(mockOnSelect).toHaveBeenCalledWith('☀️');
  });

  it('closes panel after emoji selection', () => {
    const mockOnSelect = vi.fn();
    render(<EmojiPicker onEmojiSelect={mockOnSelect} />);
    
    const triggerButton = screen.getByLabelText('Open emoji picker');
    fireEvent.click(triggerButton);
    
    expect(screen.getByText('Positive')).toBeTruthy();
    
    const sunshineButton = screen.getByLabelText('Sunshine');
    fireEvent.click(sunshineButton);
    
    expect(screen.queryByText('Positive')).toBeNull();
  });

  it('closes panel when clicking outside', () => {
    const mockOnSelect = vi.fn();
    const { container } = render(<EmojiPicker onEmojiSelect={mockOnSelect} />);
    
    const button = screen.getByLabelText('Open emoji picker');
    fireEvent.click(button);
    
    expect(screen.getByText('Positive')).toBeTruthy();
    
    fireEvent.mouseDown(container);
    
    expect(screen.queryByText('Positive')).toBeNull();
  });

  it('displays all emoji categories', () => {
    const mockOnSelect = vi.fn();
    render(<EmojiPicker onEmojiSelect={mockOnSelect} />);
    
    const button = screen.getByLabelText('Open emoji picker');
    fireEvent.click(button);
    
    // Check for sunshine emoji in Positive category
    expect(screen.getByLabelText('Sunshine')).toBeTruthy();
    
    // Check for other emojis in their categories
    expect(screen.getByLabelText('Thumbs Up')).toBeTruthy();
    expect(screen.getByLabelText('Rocket')).toBeTruthy();
  });
});
