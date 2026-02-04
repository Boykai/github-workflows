/**
 * Settings page component for user configuration.
 */

import { useState, useEffect, FormEvent } from 'react';
import type { UserSettings, UserSettingsUpdate } from '@/types';
import { settingsApi } from '@/services/api';
import './Settings.css';

export function Settings() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState<UserSettings>({
    notifications_enabled: true,
    email_notifications: true,
    theme: 'light',
    language: 'en',
    default_repository: '',
    auto_assign_copilot: false,
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadSettings();
  }, []);

  // Auto-dismiss success message after 3 seconds
  useEffect(() => {
    if (success) {
      const timeoutId = setTimeout(() => setSuccess(false), 3000);
      return () => clearTimeout(timeoutId);
    }
  }, [success]);

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await settingsApi.get();
      setSettings(data);
      setFormData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (formData.theme && !['light', 'dark'].includes(formData.theme)) {
      errors.theme = 'Theme must be either "light" or "dark"';
    }

    if (formData.language && formData.language.length < 2) {
      errors.language = 'Language code must be at least 2 characters';
    }

    if (formData.default_repository && formData.default_repository.trim()) {
      // GitHub allows alphanumeric chars, hyphens, underscores, and periods
      // Format: owner/repo (both parts can contain .-_)
      const repoPattern = /^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/;
      if (!repoPattern.test(formData.default_repository.trim())) {
        errors.default_repository = 'Repository must be in format "owner/repo"';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      setSuccess(false);

      const update: UserSettingsUpdate = {};
      
      // Only send changed fields
      if (settings) {
        if (formData.notifications_enabled !== settings.notifications_enabled) {
          update.notifications_enabled = formData.notifications_enabled;
        }
        if (formData.email_notifications !== settings.email_notifications) {
          update.email_notifications = formData.email_notifications;
        }
        if (formData.theme !== settings.theme) {
          update.theme = formData.theme;
        }
        if (formData.language !== settings.language) {
          update.language = formData.language;
        }
        if (formData.default_repository !== settings.default_repository) {
          update.default_repository = formData.default_repository || undefined;
        }
        if (formData.auto_assign_copilot !== settings.auto_assign_copilot) {
          update.auto_assign_copilot = formData.auto_assign_copilot;
        }
      }

      const updatedSettings = await settingsApi.update(update);
      setSettings(updatedSettings);
      setFormData(updatedSettings);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="settings-loading">
        <div className="spinner" />
        <p>Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Manage your preferences and configuration</p>
      </div>

      {error && (
        <div className="settings-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="settings-success">
          <span className="success-icon">✓</span>
          <span>Settings saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="settings-form">
        {/* Notifications Section */}
        <section className="settings-section">
          <h2>Notifications</h2>
          <div className="settings-group">
            <div className="setting-item">
              <div className="setting-control">
                <input
                  type="checkbox"
                  id="notifications_enabled"
                  checked={formData.notifications_enabled}
                  onChange={(e) =>
                    setFormData({ ...formData, notifications_enabled: e.target.checked })
                  }
                  className="setting-checkbox"
                />
                <label htmlFor="notifications_enabled">Enable notifications</label>
              </div>
              <p className="setting-description">
                Receive notifications for updates and changes
              </p>
            </div>

            <div className="setting-item">
              <div className="setting-control">
                <input
                  type="checkbox"
                  id="email_notifications"
                  checked={formData.email_notifications}
                  onChange={(e) =>
                    setFormData({ ...formData, email_notifications: e.target.checked })
                  }
                  className="setting-checkbox"
                  disabled={!formData.notifications_enabled}
                />
                <label htmlFor="email_notifications">Email notifications</label>
              </div>
              <p className="setting-description">
                Receive notifications via email
              </p>
            </div>
          </div>
        </section>

        {/* Appearance Section */}
        <section className="settings-section">
          <h2>Appearance</h2>
          <div className="settings-group">
            <div className="setting-item">
              <label htmlFor="theme" className="setting-label">Theme</label>
              <select
                id="theme"
                value={formData.theme}
                onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
                className="setting-select"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
              {validationErrors.theme && (
                <span className="validation-error">{validationErrors.theme}</span>
              )}
            </div>

            <div className="setting-item">
              <label htmlFor="language" className="setting-label">Language</label>
              <select
                id="language"
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                className="setting-select"
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
              </select>
              {validationErrors.language && (
                <span className="validation-error">{validationErrors.language}</span>
              )}
            </div>
          </div>
        </section>

        {/* GitHub Integration Section */}
        <section className="settings-section">
          <h2>GitHub Integration</h2>
          <div className="settings-group">
            <div className="setting-item">
              <label htmlFor="default_repository" className="setting-label">
                Default Repository
              </label>
              <input
                type="text"
                id="default_repository"
                value={formData.default_repository || ''}
                onChange={(e) =>
                  setFormData({ ...formData, default_repository: e.target.value })
                }
                placeholder="owner/repo"
                className="setting-input"
              />
              <p className="setting-description">
                Default repository for new issues (format: owner/repo)
              </p>
              {validationErrors.default_repository && (
                <span className="validation-error">{validationErrors.default_repository}</span>
              )}
            </div>

            <div className="setting-item">
              <div className="setting-control">
                <input
                  type="checkbox"
                  id="auto_assign_copilot"
                  checked={formData.auto_assign_copilot}
                  onChange={(e) =>
                    setFormData({ ...formData, auto_assign_copilot: e.target.checked })
                  }
                  className="setting-checkbox"
                />
                <label htmlFor="auto_assign_copilot">Auto-assign to Copilot</label>
              </div>
              <p className="setting-description">
                Automatically assign new issues to GitHub Copilot
              </p>
            </div>
          </div>
        </section>

        {/* Save Button */}
        <div className="settings-actions">
          <button
            type="submit"
            disabled={isSaving}
            className="save-button"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
