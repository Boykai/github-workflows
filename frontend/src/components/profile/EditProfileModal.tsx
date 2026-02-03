/**
 * Edit Profile Modal component
 */

import { useState } from 'react';
import { authApi } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import type { User } from '@/types';
import './EditProfileModal.css';

interface EditProfileModalProps {
  user: User;
  onClose: () => void;
}

export function EditProfileModal({ user, onClose }: EditProfileModalProps) {
  const { refetch } = useAuth();
  const [username, setUsername] = useState(user.github_username);
  const [avatarUrl, setAvatarUrl] = useState(user.github_avatar_url || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{
    username?: string;
    avatarUrl?: string;
  }>({});

  const validateForm = () => {
    const errors: { username?: string; avatarUrl?: string } = {};

    // Username validation
    if (!username || username.trim().length === 0) {
      errors.username = 'Username is required';
    } else if (username.length > 39) {
      errors.username = 'Username must be 39 characters or less';
    } else if (!/^[a-zA-Z0-9-]+$/.test(username)) {
      errors.username = 'Username can only contain letters, numbers, and hyphens';
    }

    // Avatar URL validation (optional)
    if (avatarUrl && avatarUrl.trim().length > 0) {
      try {
        new URL(avatarUrl);
      } catch {
        errors.avatarUrl = 'Please enter a valid URL';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await authApi.updateProfile({
        github_username: username.trim(),
        github_avatar_url: avatarUrl.trim() || undefined,
      });

      setSuccess(true);
      // Refetch user data to update the UI
      await refetch();
      
      // Close modal after a brief delay to show success message
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit Profile</h2>
          <button
            className="modal-close"
            onClick={handleCancel}
            disabled={isSubmitting}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="profile-form">
          <div className="form-group">
            <label htmlFor="username">
              Username <span className="required">*</span>
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isSubmitting}
              className={validationErrors.username ? 'error' : ''}
              placeholder="Enter username"
              maxLength={39}
            />
            {validationErrors.username && (
              <span className="field-error">{validationErrors.username}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="avatarUrl">Avatar URL</label>
            <input
              id="avatarUrl"
              type="text"
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              disabled={isSubmitting}
              className={validationErrors.avatarUrl ? 'error' : ''}
              placeholder="https://example.com/avatar.png"
            />
            {validationErrors.avatarUrl && (
              <span className="field-error">{validationErrors.avatarUrl}</span>
            )}
          </div>

          {error && (
            <div className="error-message">
              <span>⚠️ {error}</span>
            </div>
          )}

          {success && (
            <div className="success-message">
              <span>✓ Profile updated successfully!</span>
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              onClick={handleCancel}
              disabled={isSubmitting}
              className="button-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="button-primary"
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
