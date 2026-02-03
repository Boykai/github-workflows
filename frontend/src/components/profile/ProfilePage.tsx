/**
 * User profile page component for viewing and editing personal information.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { authApi } from '@/services/api';
import './ProfilePage.css';

export function ProfilePage() {
  const { user, refetch } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    display_name: user?.display_name || '',
    github_avatar_url: user?.github_avatar_url || '',
  });

  // Sync form data when user changes
  useEffect(() => {
    if (user) {
      setFormData({
        display_name: user.display_name || '',
        github_avatar_url: user.github_avatar_url || '',
      });
    }
  }, [user]);

  const handleEdit = () => {
    setFormData({
      display_name: user?.display_name || '',
      github_avatar_url: user?.github_avatar_url || '',
    });
    setIsEditing(true);
    setError(null);
    setSuccess(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
    setSuccess(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsLoading(true);

    // Validation
    if (formData.display_name.trim().length === 0) {
      setError('Display name cannot be empty');
      setIsLoading(false);
      return;
    }

    if (formData.display_name.length > 100) {
      setError('Display name must be 100 characters or less');
      setIsLoading(false);
      return;
    }

    if (formData.github_avatar_url && !formData.github_avatar_url.startsWith('http')) {
      setError('Avatar URL must be a valid HTTP/HTTPS URL');
      setIsLoading(false);
      return;
    }

    try {
      await authApi.updateProfile({
        display_name: formData.display_name || undefined,
        github_avatar_url: formData.github_avatar_url || undefined,
      });
      
      await refetch();
      setIsEditing(false);
      setSuccess('Profile updated successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="profile-page">
      <div className="profile-card">
        <div className="profile-header">
          <h1>Profile</h1>
          {!isEditing && (
            <button onClick={handleEdit} className="edit-button">
              Edit
            </button>
          )}
        </div>

        {success && (
          <div className="success-message">
            {success}
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {isEditing ? (
          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-field">
              <label htmlFor="avatar">Avatar</label>
              <div className="avatar-field">
                {formData.github_avatar_url && (
                  <img
                    src={formData.github_avatar_url}
                    alt="Avatar preview"
                    className="avatar-preview"
                  />
                )}
                <input
                  id="avatar"
                  type="url"
                  value={formData.github_avatar_url}
                  onChange={(e) => setFormData({ ...formData, github_avatar_url: e.target.value })}
                  placeholder="https://..."
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="form-field">
              <label htmlFor="displayName">Display Name *</label>
              <input
                id="displayName"
                type="text"
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                placeholder="Your display name"
                required
                disabled={isLoading}
                maxLength={100}
              />
            </div>

            <div className="form-field">
              <label>Username</label>
              <input
                type="text"
                value={user.github_username}
                disabled
                className="readonly-field"
              />
              <span className="field-hint">From GitHub (read-only)</span>
            </div>

            <div className="form-field">
              <label>Email</label>
              <input
                type="email"
                value={user.github_email || 'Not available'}
                disabled
                className="readonly-field"
              />
              <span className="field-hint">From GitHub (read-only)</span>
            </div>

            <div className="form-actions">
              <button
                type="button"
                onClick={handleCancel}
                className="cancel-button"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="save-button"
                disabled={isLoading}
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        ) : (
          <div className="profile-view">
            <div className="profile-field">
              <label>Avatar</label>
              <div className="avatar-display">
                {user.github_avatar_url ? (
                  <img
                    src={user.github_avatar_url}
                    alt={user.github_username}
                    className="avatar-large"
                  />
                ) : (
                  <div className="avatar-placeholder">No avatar</div>
                )}
              </div>
            </div>

            <div className="profile-field">
              <label>Display Name</label>
              <div className="field-value">{user.display_name || 'Not set'}</div>
            </div>

            <div className="profile-field">
              <label>Username</label>
              <div className="field-value">{user.github_username}</div>
            </div>

            <div className="profile-field">
              <label>Email</label>
              <div className="field-value">{user.github_email || 'Not available'}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
