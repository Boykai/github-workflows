# Quickstart: Native iOS Support for iPhone 14 Pro Max

**Feature**: 014-native-ios-support
**Date**: 2026-02-28

## Overview

This feature packages the existing React/TypeScript web application as a native iOS app using Capacitor. The iOS app wraps the existing Vite-built frontend in a WKWebView with native device API access via Capacitor plugins.

## Prerequisites

- **macOS** with Xcode 15+ installed (required for iOS builds)
- **Apple Developer Program** membership ($99/year) for device testing and App Store distribution
- **CocoaPods** installed (`sudo gem install cocoapods`)
- **Node.js 18+** and **npm** (existing)
- **Python 3.11+** (existing, for backend)
- **Docker and Docker Compose** (existing, for backend services)

## Development Setup

### 1. Start the Backend

```bash
# From repo root — start backend services
docker compose up -d

# Or run directly:
cd backend && pip install -e ".[dev]" && uvicorn src.main:app --reload
```

### 2. Build the Frontend

```bash
cd frontend
npm install
npm run build    # Produces dist/ directory
```

### 3. Initialize Capacitor (First Time Only)

```bash
cd frontend
npm install @capacitor/core @capacitor/cli @capacitor/ios
npx cap init "Agent Projects" "com.agentprojects.app" --web-dir dist

# Install Capacitor plugins
npm install @capacitor/app @capacitor/status-bar @capacitor/splash-screen \
  @capacitor/keyboard @capacitor/push-notifications @capacitor/preferences

# Add iOS platform
npx cap add ios
```

### 4. Sync and Open in Xcode

```bash
cd frontend
npx cap sync ios     # Copies web assets + syncs native plugins
npx cap open ios     # Opens the Xcode project
```

### 5. Configure Xcode Project

In Xcode:
1. Set **Deployment Target** to iOS 16.0
2. Set **Signing & Capabilities** with your Apple Developer team
3. Add **Push Notifications** capability
4. Verify **Info.plist** contains all required usage description strings
5. Select **iPhone 14 Pro Max** simulator or connected device
6. Build and run (⌘+R)

### 6. Development Workflow (Iterating)

For rapid development, use the Capacitor live reload with the Vite dev server:

```bash
# Terminal 1: Start Vite dev server
cd frontend && npm run dev

# Terminal 2: Open iOS app (configured to point to dev server)
cd frontend && npx cap open ios
```

In `capacitor.config.ts`, temporarily enable the dev server URL:
```typescript
server: {
  url: 'http://YOUR_LOCAL_IP:5173',  // Use local IP, not localhost
}
```

## Key Files to Modify/Create

### Frontend (New Files)

| File | Action | Purpose |
|------|--------|---------|
| `frontend/capacitor.config.ts` | Create | Root Capacitor configuration |
| `frontend/src/components/ios/SafeAreaWrapper.tsx` | Create | Safe area inset wrapper component (FR-003) |
| `frontend/src/hooks/useIOSLifecycle.ts` | Create | App lifecycle event handling (FR-006, FR-013) |
| `frontend/src/hooks/usePushNotifications.ts` | Create | APNs push notification management (FR-007) |
| `frontend/src/services/capacitor.ts` | Create | Capacitor plugin initialization and platform helpers |

### Frontend (Modified Files)

| File | Action | Purpose |
|------|--------|---------|
| `frontend/package.json` | Modify | Add Capacitor dependencies |
| `frontend/src/index.css` | Modify | Add safe area CSS variables and touch target styles |
| `frontend/src/App.tsx` | Modify | Wrap with SafeAreaWrapper, integrate lifecycle hook |
| `frontend/index.html` | Modify | Add `viewport-fit=cover` to meta viewport tag |

### iOS Project (Generated + Configured)

| File | Action | Purpose |
|------|--------|---------|
| `frontend/ios/App/App/Info.plist` | Modify | Add permission strings and privacy settings |
| `frontend/ios/App/App/Assets.xcassets/` | Modify | Add app icon and splash screen assets |
| `frontend/ios/App/App.xcodeproj/` | Modify | Set deployment target, signing, capabilities |

### Backend

| File | Action | Purpose |
|------|--------|---------|
| *(none)* | — | No backend changes required |

## Implementation Order

1. **Capacitor initialization** — Install dependencies, create `capacitor.config.ts`, add iOS platform
2. **HTML viewport update** — Add `viewport-fit=cover` to `index.html` meta tag
3. **CSS safe area styles** — Add `env(safe-area-inset-*)` variables and touch target styles to `index.css`
4. **SafeAreaWrapper component** — Create wrapper component for root layout
5. **Capacitor service utility** — Create platform detection and plugin initialization helpers
6. **App lifecycle hook** — Create `useIOSLifecycle` for state persistence
7. **Push notification hook** — Create `usePushNotifications` for APNs
8. **App.tsx integration** — Wrap with SafeAreaWrapper, integrate lifecycle hook
9. **Xcode project configuration** — Info.plist, signing, deployment target, capabilities
10. **App icon and splash screen** — Add visual assets to Assets.xcassets
11. **Accessibility audit** — Verify VoiceOver labels, Dynamic Type scaling, touch targets, contrast
12. **App Store preparation** — Privacy manifest, usage descriptions, App Store metadata

## Testing the Feature

### Manual Testing (Xcode Simulator)

1. Build and run on iPhone 14 Pro Max simulator
2. Verify all screens render within safe areas (no content behind Dynamic Island or home indicator)
3. Navigate between sections — verify tab bar and swipe-back gestures work
4. Toggle Dark Mode in simulator Settings — verify app adapts dynamically
5. Background the app (⌘+Shift+H) and return — verify state is preserved
6. Enable VoiceOver in simulator — verify all elements are labeled and navigable
7. Change Dynamic Type size — verify text scales without layout breakage

### Checklist: Before App Store Submission

- [ ] App launches within 3 seconds on iPhone 14 Pro Max
- [ ] All screens respect safe area insets
- [ ] Dark Mode and Light Mode both display correctly
- [ ] Swipe-back gesture works on all detail screens
- [ ] App state preserved across background/resume cycles
- [ ] All interactive elements ≥ 44×44 points
- [ ] VoiceOver navigation works for all screens
- [ ] Dynamic Type scales text correctly
- [ ] Privacy manifest (`PrivacyInfo.xcprivacy`) is present
- [ ] All `Info.plist` usage description strings are set
- [ ] App icon includes all required sizes
- [ ] Splash screen displays correctly

### Validation Test Cases

- Rotate device → app handles gracefully (portrait locked or responsive)
- Kill app from multitasking → relaunch restores last section
- Deny notification permission → app continues without notifications, no repeated prompts
- Disable network → app shows offline message, cached data available
- Enable Reduce Motion → animations minimized or removed
- Change system font size to largest → text scales, no overlapping/clipping
