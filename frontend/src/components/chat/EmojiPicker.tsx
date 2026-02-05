/**
 * Emoji picker component for chat message input
 */

import { useState, useRef, useEffect } from 'react';
import { chatEmojiRegistry } from '@/constants/chatEmojis';
import './EmojiPicker.css';

interface EmojiPickerProps {
  onEmojiSelect: (emoji: string) => void;
}

export function EmojiPicker({ onEmojiSelect }: EmojiPickerProps) {
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsVisible(false);
      }
    };

    if (isVisible) {
      document.addEventListener('mousedown', handleOutsideClick);
      return () => document.removeEventListener('mousedown', handleOutsideClick);
    }
  }, [isVisible]);

  const handleToggle = () => {
    setIsVisible(prev => !prev);
  };

  const handleEmojiClick = (symbol: string) => {
    onEmojiSelect(symbol);
    setIsVisible(false);
  };

  const availableEmojis = chatEmojiRegistry.getAllForPicker();
  const positiveGroup = availableEmojis.filter(e => e.category === 'positive');
  const actionGroup = availableEmojis.filter(e => e.category === 'action');

  return (
    <div className="emoji-picker-container" ref={containerRef}>
      <button
        type="button"
        onClick={handleToggle}
        className="emoji-picker-trigger"
        aria-label="Open emoji picker"
        title="Add emoji"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M8 14s1.5 2 4 2 4-2 4-2" />
          <line x1="9" y1="9" x2="9.01" y2="9" />
          <line x1="15" y1="9" x2="15.01" y2="9" />
        </svg>
      </button>

      {isVisible && (
        <div className="emoji-picker-panel">
          <div className="emoji-category">
            <div className="emoji-category-label">Positive</div>
            <div className="emoji-grid">
              {positiveGroup.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  className="emoji-option"
                  onClick={() => handleEmojiClick(item.symbol)}
                  title={item.label}
                  aria-label={item.label}
                >
                  {item.symbol}
                </button>
              ))}
            </div>
          </div>

          <div className="emoji-category">
            <div className="emoji-category-label">Actions</div>
            <div className="emoji-grid">
              {actionGroup.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  className="emoji-option"
                  onClick={() => handleEmojiClick(item.symbol)}
                  title={item.label}
                  aria-label={item.label}
                >
                  {item.symbol}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
