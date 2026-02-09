/**
 * User profile page component.
 * Displays and allows editing of user profile information.
 */

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { authApi } from '@/services/api';
import type { ProfileUpdateRequest } from '@/types';
import './Profile.css';

interface FormErrors {
  email?: string;
  bio?: string;
  contact_phone?: string;
  contact_location?: string;
}

export function Profile() {
  const { user, refetch } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  
  // Form state
  const [formData, setFormData] = useState<ProfileUpdateRequest>({
    email: user?.email || '',
    bio: user?.bio || '',
    contact_phone: user?.contact_phone || '',
    contact_location: user?.contact_location || '',
  });

  if (!user) {
    return null;
  }

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    
    // Email validation
    if (formData.email && formData.email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        newErrors.email = 'Please enter a valid email address';
      }
    }
    
    // Bio validation
    if (formData.bio && formData.bio.length > 500) {
      newErrors.bio = 'Bio must be 500 characters or less';
    }
    
    // Phone validation (basic)
    if (formData.contact_phone && formData.contact_phone.length > 50) {
      newErrors.contact_phone = 'Phone number is too long';
    }
    
    // Location validation
    if (formData.contact_location && formData.contact_location.length > 255) {
      newErrors.contact_location = 'Location is too long';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleEdit = () => {
    setIsEditing(true);
    setSuccessMessage('');
    setErrors({});
    // Reset form data to current user values
    setFormData({
      email: user.email || '',
      bio: user.bio || '',
      contact_phone: user.contact_phone || '',
      contact_location: user.contact_location || '',
    });
  };

  const handleCancel = () => {
    setIsEditing(false);
    setErrors({});
    setSuccessMessage('');
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setIsSaving(true);
    setErrors({});
    setSuccessMessage('');

    try {
      await authApi.updateProfile(formData);
      await refetch();
      setIsEditing(false);
      setSuccessMessage('Profile updated successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccessMessage('');
      }, 3000);
    } catch (error) {
      setErrors({
        email: error instanceof Error ? error.message : 'Failed to update profile',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="profile-container">
      <div className="profile-card">
        <div className="profile-header">
          <h2>Profile</h2>
          {!isEditing && (
            <button className="edit-button" onClick={handleEdit}>
              Edit Profile
            </button>
          )}
        </div>

        {successMessage && (
          <div className="success-message" role="status">
            ✓ {successMessage}
          </div>
        )}

        <div className="profile-content">
          <div className="profile-avatar-section">
            {user.github_avatar_url && (
              <img
                src={user.github_avatar_url}
                alt={user.github_username}
                className="profile-avatar"
              />
            )}
            <div className="profile-username-section">
              <h3>{user.github_username}</h3>
              <span className="profile-user-id">GitHub ID: {user.github_user_id}</span>
            </div>
          </div>

          <div className="profile-fields">
            <div className="profile-field">
              <label htmlFor="email">Email</label>
              {isEditing ? (
                <>
                  <input
                    type="email"
                    id="email"
                    className={errors.email ? 'input-error' : ''}
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="Enter your email"
                  />
                  {errors.email && (
                    <span className="field-error">{errors.email}</span>
                  )}
                </>
              ) : (
                <span className="profile-value">{user.email || 'Not set'}</span>
              )}
            </div>

            <div className="profile-field">
              <label htmlFor="bio">Bio</label>
              {isEditing ? (
                <>
                  <textarea
                    id="bio"
                    className={errors.bio ? 'input-error' : ''}
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    placeholder="Tell us about yourself"
                    rows={4}
                    maxLength={500}
                  />
                  <span className="character-count">
                    {formData.bio?.length || 0} / 500
                  </span>
                  {errors.bio && (
                    <span className="field-error">{errors.bio}</span>
                  )}
                </>
              ) : (
                <span className="profile-value">{user.bio || 'Not set'}</span>
              )}
            </div>

            <div className="profile-field">
              <label htmlFor="contact_phone">Phone</label>
              {isEditing ? (
                <>
                  <input
                    type="tel"
                    id="contact_phone"
                    className={errors.contact_phone ? 'input-error' : ''}
                    value={formData.contact_phone}
                    onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                    placeholder="Enter your phone number"
                  />
                  {errors.contact_phone && (
                    <span className="field-error">{errors.contact_phone}</span>
                  )}
                </>
              ) : (
                <span className="profile-value">{user.contact_phone || 'Not set'}</span>
              )}
            </div>

            <div className="profile-field">
              <label htmlFor="contact_location">Location</label>
              {isEditing ? (
                <>
                  <input
                    type="text"
                    id="contact_location"
                    className={errors.contact_location ? 'input-error' : ''}
                    value={formData.contact_location}
                    onChange={(e) => setFormData({ ...formData, contact_location: e.target.value })}
                    placeholder="Enter your location"
                  />
                  {errors.contact_location && (
                    <span className="field-error">{errors.contact_location}</span>
                  )}
                </>
              ) : (
                <span className="profile-value">{user.contact_location || 'Not set'}</span>
              )}
            </div>
          </div>

          {isEditing && (
            <div className="profile-actions">
              <button
                className="cancel-button"
                onClick={handleCancel}
                disabled={isSaving}
              >
                Cancel
              </button>
              <button
                className="save-button"
                onClick={handleSave}
                disabled={isSaving}
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
