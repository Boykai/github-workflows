# Data Model: Native iOS Support

**Feature**: 014-native-ios-support
**Date**: 2026-02-28
**Depends on**: research.md (R5, R6)

## Entities

### User Session State (Client-Side)

Represents the transient user state persisted via Capacitor Preferences for lifecycle restoration. This is a client-side-only entity — no backend changes required.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `activeSection` | string | NOT NULL | Currently active tab/section identifier (e.g., "board", "settings", "chat") |
| `scrollPositions` | object | Optional | Map of section → scroll Y position (in pixels) |
| `formDraft` | object | Optional | Serialized unsaved form data keyed by form identifier |
| `lastSavedAt` | string (ISO 8601) | NOT NULL | Timestamp of last state save |
| `appVersion` | string | NOT NULL | App version at time of save (for migration compatibility) |

**Storage**: Capacitor Preferences plugin (key-value, persisted to device disk)
**Key**: `ios_session_state`
**Serialization**: JSON string

### Notification Registration (Client-Side)

Represents the push notification permission and device token state. Stored locally and optionally synced to the backend.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `permissionStatus` | enum | "granted" \| "denied" \| "prompt" | Current notification permission state |
| `deviceToken` | string | Optional, present when granted | APNs device token for push delivery |
| `registeredAt` | string (ISO 8601) | Optional | When the token was last registered |

**Storage**: Capacitor Preferences plugin
**Key**: `ios_push_registration`
**Serialization**: JSON string

### Appearance Configuration (Client-Side — Existing)

The existing `ThemeProvider` already manages this entity via localStorage with key `vite-ui-theme` and values `light`, `dark`, or `system`. No changes required — the existing implementation satisfies FR-004.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `theme` | enum | "light" \| "dark" \| "system" | User's theme preference |

**Storage**: localStorage (existing, key: `vite-ui-theme`)
**Note**: Already implemented in `frontend/src/components/ThemeProvider.tsx`

### iOS Application Package (Build Artifact)

Represents the distributable app bundle. This is a build-time artifact, not a runtime data entity.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `bundleIdentifier` | string | Reverse domain (e.g., `com.agentprojects.app`) | Unique app identifier for App Store |
| `version` | string | Semver (e.g., `1.0.0`) | App version displayed to users |
| `buildNumber` | integer | Incrementing | Internal build number for App Store uploads |
| `minimumOSVersion` | string | `16.0` | Minimum supported iOS version |
| `supportedDevices` | string[] | `["iphone"]` | Target device family |

**Storage**: `Info.plist` (Xcode project configuration)

## Relationships

```
iOS App Package (build artifact)
  └── contains ── Web Assets (Vite build output)
  └── configures ── Capacitor Plugins

User Session State (client-side)
  └── persisted via ── Capacitor Preferences
  └── restored on ── App resume / relaunch

Notification Registration (client-side)
  └── managed by ── @capacitor/push-notifications
  └── optionally synced to ── Backend API (future)

Appearance Configuration (client-side, existing)
  └── managed by ── ThemeProvider (existing)
  └── observes ── iOS system prefers-color-scheme
```

## Validation Rules

| Rule | Field(s) | Enforcement |
|------|----------|-------------|
| Valid section identifier | `activeSection` | TypeScript enum/union type in hook |
| Non-negative scroll positions | `scrollPositions` values | Math.max(0, value) in hook |
| Valid JSON serialization | All Preferences entries | try/catch in read/write operations |
| App version compatibility | `appVersion` | Version check before state restoration; discard stale state |
| Permission status matches OS state | `permissionStatus` | Re-check on app resume via Capacitor plugin |

## State Transitions

### App Lifecycle States

```
[Not Installed] → App Store Install → [Installed / Not Running]
[Not Running]   → User taps icon    → [Active (Foreground)]
[Active]        → Home/switch app   → [Background]
[Background]    → Return to app     → [Active] (state restored from Preferences)
[Background]    → System pressure   → [Suspended → Terminated]
[Terminated]    → User taps icon    → [Active] (state restored from Preferences if available)
```

### Notification Permission States

```
[Not Determined] → User prompted → [Granted] or [Denied]
[Granted]        → Token received → [Registered] (deviceToken stored)
[Denied]         → App continues without notifications
[Granted]        → User disables in Settings → [Denied] (detected on app resume)
```

## Backend Changes

**None required.** The existing FastAPI backend API endpoints are consumed by the iOS app via the same HTTP calls the web frontend makes. The backend is unaware of whether the client is a web browser or a native iOS app.

If push notification server-side delivery is implemented in the future, a new `device_tokens` table would be needed to store APNs tokens keyed by user. This is explicitly out of scope for the initial implementation (FR-007 is a SHOULD requirement).
