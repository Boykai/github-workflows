/**
 * Signal Connection settings component.
 *
 * Provides QR code linking flow, connection status display,
 * disconnect functionality, notification preferences, and conflict banners.
 * Integrates as a SettingsSection in the Settings page.
 */

import { useState, useCallback } from 'react';
import { SettingsSection } from './SettingsSection';
import {
  useSignalConnection,
  useInitiateSignalLink,
  useSignalLinkStatus,
  useDisconnectSignal,
  useSignalPreferences,
  useUpdateSignalPreferences,
  useSignalBanners,
  useDismissBanner,
} from '@/hooks/useSettings';
import type { SignalNotificationMode } from '@/types';

// ── Sub-components ──

function ConnectionStatusBadge({ status }: { status: string | null }) {
  const labels: Record<string, string> = {
    connected: 'Connected',
    pending: 'Linking…',
    error: 'Error',
    disconnected: 'Not Connected',
  };
  const classes: Record<string, string> = {
    connected: 'signal-status--connected',
    pending: 'signal-status--pending',
    error: 'signal-status--error',
    disconnected: 'signal-status--disconnected',
  };

  const key = status ?? 'disconnected';
  return (
    <span className={`signal-status-badge ${classes[key] ?? 'signal-status--disconnected'}`}>
      {labels[key] ?? 'Not Connected'}
    </span>
  );
}

function QRCodeDisplay({ base64, expiresIn }: { base64: string; expiresIn: number }) {
  return (
    <div className="signal-qr-section">
      <p className="signal-qr-instructions">
        Scan this QR code with your Signal app:
        <br />
        <em>Signal → Settings → Linked Devices → + (plus button)</em>
      </p>
      <img
        className="signal-qr-image"
        src={`data:image/png;base64,${base64}`}
        alt="Signal QR code for device linking"
        width={256}
        height={256}
      />
      <p className="signal-qr-expiry">
        QR code expires in {expiresIn} seconds. A new one will be generated if it expires.
      </p>
    </div>
  );
}

function ConflictBanners() {
  const { banners } = useSignalBanners();
  const { dismissBanner, isPending } = useDismissBanner();

  if (banners.length === 0) return null;

  return (
    <div className="signal-conflict-banners">
      {banners.map((banner) => (
        <div key={banner.id} className="signal-conflict-banner">
          <span className="signal-banner-icon">⚠️</span>
          <span className="signal-banner-message">{banner.message}</span>
          <button
            className="signal-banner-dismiss"
            onClick={() => dismissBanner(banner.id)}
            disabled={isPending}
            type="button"
          >
            Dismiss
          </button>
        </div>
      ))}
    </div>
  );
}

function NotificationPreferenceSelector() {
  const { preferences, isLoading } = useSignalPreferences();
  const { updatePreferences, isPending } = useUpdateSignalPreferences();

  if (isLoading || !preferences) return null;

  const options: { value: SignalNotificationMode; label: string; description: string }[] = [
    { value: 'all', label: 'All Messages', description: 'Receive all chat messages via Signal' },
    { value: 'actions_only', label: 'Action Proposals Only', description: 'Only task proposals and action items' },
    { value: 'confirmations_only', label: 'System Confirmations Only', description: 'Only task creation and status change confirmations' },
    { value: 'none', label: 'None', description: 'Do not forward any messages to Signal' },
  ];

  const handleChange = async (mode: SignalNotificationMode) => {
    await updatePreferences({ notification_mode: mode });
  };

  return (
    <div className="signal-preferences">
      <h4 className="signal-preferences-title">Notification Preferences</h4>
      <div className="signal-preferences-options">
        {options.map((opt) => (
          <label key={opt.value} className="signal-preference-option">
            <input
              type="radio"
              name="signal-notification-mode"
              value={opt.value}
              checked={preferences.notification_mode === opt.value}
              onChange={() => handleChange(opt.value)}
              disabled={isPending}
            />
            <div className="signal-preference-label">
              <span className="signal-preference-name">{opt.label}</span>
              <span className="signal-preference-desc">{opt.description}</span>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
}

// ── Main Component ──

export function SignalConnection() {
  const { connection, isLoading } = useSignalConnection();
  const { initiateLink, data: linkData, isPending: isLinking, reset: resetLink } = useInitiateSignalLink();
  const { disconnect, isPending: isDisconnecting } = useDisconnectSignal();
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);

  const isConnected = connection?.status === 'connected';
  const isLinkingInProgress = isLinking || !!linkData;

  // Poll link status when linking is in progress
  const { linkStatus } = useSignalLinkStatus(isLinkingInProgress && !isConnected);

  // If polling detected link completion, connection query will be invalidated automatically

  const handleInitiateLink = useCallback(async () => {
    resetLink();
    await initiateLink(undefined);
  }, [initiateLink, resetLink]);

  const handleDisconnect = useCallback(async () => {
    await disconnect();
    setShowDisconnectConfirm(false);
    resetLink();
  }, [disconnect, resetLink]);

  if (isLoading) {
    return (
      <SettingsSection
        title="Signal Integration"
        description="Connect your Signal account to receive and send chat messages via Signal."
        hideSave
      >
        <div className="signal-loading">Loading Signal connection status...</div>
      </SettingsSection>
    );
  }

  return (
    <SettingsSection
      title="Signal Integration"
      description="Connect your Signal account to receive and send chat messages via Signal."
      hideSave
    >
      <ConflictBanners />

      <div className="signal-connection-status">
        <div className="signal-status-row">
          <span className="signal-status-label">Status:</span>
          <ConnectionStatusBadge status={connection?.status ?? null} />
        </div>

        {isConnected && connection?.signal_identifier && (
          <div className="signal-status-row">
            <span className="signal-status-label">Phone:</span>
            <span className="signal-phone-masked">{connection.signal_identifier}</span>
          </div>
        )}
      </div>

      {/* Connect / QR Code Section */}
      {!isConnected && !isLinkingInProgress && (
        <div className="signal-connect-section">
          <button
            className="signal-connect-btn"
            onClick={handleInitiateLink}
            disabled={isLinking}
            type="button"
          >
            {isLinking ? 'Generating QR Code...' : 'Connect Signal Account'}
          </button>
        </div>
      )}

      {/* QR Code display during linking */}
      {isLinkingInProgress && linkData && !isConnected && (
        <>
          <QRCodeDisplay
            base64={linkData.qr_code_base64}
            expiresIn={linkData.expires_in_seconds}
          />
          {linkStatus?.status === 'pending' && (
            <p className="signal-link-polling">Waiting for QR code scan...</p>
          )}
          {linkStatus?.status === 'failed' && (
            <div className="signal-link-error">
              <p>Linking failed: {linkStatus.error_message ?? 'Unknown error'}</p>
              <button className="signal-retry-btn" onClick={handleInitiateLink} type="button">
                Try Again
              </button>
            </div>
          )}
          <button
            className="signal-cancel-link-btn"
            onClick={() => resetLink()}
            type="button"
          >
            Cancel
          </button>
        </>
      )}

      {/* Disconnect Section */}
      {isConnected && (
        <div className="signal-disconnect-section">
          {!showDisconnectConfirm ? (
            <button
              className="signal-disconnect-btn"
              onClick={() => setShowDisconnectConfirm(true)}
              type="button"
            >
              Disconnect Signal
            </button>
          ) : (
            <div className="signal-disconnect-confirm">
              <p>Are you sure? This will stop all Signal notifications and delete your linked phone number.</p>
              <div className="signal-disconnect-actions">
                <button
                  className="signal-disconnect-confirm-btn"
                  onClick={handleDisconnect}
                  disabled={isDisconnecting}
                  type="button"
                >
                  {isDisconnecting ? 'Disconnecting...' : 'Yes, Disconnect'}
                </button>
                <button
                  className="signal-disconnect-cancel-btn"
                  onClick={() => setShowDisconnectConfirm(false)}
                  type="button"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Notification Preferences (only when connected) */}
      {isConnected && <NotificationPreferenceSelector />}
    </SettingsSection>
  );
}
