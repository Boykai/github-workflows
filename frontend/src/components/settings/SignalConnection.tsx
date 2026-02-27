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
  const key = status ?? 'disconnected';

  const config: Record<string, { label: string; dot: string; bg: string; text: string }> = {
    connected: {
      label: 'Connected',
      dot: 'bg-green-500',
      bg: 'bg-green-500/10',
      text: 'text-green-600 dark:text-green-400',
    },
    pending: {
      label: 'Linking…',
      dot: 'bg-yellow-500 animate-pulse',
      bg: 'bg-yellow-500/10',
      text: 'text-yellow-600 dark:text-yellow-400',
    },
    error: {
      label: 'Error',
      dot: 'bg-red-500',
      bg: 'bg-red-500/10',
      text: 'text-red-600 dark:text-red-400',
    },
    disconnected: {
      label: 'Not Connected',
      dot: 'bg-muted-foreground/40',
      bg: 'bg-muted/50',
      text: 'text-muted-foreground',
    },
  };

  const c = config[key] ?? config.disconnected;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}

function QRCodeDisplay({ base64, expiresIn }: { base64: string; expiresIn: number }) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-lg border border-border bg-muted/30 p-6">
      <p className="text-sm text-muted-foreground text-center leading-relaxed">
        Scan this QR code with your Signal app:
        <br />
        <span className="text-xs italic">Signal → Settings → Linked Devices → + (plus button)</span>
      </p>
      <div className="rounded-lg border border-border bg-white p-3 shadow-sm">
        <img
          src={`data:image/png;base64,${base64}`}
          alt="Signal QR code for device linking"
          width={220}
          height={220}
          className="block"
        />
      </div>
      <p className="text-xs text-muted-foreground">
        QR code expires in <span className="font-medium">{expiresIn}s</span>. A new one will be generated if it expires.
      </p>
    </div>
  );
}

function ConflictBanners() {
  const { banners } = useSignalBanners();
  const { dismissBanner, isPending } = useDismissBanner();

  if (banners.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      {banners.map((banner) => (
        <div
          key={banner.id}
          className="flex items-start gap-3 rounded-md border border-yellow-500/30 bg-yellow-500/10 p-3"
        >
          <span className="text-base leading-none mt-0.5">⚠️</span>
          <span className="flex-1 text-sm text-yellow-700 dark:text-yellow-300">{banner.message}</span>
          <button
            className="shrink-0 text-xs font-medium text-yellow-700 dark:text-yellow-300 underline underline-offset-2 hover:text-yellow-900 dark:hover:text-yellow-100 transition-colors disabled:opacity-50"
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
    { value: 'confirmations_only', label: 'Confirmations Only', description: 'Only task creation and status change confirmations' },
    { value: 'none', label: 'None', description: 'Do not forward any messages to Signal' },
  ];

  const handleChange = async (mode: SignalNotificationMode) => {
    await updatePreferences({ notification_mode: mode });
  };

  return (
    <div className="flex flex-col gap-3">
      <h4 className="text-sm font-medium text-foreground">Notification Preferences</h4>
      <div className="flex flex-col gap-2">
        {options.map((opt) => (
          <label
            key={opt.value}
            className={`flex items-start gap-3 rounded-md border p-3 cursor-pointer transition-colors
              ${preferences.notification_mode === opt.value
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/40 hover:bg-muted/30'
              }
              ${isPending ? 'opacity-60 pointer-events-none' : ''}`}
          >
            <input
              type="radio"
              name="signal-notification-mode"
              value={opt.value}
              checked={preferences.notification_mode === opt.value}
              onChange={() => handleChange(opt.value)}
              disabled={isPending}
              className="mt-0.5 accent-primary"
            />
            <div className="flex flex-col gap-0.5">
              <span className="text-sm font-medium text-foreground">{opt.label}</span>
              <span className="text-xs text-muted-foreground">{opt.description}</span>
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
        description="Connect your Signal account to chat with the AI assistant and receive notifications via Signal."
        hideSave
      >
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="w-4 h-4 border-2 border-muted-foreground/30 border-t-muted-foreground rounded-full animate-spin" />
          Loading Signal connection status…
        </div>
      </SettingsSection>
    );
  }

  return (
    <SettingsSection
      title="Signal Integration"
      description="Connect your Signal account to chat with the AI assistant and receive notifications via Signal."
      hideSave
    >
      <ConflictBanners />

      {/* Connection Status */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-muted-foreground">Status</span>
          <ConnectionStatusBadge status={connection?.status ?? null} />
        </div>

        {isConnected && connection?.signal_identifier && (
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-muted-foreground">Phone</span>
            <span className="text-sm font-mono text-foreground">{connection.signal_identifier}</span>
          </div>
        )}
      </div>

      {/* Connect CTA — only when not connected and not in linking flow */}
      {!isConnected && !isLinkingInProgress && (
        <button
          className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md
            bg-primary text-primary-foreground shadow-sm
            hover:bg-primary/90 transition-colors
            disabled:opacity-50 disabled:cursor-not-allowed
            w-fit"
          onClick={handleInitiateLink}
          disabled={isLinking}
          type="button"
        >
          {isLinking ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              Generating QR Code…
            </>
          ) : (
            'Connect Signal Account'
          )}
        </button>
      )}

      {/* QR Code display during linking */}
      {isLinkingInProgress && linkData && !isConnected && (
        <div className="flex flex-col gap-4">
          <QRCodeDisplay
            base64={linkData.qr_code_base64}
            expiresIn={linkData.expires_in_seconds}
          />

          {linkStatus?.status === 'pending' && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="w-3.5 h-3.5 border-2 border-muted-foreground/30 border-t-muted-foreground rounded-full animate-spin" />
              Waiting for QR code scan…
            </p>
          )}

          {linkStatus?.status === 'failed' && (
            <div className="flex flex-col gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3">
              <p className="text-sm text-destructive">
                Linking failed: {linkStatus.error_message ?? 'Unknown error'}
              </p>
              <button
                className="inline-flex items-center justify-center px-3 py-1.5 text-xs font-medium rounded-md
                  bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors w-fit"
                onClick={handleInitiateLink}
                type="button"
              >
                Try Again
              </button>
            </div>
          )}

          <button
            className="inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium rounded-md
              border border-border text-muted-foreground
              hover:bg-muted hover:text-foreground transition-colors w-fit"
            onClick={() => resetLink()}
            type="button"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Disconnect Section — only when connected */}
      {isConnected && (
        <div className="flex flex-col gap-3 pt-1">
          {!showDisconnectConfirm ? (
            <button
              className="inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium rounded-md
                border border-destructive/30 text-destructive
                hover:bg-destructive/10 transition-colors w-fit"
              onClick={() => setShowDisconnectConfirm(true)}
              type="button"
            >
              Disconnect Signal
            </button>
          ) : (
            <div className="flex flex-col gap-3 rounded-md border border-destructive/30 bg-destructive/5 p-4">
              <p className="text-sm text-foreground">
                Are you sure? This will stop all Signal notifications and delete your linked phone number.
              </p>
              <div className="flex items-center gap-2">
                <button
                  className="inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium rounded-md
                    bg-destructive text-destructive-foreground shadow-sm
                    hover:bg-destructive/90 transition-colors
                    disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={handleDisconnect}
                  disabled={isDisconnecting}
                  type="button"
                >
                  {isDisconnecting ? 'Disconnecting…' : 'Yes, Disconnect'}
                </button>
                <button
                  className="inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium rounded-md
                    border border-border text-muted-foreground
                    hover:bg-muted hover:text-foreground transition-colors"
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
