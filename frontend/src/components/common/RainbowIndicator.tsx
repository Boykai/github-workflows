/**
 * RainbowIndicator Component
 *
 * Displays an animated rainbow graphic when workflows complete successfully.
 * Auto-dismisses after 3 seconds with a fade-out animation.
 * Can be manually dismissed by the user.
 */

import { useEffect, useState } from 'react';
import './RainbowIndicator.css';

interface RainbowIndicatorProps {
  show: boolean;
  onDismiss?: () => void;
}

export function RainbowIndicator({ show, onDismiss }: RainbowIndicatorProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isFading, setIsFading] = useState(false);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      setIsFading(false);
      
      // Start fade out after 3 seconds
      const fadeTimer = setTimeout(() => {
        setIsFading(true);
      }, 3000);

      // Remove component after fade animation (3s + 1s fade)
      const removeTimer = setTimeout(() => {
        setIsVisible(false);
        onDismiss?.();
      }, 4000);

      return () => {
        clearTimeout(fadeTimer);
        clearTimeout(removeTimer);
      };
    }
  }, [show, onDismiss]);

  const handleDismiss = () => {
    setIsFading(true);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss?.();
    }, 1000); // Wait for fade animation
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={`rainbow-indicator ${isFading ? 'fading' : ''}`}
      role="status"
      aria-live="polite"
      aria-label="Success! Workflow completed successfully"
    >
      <div className="rainbow-content">
        <svg
          className="rainbow-graphic"
          viewBox="0 0 200 100"
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label="Rainbow celebration graphic"
        >
          <title>Rainbow</title>
          {/* Rainbow arcs from outer to inner */}
          <path
            d="M 10 90 Q 100 10, 190 90"
            fill="none"
            stroke="#ef4444"
            strokeWidth="8"
            strokeLinecap="round"
            className="rainbow-arc arc-1"
          />
          <path
            d="M 20 90 Q 100 20, 180 90"
            fill="none"
            stroke="#f97316"
            strokeWidth="8"
            strokeLinecap="round"
            className="rainbow-arc arc-2"
          />
          <path
            d="M 30 90 Q 100 30, 170 90"
            fill="none"
            stroke="#fbbf24"
            strokeWidth="8"
            strokeLinecap="round"
            className="rainbow-arc arc-3"
          />
          <path
            d="M 40 90 Q 100 40, 160 90"
            fill="none"
            stroke="#84cc16"
            strokeWidth="8"
            strokeLinecap="round"
            className="rainbow-arc arc-4"
          />
          <path
            d="M 50 90 Q 100 50, 150 90"
            fill="none"
            stroke="#3b82f6"
            strokeWidth="8"
            strokeLinecap="round"
            className="rainbow-arc arc-5"
          />
          <path
            d="M 60 90 Q 100 60, 140 90"
            fill="none"
            stroke="#8b5cf6"
            strokeWidth="8"
            strokeLinecap="round"
            className="rainbow-arc arc-6"
          />
        </svg>
        <span className="success-message">🎉 Success!</span>
        <button
          className="dismiss-button"
          onClick={handleDismiss}
          aria-label="Dismiss celebration"
          type="button"
        >
          ×
        </button>
      </div>
    </div>
  );
}

export default RainbowIndicator;
