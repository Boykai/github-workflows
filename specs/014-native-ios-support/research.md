# Research: Add Native iOS Support for iPhone 14 Pro Max

**Feature**: 014-native-ios-support
**Date**: 2026-02-28
**Status**: Complete

## R1: Native iOS Packaging Approach

**Decision**: Use Capacitor 6 to wrap the existing React/Vite web application as a native iOS app.

**Rationale**: The existing application is built with React 18, TypeScript, Vite, and Tailwind CSS. Capacitor is specifically designed to wrap existing web applications in native iOS (and Android) shells with minimal code changes. It provides a native WebView (WKWebView on iOS) that runs the existing compiled frontend, while exposing native device APIs through a plugin system. This approach preserves 100% of the existing React codebase, requires no rewrite, and provides access to native iOS features (push notifications, status bar, splash screen, keyboard handling, app lifecycle). The spec's technical notes explicitly recommend Capacitor for React/web-based apps.

**Alternatives considered**:
- **React Native rewrite**: Would require rewriting the entire frontend in React Native components. Significant effort, introduces a new framework, and duplicates work already done in the web frontend. Does not align with YAGNI or Simplicity principles.
- **Swift/SwiftUI native app**: Would require a complete rewrite from scratch. Maximum native performance but impractical given the existing React codebase and the transitional nature of this feature.
- **Cordova/PhoneGap**: Older technology with declining community support. Capacitor is its modern successor with better performance, TypeScript support, and active maintenance.
- **PWA (Progressive Web App)**: Does not produce a true App Store-distributable app. Lacks access to some native APIs (e.g., full push notification support). Does not satisfy FR-001 (native iOS application requirement).

## R2: Safe Area and Dynamic Island Handling

**Decision**: Use CSS `env(safe-area-inset-*)` variables combined with Capacitor's Status Bar plugin and a React wrapper component for safe area management.

**Rationale**: iOS WKWebView (used by Capacitor) supports the CSS `env()` function for safe area insets natively. By setting `viewport-fit=cover` in the HTML meta tag and applying `env(safe-area-inset-top)`, `env(safe-area-inset-bottom)`, `env(safe-area-inset-left)`, and `env(safe-area-inset-right)` as padding on the root layout, the app content automatically avoids the Dynamic Island region and home indicator area. This is the standard Apple-recommended approach for web content in WKWebView. A React `SafeAreaWrapper` component encapsulates this pattern for reuse across all screens.

**Alternatives considered**:
- **Native safe area constraints via Swift**: Would require bridging native UIKit constraints into the WebView. Overengineered for a Capacitor app where CSS environment variables work natively.
- **Fixed pixel offsets**: Fragile and device-specific. CSS environment variables are dynamic and adapt to any device form factor automatically.

## R3: Dark Mode and Light Mode Support

**Decision**: Leverage the existing `ThemeProvider` component (which already supports `light`, `dark`, and `system` themes via localStorage) combined with the CSS `prefers-color-scheme` media query for automatic iOS system theme detection.

**Rationale**: The existing frontend already has full dark/light mode support via `ThemeProvider.tsx` which reads the user's preference and falls back to the system setting. On iOS, WKWebView correctly propagates the system's `prefers-color-scheme` value. When the Capacitor app is built, the existing `system` theme option will automatically track the iOS Dark Mode setting. No additional code is required for FR-004 — the existing implementation satisfies this requirement out of the box.

**Alternatives considered**:
- **Capacitor Dark Mode plugin**: Unnecessary; the standard CSS media query approach already works in WKWebView.
- **Native Swift theme bridging**: Overengineered; the web-based approach is sufficient and already implemented.

## R4: Native Navigation Patterns

**Decision**: Implement iOS-like navigation patterns using CSS/JS within the web layer, enhanced by Capacitor's native navigation behavior. Use CSS scroll behavior for smooth transitions, gesture-based navigation via touch event listeners for swipe-back, and a tab bar component for section switching.

**Rationale**: Capacitor's WKWebView on iOS natively supports edge-swipe gestures for browser history back navigation (when `allowsBackForwardNavigationGestures` is enabled in the Capacitor configuration). This provides FR-005's swipe-back requirement with zero custom code. Tab bar and navigation stack transitions are implemented using the existing React component structure with CSS animations. Since the app already has a page/section structure, adding a bottom tab bar component and push/pop-style CSS transitions creates a native feel.

**Alternatives considered**:
- **React Native Navigation (react-navigation)**: Only works with React Native, not Capacitor.
- **Ionic Framework components**: Would add a large dependency (Ionic UI library) just for navigation. The app already has its own component library (shadcn/ui + Tailwind). Using Ionic components would create visual inconsistency.
- **Framework7**: Another mobile UI framework; same issue as Ionic — adds unnecessary weight and visual inconsistency.

## R5: App Lifecycle and State Preservation

**Decision**: Use Capacitor's `@capacitor/app` plugin for lifecycle events combined with a custom React hook (`useIOSLifecycle`) that saves and restores user state via the Capacitor Preferences plugin.

**Rationale**: The `@capacitor/app` plugin provides event listeners for `appStateChange` (foreground/background), `pause`, `resume`, and `backButton`. When the app enters background, the hook serializes the current navigation state (active page/section, scroll position) and any unsaved form data to Capacitor's Preferences (key-value storage persisted to disk). On resume or relaunch, the hook restores this state. This approach is lightweight, requires no backend changes, and follows the established pattern of custom React hooks in the codebase (e.g., `useAuth`, `useAppTheme`).

**Alternatives considered**:
- **Browser sessionStorage/localStorage only**: Works for simple cases but may not persist across app termination by the system. Capacitor Preferences provides more reliable persistence.
- **Backend-side state storage**: Overengineered for client navigation state. Would add unnecessary API calls and latency.

## R6: Push Notifications via APNs

**Decision**: Use Capacitor's `@capacitor/push-notifications` plugin for APNs integration with a custom React hook (`usePushNotifications`).

**Rationale**: The `@capacitor/push-notifications` plugin handles the full APNs lifecycle: requesting permission, registering for remote notifications, receiving the device token, and handling incoming notifications (foreground and background). The plugin abstracts the native Swift APNs code. The device token would be sent to the backend for server-side push delivery if/when the app adds push notification triggers. Since FR-007 is a SHOULD requirement (conditional on the app having notification functionality), the initial implementation focuses on permission handling and token registration, with actual push delivery as a future enhancement.

**Alternatives considered**:
- **Firebase Cloud Messaging (FCM)**: Adds Google dependency and SDK overhead. APNs via Capacitor is the direct, Apple-native approach.
- **OneSignal/Pusher**: Third-party services with their own SDKs. Unnecessary complexity for basic APNs support.

## R7: Accessibility Compliance

**Decision**: Apply standard web accessibility practices (ARIA labels, semantic HTML, proper heading hierarchy) in the existing React components, augmented with iOS-specific CSS for Dynamic Type scaling and touch target sizing.

**Rationale**: WKWebView on iOS supports VoiceOver for web content — it reads ARIA labels, roles, and semantic HTML elements the same way Safari does. Dynamic Type support is achieved via CSS `font: -apple-system-body` or using relative units (`rem`, `em`) that scale with the system font size when combined with the `-webkit-text-size-adjust` property. Touch target sizing is enforced by ensuring all interactive elements have `min-height: 44px` and `min-width: 44px` via Tailwind utility classes. The existing Tailwind + shadcn/ui components already use relative sizing; targeted adjustments ensure compliance.

**Alternatives considered**:
- **Native accessibility layer via Swift**: Would bypass the WebView accessibility tree. WKWebView's built-in accessibility support is sufficient and better maintained.
- **Accessibility testing library (axe-core)**: Good for automated checks but doesn't replace manual VoiceOver testing. Can be added as an optional development dependency.

## R8: App Store Submission and Compliance

**Decision**: Configure the Xcode project with required App Store metadata, privacy manifest (`PrivacyInfo.xcprivacy`), usage description strings in `Info.plist`, and App Transport Security settings for the API connection.

**Rationale**: Apple requires privacy manifests (introduced in iOS 17 but retroactively encouraged for iOS 16+ apps) declaring data collection and API usage. Capacitor-generated Xcode projects include a standard `Info.plist` that needs augmentation with `NSCameraUsageDescription`, `NSPhotoLibraryUsageDescription`, `NSLocationWhenInUseUsageDescription`, and `NSUserNotificationsUsageDescription` for any permissions the app may request. The privacy manifest declares the app's data practices for App Store transparency. App Transport Security (ATS) must allow connections to the backend API endpoint.

**Alternatives considered**:
- **Skip privacy manifest**: Would cause App Store rejection. Apple has made privacy manifests increasingly required.
- **Defer App Store submission**: The configuration should be done upfront even if submission is a later step, to avoid rework.

## R9: Capacitor Configuration and Build Pipeline

**Decision**: Add Capacitor to the existing frontend project with `capacitor.config.ts` at the frontend root. Use the existing Vite build output (`frontend/dist/`) as the web assets directory. iOS builds are triggered via `npx cap sync ios` followed by Xcode build.

**Rationale**: Capacitor is designed to work alongside existing web build tools. The `capacitor.config.ts` points to the Vite build output directory. The build workflow is: (1) `npm run build` (Vite builds to `dist/`), (2) `npx cap sync ios` (copies web assets to the Xcode project and syncs native plugins), (3) Open in Xcode or build via `xcodebuild`. This keeps the existing build pipeline intact and adds iOS as an additional output target.

**Alternatives considered**:
- **Separate iOS build project**: Would duplicate the frontend code. Capacitor's approach of building once and syncing to native projects is cleaner.
- **CI/CD with Fastlane**: Good for automation but out of scope for initial setup. Can be added later for App Store deployment automation.
