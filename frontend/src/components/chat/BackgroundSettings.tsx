/**
 * Background settings component for chat customization.
 */

import { useState, useRef, ChangeEvent } from 'react';
import { PRESET_BACKGROUNDS } from '@/hooks/useBackgroundSettings';
import './BackgroundSettings.css';

interface BackgroundSettingsProps {
  currentBackground: { type: string; value: string };
  onPresetSelect: (value: string) => void;
  onCustomUpload: (dataUrl: string) => void;
  onReset: () => void;
  onClose: () => void;
}

export function BackgroundSettings({
  currentBackground,
  onPresetSelect,
  onCustomUpload,
  onReset,
  onClose,
}: BackgroundSettingsProps) {
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.match(/^image\/(jpeg|png)$/)) {
      setError('Only JPEG and PNG images are allowed.');
      return;
    }

    // Validate file size (max 2MB)
    const maxSize = 2 * 1024 * 1024; // 2MB in bytes
    if (file.size > maxSize) {
      setError('Image must be less than 2MB.');
      return;
    }

    setError('');

    // Read file as data URL
    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      if (dataUrl) {
        onCustomUpload(dataUrl);
      }
    };
    reader.onerror = () => {
      setError('Failed to read image file.');
    };
    reader.readAsDataURL(file);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="background-settings-overlay" onClick={onClose}>
      <div className="background-settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h3>Change Background</h3>
          <button className="close-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="settings-content">
          <section className="settings-section">
            <h4>Preset Backgrounds</h4>
            <div className="preset-grid">
              {PRESET_BACKGROUNDS.map((preset) => (
                <button
                  key={preset.id}
                  className={`preset-option ${
                    currentBackground.type === 'preset' && currentBackground.value === preset.value
                      ? 'selected'
                      : ''
                  }`}
                  style={{ background: preset.value }}
                  onClick={() => onPresetSelect(preset.value)}
                  title={preset.name}
                >
                  <span className="preset-name">{preset.name}</span>
                  {currentBackground.type === 'preset' && currentBackground.value === preset.value && (
                    <span className="checkmark">✓</span>
                  )}
                </button>
              ))}
            </div>
          </section>

          <section className="settings-section">
            <h4>Custom Image</h4>
            <p className="section-description">Upload your own background image (JPEG or PNG, max 2MB)</p>
            <button className="upload-button" onClick={handleUploadClick}>
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
              </svg>
              Upload Image
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            {error && <div className="error-message">{error}</div>}
            {currentBackground.type === 'custom' && (
              <div className="custom-preview">
                <img src={currentBackground.value} alt="Custom background preview" />
              </div>
            )}
          </section>
        </div>

        <div className="settings-footer">
          <button className="reset-button" onClick={onReset}>
            Reset to Default
          </button>
          <button className="done-button" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
