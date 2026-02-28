# Capacitor Plugin Contracts: Native iOS Support

**Feature**: 014-native-ios-support
**Date**: 2026-02-28
**Depends on**: research.md (R1, R2, R5, R6, R9)

This document defines the Capacitor plugin configuration and TypeScript interfaces used by the iOS native layer.

---

## Capacitor Configuration

File: `frontend/capacitor.config.ts`

```typescript
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.agentprojects.app',
  appName: 'Agent Projects',
  webDir: 'dist',
  server: {
    // In production, content is served from the local bundle
    // In development, point to the Vite dev server:
    // url: 'http://localhost:5173',
    androidScheme: 'https',
    iosScheme: 'https',
  },
  ios: {
    // Enable edge-swipe back navigation (FR-005)
    allowsMultipleWindows: false,
    scrollEnabled: true,
    // Content inset behavior for safe areas
    contentInset: 'automatic',
  },
  plugins: {
    StatusBar: {
      // Overlay content under the status bar for edge-to-edge rendering
      overlaysWebView: true,
      style: 'Default', // Adapts to light/dark mode automatically
    },
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      backgroundColor: '#ffffff',
      showSpinner: false,
    },
    Keyboard: {
      // Resize the web view when keyboard appears
      resize: 'body',
      style: 'Default', // Adapts to light/dark mode
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },
  },
};

export default config;
```

---

## TypeScript Interfaces

### Session State Contract

```typescript
/** Persisted via Capacitor Preferences for lifecycle restoration */
interface IOSSessionState {
  activeSection: 'board' | 'settings' | 'chat';
  scrollPositions: Record<string, number>;
  formDraft: Record<string, unknown> | null;
  lastSavedAt: string; // ISO 8601
  appVersion: string;
}

const SESSION_STATE_KEY = 'ios_session_state';
```

### Push Notification Contract

```typescript
/** Persisted via Capacitor Preferences */
interface IOSPushRegistration {
  permissionStatus: 'granted' | 'denied' | 'prompt';
  deviceToken: string | null;
  registeredAt: string | null; // ISO 8601
}

const PUSH_REGISTRATION_KEY = 'ios_push_registration';
```

### Lifecycle Event Contract

```typescript
import type { AppState } from '@capacitor/app';

/** Events emitted by @capacitor/app plugin */
interface AppLifecycleEvents {
  /** Fired when app state changes (foreground/background) */
  appStateChange: { isActive: boolean };
  /** Fired when app URL is opened (deep links) */
  appUrlOpen: { url: string };
  /** Fired on Android back button (no-op on iOS, included for completeness) */
  backButton: { canGoBack: boolean };
}
```

---

## Plugin Dependencies

| Plugin | Version | Purpose | FR Coverage |
|--------|---------|---------|-------------|
| `@capacitor/core` | ^6.0.0 | Core runtime | All |
| `@capacitor/cli` | ^6.0.0 | Build tooling | FR-001 |
| `@capacitor/ios` | ^6.0.0 | iOS native platform | FR-001, FR-002, FR-003 |
| `@capacitor/app` | ^6.0.0 | Lifecycle events | FR-006, FR-013 |
| `@capacitor/status-bar` | ^6.0.0 | Status bar control | FR-003, FR-004 |
| `@capacitor/splash-screen` | ^6.0.0 | Launch screen | FR-001 |
| `@capacitor/keyboard` | ^6.0.0 | Keyboard handling | FR-003, FR-008 |
| `@capacitor/push-notifications` | ^6.0.0 | APNs integration | FR-007 |
| `@capacitor/preferences` | ^6.0.0 | Key-value persistence | FR-006, FR-013 |

---

## Info.plist Required Entries

```xml
<!-- Minimum iOS version (FR-012) -->
<key>MinimumOSVersion</key>
<string>16.0</string>

<!-- Push notifications permission (FR-007, FR-011) -->
<key>NSUserNotificationsUsageDescription</key>
<string>Agent Projects would like to send you notifications about project updates and workflow events.</string>

<!-- Camera permission if used (FR-011) -->
<key>NSCameraUsageDescription</key>
<string>Agent Projects needs camera access to capture images for project attachments.</string>

<!-- Photo library permission if used (FR-011) -->
<key>NSPhotoLibraryUsageDescription</key>
<string>Agent Projects needs photo library access to attach images to projects.</string>

<!-- App Transport Security — allow API connection -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <!-- Add specific domain exceptions as needed -->
</dict>
```

---

## CSS Safe Area Contract

```css
/* Applied to root layout element (FR-003) */
:root {
  --safe-area-top: env(safe-area-inset-top);
  --safe-area-bottom: env(safe-area-inset-bottom);
  --safe-area-left: env(safe-area-inset-left);
  --safe-area-right: env(safe-area-inset-right);
}

/* HTML viewport meta tag must include viewport-fit=cover */
/* <meta name="viewport" content="viewport-fit=cover, width=device-width, initial-scale=1.0"> */

/* Minimum touch target size (FR-008) */
.ios-touch-target {
  min-height: 44px;
  min-width: 44px;
}
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Capacitor plugin not available (web fallback) | Graceful degradation — hooks check `Capacitor.isNativePlatform()` before calling native APIs |
| Push notification permission denied | App continues without notifications; no repeated prompts |
| State restoration fails (corrupted data) | Discard saved state; start fresh with default navigation state |
| Network unavailable | Show user-friendly offline message; cached data displayed where available |
| iOS version below 16.0 | Xcode project's deployment target prevents installation; App Store listing shows minimum version |
