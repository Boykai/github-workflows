/**
 * Error display component for API failures.
 */

import { useEffect, useState } from 'react';

interface ErrorToastProps {
  error: Error | null;
  onDismiss: () => void;
}

export function ErrorToast({ error, onDismiss }: ErrorToastProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (error) {
      setIsVisible(true);
      // Auto-dismiss after 5 seconds
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onDismiss, 300); // Allow fade-out animation
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, onDismiss]);

  if (!error) return null;

  // Parse error message for user-friendly display
  const message = getUserFriendlyMessage(error);

  return (
    <div className={`error-toast ${isVisible ? 'visible' : ''}`} role="alert">
      <div className="error-toast-icon">⚠️</div>
      <div className="error-toast-content">
        <span className="error-toast-message">{message}</span>
      </div>
      <button
        className="error-toast-dismiss"
        onClick={() => {
          setIsVisible(false);
          setTimeout(onDismiss, 300);
        }}
        aria-label="Dismiss error"
      >
        ×
      </button>
    </div>
  );
}

interface ErrorBannerProps {
  error: Error | null;
  retry?: () => void;
}

export function ErrorBanner({ error, retry }: ErrorBannerProps) {
  if (!error) return null;

  const message = getUserFriendlyMessage(error);

  return (
    <div className="error-banner" role="alert">
      <div className="error-banner-icon">⚠️</div>
      <div className="error-banner-content">
        <span className="error-banner-title">Something went wrong</span>
        <span className="error-banner-message">{message}</span>
      </div>
      {retry && (
        <button className="error-banner-retry" onClick={retry}>
          Try Again
        </button>
      )}
    </div>
  );
}

function getUserFriendlyMessage(error: Error): string {
  const message = error.message.toLowerCase();

  // Authentication errors
  if (message.includes('authentication') || message.includes('401')) {
    return 'Your session has expired. Please log in again.';
  }

  // Authorization errors
  if (message.includes('access denied') || message.includes('403')) {
    return "You don't have permission to perform this action.";
  }

  // Not found errors
  if (message.includes('not found') || message.includes('404')) {
    return 'The requested resource was not found.';
  }

  // Rate limit errors
  if (message.includes('rate limit') || message.includes('429')) {
    return 'Too many requests. Please wait a moment and try again.';
  }

  // GitHub API errors
  if (message.includes('github') || message.includes('502')) {
    return 'Unable to connect to GitHub. Please check your connection and try again.';
  }

  // Network errors
  if (message.includes('network') || message.includes('fetch')) {
    return 'Network error. Please check your internet connection.';
  }

  // Validation errors
  if (message.includes('validation') || message.includes('422')) {
    return 'Invalid input. Please check your data and try again.';
  }

  // Server errors
  if (message.includes('500') || message.includes('internal')) {
    return 'Server error. Please try again later.';
  }

  // Default message
  return error.message || 'An unexpected error occurred. Please try again.';
}
