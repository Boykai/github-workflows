/**
 * User Profile Page component
 */

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { EditProfileModal } from './EditProfileModal';
import './ProfilePage.css';

export function ProfilePage() {
  const { user, isLoading } = useAuth();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="profile-loading">
        <div className="spinner" />
        <p>Loading profile...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="profile-error">
        <p>Unable to load profile. Please try logging in again.</p>
      </div>
    );
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="profile-header">
          <h1>User Profile</h1>
          <button 
            className="edit-button" 
            onClick={() => setIsEditModalOpen(true)}
          >
            Edit Profile
          </button>
        </div>

        <div className="profile-content">
          <div className="profile-avatar-section">
            {user.github_avatar_url ? (
              <img
                src={user.github_avatar_url}
                alt={user.github_username}
                className="profile-avatar"
              />
            ) : (
              <div className="profile-avatar-placeholder">
                {user.github_username.charAt(0).toUpperCase()}
              </div>
            )}
          </div>

          <div className="profile-info">
            <div className="profile-field">
              <label>Username</label>
              <p>{user.github_username}</p>
            </div>

            <div className="profile-field">
              <label>User ID</label>
              <p>{user.github_user_id}</p>
            </div>

            <div className="profile-field">
              <label>Account Created</label>
              <p>{formatDate(user.created_at)}</p>
            </div>
          </div>
        </div>
      </div>

      {isEditModalOpen && (
        <EditProfileModal
          user={user}
          onClose={() => setIsEditModalOpen(false)}
        />
      )}
    </div>
  );
}
