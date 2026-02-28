# Tasks: Add Native iOS Support for iPhone 14 Pro Max

**Input**: Design documents from `/specs/014-native-ios-support/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/capacitor-plugins.md, quickstart.md

**Tests**: Not requested in the feature specification. Existing frontend tests must continue to pass. Manual Xcode Simulator testing is documented in quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **iOS project**: `frontend/ios/` (Capacitor-generated Xcode project)
- **Backend**: No changes required (existing FastAPI API consumed as-is)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install Capacitor, create root configuration, and initialize platform detection utilities required by all user stories.

- [x] T001 Add Capacitor core dependencies (`@capacitor/core`, `@capacitor/cli`, `@capacitor/ios`) to `frontend/package.json`
- [x] T002 Add Capacitor plugin dependencies (`@capacitor/app`, `@capacitor/status-bar`, `@capacitor/splash-screen`, `@capacitor/keyboard`, `@capacitor/push-notifications`, `@capacitor/preferences`) to `frontend/package.json`
- [x] T003 Create Capacitor configuration file at `frontend/capacitor.config.ts` with app ID `com.agentprojects.app`, webDir `dist`, iOS settings (allowsMultipleWindows: false, scrollEnabled: true, contentInset: automatic), and plugin configs for StatusBar, SplashScreen, Keyboard, and PushNotifications per contracts/capacitor-plugins.md
- [x] T004 Create Capacitor platform detection and plugin initialization utility at `frontend/src/services/capacitor.ts` with `isNativePlatform()` helper, `isIOS()` check, and lazy plugin initialization functions that gracefully degrade on web
- [x] T005 [P] Update viewport meta tag in `frontend/index.html` to include `viewport-fit=cover` for edge-to-edge rendering on iOS (change `<meta name="viewport" ...>` to include `viewport-fit=cover`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core safe area handling and CSS infrastructure that MUST be complete before ANY user story can be implemented. All user stories depend on proper safe area insets and touch target sizing.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Add CSS safe area custom properties and touch target utility classes to `frontend/src/index.css`: define `--safe-area-top`, `--safe-area-bottom`, `--safe-area-left`, `--safe-area-right` using `env(safe-area-inset-*)` values on `:root`, and add `.ios-touch-target` class with `min-height: 44px; min-width: 44px` per contracts/capacitor-plugins.md CSS Safe Area Contract
- [x] T007 Create `SafeAreaWrapper` component at `frontend/src/components/ios/SafeAreaWrapper.tsx` that applies safe area inset padding (using the CSS custom properties from T006) to its children, ensuring no UI elements are obscured by the Dynamic Island or home indicator area. Component should conditionally apply padding only on native iOS platform using the `isNativePlatform()` helper from `frontend/src/services/capacitor.ts`
- [x] T008 Integrate `SafeAreaWrapper` into `frontend/src/App.tsx` by wrapping the root layout content with the `SafeAreaWrapper` component so all screens automatically respect safe area insets

**Checkpoint**: Foundation ready — safe area handling active, touch target styles available, Capacitor configured. User story implementation can now begin.

---

## Phase 3: User Story 1 — Native App Launch and Core Functionality (Priority: P1) 🎯 MVP

**Goal**: A user can install and launch the app on iPhone 14 Pro Max. All screens render correctly within safe areas with properly scaled layouts. All existing functionality is accessible through the native iOS interface.

**Independent Test**: Install the app on an iPhone 14 Pro Max simulator, launch it, navigate to every screen, and verify that all UI elements are visible within safe areas and all existing features work.

### Implementation for User Story 1

- [x] T009 [US1] Initialize the iOS platform by running `npx cap add ios` from the `frontend/` directory to generate the Xcode project at `frontend/ios/`
- [x] T010 [US1] Configure the Xcode project deployment target to iOS 16.0 and set the bundle identifier to `com.agentprojects.app` in `frontend/ios/App/App.xcodeproj/project.pbxproj`
- [x] T011 [P] [US1] Configure `frontend/ios/App/App/Info.plist` with `MinimumOSVersion` set to `16.0`, supported interface orientations (portrait primary), and launch storyboard settings
- [x] T012 [P] [US1] Add app icon image set to `frontend/ios/App/App/Assets.xcassets/AppIcon.appiconset/` with all required iOS icon sizes (20pt, 29pt, 40pt, 60pt, 76pt, 83.5pt at 1x/2x/3x scales) and corresponding `Contents.json` manifest
- [x] T013 [P] [US1] Configure splash screen assets in `frontend/ios/App/App/Assets.xcassets/` with appropriate launch images for iPhone 14 Pro Max resolution (2778×1284 @3x) and update the SplashScreen plugin config duration in `frontend/capacitor.config.ts`
- [x] T014 [US1] Build the Vite frontend (`npm run build` in `frontend/`) and sync to the iOS project via `npx cap sync ios` to verify the web assets are correctly bundled into the native shell
- [x] T015 [US1] Verify all existing app screens render within safe area insets on iPhone 14 Pro Max simulator — no content obscured by Dynamic Island or home indicator, all layouts properly scaled to the 6.7-inch display

**Checkpoint**: User Story 1 complete — the app launches as a native iOS app on iPhone 14 Pro Max with all screens correctly rendered within safe areas. This is a deployable MVP.

---

## Phase 4: User Story 2 — Native iOS Navigation and Gestures (Priority: P1)

**Goal**: A user navigates the app using standard iOS patterns: swipe-back gesture, tab bar for section switching, and push/pop navigation transitions consistent with Apple Human Interface Guidelines.

**Independent Test**: Navigate through multiple screens, perform swipe-back gestures from the left edge, switch between tabs, and verify navigation animations match standard iOS behavior.

### Implementation for User Story 2

- [x] T016 [US2] Enable edge-swipe back navigation by setting `allowsBackForwardNavigationGestures: true` in the `ios` section of `frontend/capacitor.config.ts` (Capacitor WKWebView native gesture support per research.md R4)
- [x] T017 [US2] Implement a bottom tab bar navigation component for section switching (board, settings, chat sections) with proper iOS styling (blur background, safe area bottom padding) — add or update the relevant layout component in `frontend/src/components/` that serves as the app shell
- [x] T018 [US2] Add CSS push/pop navigation transition animations to `frontend/src/index.css` for screen transitions that mimic standard iOS navigation stack behavior (slide-in from right, slide-out to right)
- [x] T019 [US2] Verify swipe-back gesture works on all detail/child screens in the iOS simulator and confirm tab bar switches between major sections with correct visual feedback

**Checkpoint**: User Story 2 complete — native iOS navigation patterns are functional. Swipe-back, tab bar, and transitions feel native.

---

## Phase 5: User Story 3 — Dark Mode and Light Mode Support (Priority: P2)

**Goal**: The app dynamically adapts to the iOS system Dark Mode and Light Mode settings without requiring a restart. All text maintains sufficient contrast in both modes.

**Independent Test**: Toggle the iOS simulator between Dark Mode and Light Mode in Settings and verify the app dynamically adapts its color scheme. Check contrast ratios in both modes.

### Implementation for User Story 3

- [x] T020 [P] [US3] Configure the StatusBar plugin in `frontend/src/services/capacitor.ts` to dynamically update the status bar style (light/dark content) when the system appearance changes, using `StatusBar.setStyle()` with `Style.Default` for automatic adaptation per research.md R3
- [x] T021 [P] [US3] Verify that the existing `ThemeProvider` in `frontend/src/components/ThemeProvider.tsx` correctly detects iOS `prefers-color-scheme` changes in WKWebView when the `system` theme option is active — no code changes expected per research.md R3, but verify behavior on iOS simulator
- [x] T022 [US3] Audit all screens for sufficient color contrast ratios (minimum 4.5:1 for body text) in both Dark Mode and Light Mode, and fix any contrast issues found in `frontend/src/index.css` or component-level Tailwind classes

**Checkpoint**: User Story 3 complete — Dark Mode and Light Mode work dynamically via system settings with proper contrast.

---

## Phase 6: User Story 4 — App Lifecycle and State Preservation (Priority: P2)

**Goal**: When the app enters background (phone call, home press, multitasking), user state is preserved. On resume, the app returns to exactly where the user left off. On relaunch after termination, key state is restored.

**Independent Test**: Navigate to a specific screen, background the app (⌘+Shift+H in simulator), return, and verify state is preserved. Force-quit and relaunch to verify persistent state restoration.

### Implementation for User Story 4

- [x] T023 [US4] Create the `useIOSLifecycle` hook at `frontend/src/hooks/useIOSLifecycle.ts` that uses `@capacitor/app` plugin's `appStateChange` event to detect foreground/background transitions. On background: serialize current navigation state (`activeSection`, `scrollPositions`, `formDraft`) to Capacitor Preferences under key `ios_session_state` per data-model.md Session State entity. On resume: restore state from Preferences. Include `isNativePlatform()` guard so the hook is a no-op on web.
- [x] T024 [US4] Define the `IOSSessionState` TypeScript interface in `frontend/src/hooks/useIOSLifecycle.ts` (or a shared types file) matching the contract in contracts/capacitor-plugins.md: `activeSection`, `scrollPositions`, `formDraft`, `lastSavedAt`, `appVersion`
- [x] T025 [US4] Integrate `useIOSLifecycle` hook into `frontend/src/App.tsx` so lifecycle state persistence is active app-wide. Ensure the hook reads current navigation/scroll state from the app's existing routing context and restores it on resume.
- [x] T026 [US4] Implement version-checking logic in `useIOSLifecycle` to discard stale saved state when `appVersion` in persisted data doesn't match current app version, per data-model.md validation rules

**Checkpoint**: User Story 4 complete — app state is preserved across background/resume cycles and restored after termination.

---

## Phase 7: User Story 5 — Accessibility Features (Priority: P2)

**Goal**: VoiceOver users can navigate and interact with all app features. Dynamic Type scales text without layout breakage. All touch targets meet 44×44pt minimum. Reduce Motion preference is respected.

**Independent Test**: Enable VoiceOver in iOS simulator and navigate the entire app. Set Dynamic Type to largest size and verify text scaling. Inspect touch target sizes. Enable Reduce Motion and verify animations are minimized.

### Implementation for User Story 5

- [x] T027 [P] [US5] Audit all interactive components in `frontend/src/components/` for VoiceOver compatibility — add `aria-label`, `role`, and semantic HTML elements where missing. Ensure logical focus order and meaningful labels on all buttons, links, inputs, and navigation elements
- [x] T028 [P] [US5] Add Dynamic Type font scaling support to `frontend/src/index.css` by setting `-webkit-text-size-adjust: 100%` on the root element and ensuring font sizes use relative units (`rem`, `em`) that scale with the iOS system font size. Add `font: -apple-system-body` fallback where appropriate
- [x] T029 [P] [US5] Enforce minimum 44×44pt touch targets across all interactive elements by adding `min-height: 44px; min-width: 44px` to buttons, links, and tappable elements in `frontend/src/index.css` using the `.ios-touch-target` utility class or Tailwind `min-h-[44px] min-w-[44px]` utilities on affected components
- [x] T030 [US5] Add `prefers-reduced-motion` media query support to `frontend/src/index.css` that disables or simplifies CSS animations and transitions when the iOS Reduce Motion accessibility setting is enabled (FR-014)

**Checkpoint**: User Story 5 complete — VoiceOver, Dynamic Type, touch targets, and Reduce Motion all function correctly.

---

## Phase 8: User Story 6 — Push Notifications (Priority: P3)

**Goal**: The app requests notification permission, registers for APNs, and handles incoming push notifications correctly. Notifications appear on the lock screen, in Notification Center, and as banners.

**Independent Test**: Grant notification permission when prompted, trigger a test notification, and verify it appears correctly. Deny permission and verify the app continues without notifications.

### Implementation for User Story 6

- [x] T031 [US6] Create the `usePushNotifications` hook at `frontend/src/hooks/usePushNotifications.ts` that uses `@capacitor/push-notifications` plugin to: (1) check current permission status, (2) request permission with user-facing explanation, (3) register for remote notifications and receive the APNs device token, (4) handle notification received (foreground) and notification action performed (tap) events. Include `isNativePlatform()` guard per contracts/capacitor-plugins.md error handling contract.
- [x] T032 [US6] Define the `IOSPushRegistration` TypeScript interface in `frontend/src/hooks/usePushNotifications.ts` matching the contract: `permissionStatus` (granted/denied/prompt), `deviceToken`, `registeredAt`. Persist registration state to Capacitor Preferences under key `ios_push_registration` per data-model.md
- [x] T033 [US6] Integrate `usePushNotifications` hook into the appropriate app initialization point in `frontend/src/App.tsx` or a dedicated notification setup component, requesting permission on first launch with a pre-prompt explanation
- [x] T034 [US6] Implement notification tap handling in `usePushNotifications` to navigate the user to the relevant content/screen when they tap a received notification (deep link routing)

**Checkpoint**: User Story 6 complete — push notification permission flow, APNs registration, and notification handling all functional.

---

## Phase 9: User Story 7 — App Store Submission and Compliance (Priority: P3)

**Goal**: The app is fully configured for App Store submission with all required metadata, privacy manifests, usage description strings, and compliance with Apple's guidelines.

**Independent Test**: Run Xcode's App Store validation (Product → Archive → Validate App) and verify it passes all automated checks. Review Info.plist for completeness.

### Implementation for User Story 7

- [x] T035 [P] [US7] Add all required usage description strings to `frontend/ios/App/App/Info.plist`: `NSUserNotificationsUsageDescription`, `NSCameraUsageDescription`, `NSPhotoLibraryUsageDescription`, and any other permission strings per contracts/capacitor-plugins.md Info.plist Required Entries
- [x] T036 [P] [US7] Create the privacy manifest file at `frontend/ios/App/App/PrivacyInfo.xcprivacy` declaring the app's data collection practices, API usage (required API reasons), and tracking domains per Apple's privacy manifest requirements (research.md R8)
- [x] T037 [P] [US7] Configure App Transport Security in `frontend/ios/App/App/Info.plist` to allow secure connections to the backend API endpoint while keeping `NSAllowsArbitraryLoads` set to `false` per contracts/capacitor-plugins.md
- [x] T038 [US7] Configure Xcode signing and capabilities in `frontend/ios/App/App.xcodeproj/`: set the development team, enable Push Notifications capability, and configure provisioning profiles for iOS 16+ distribution
- [x] T039 [US7] Validate the app passes Xcode's automated App Store submission checks (Archive → Validate App) and resolve any reported issues

**Checkpoint**: User Story 7 complete — app is fully configured and validated for App Store submission.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation, and cleanup across all user stories.

- [x] T040 [P] Verify existing frontend tests still pass by running `npm run test` (or equivalent) in `frontend/` — no regressions from Capacitor integration
- [x] T041 [P] Update `frontend/package.json` scripts section to include Capacitor-related commands (`cap:sync`, `cap:open`, `cap:build`) for developer convenience
- [x] T042 Run the complete quickstart.md validation workflow: build frontend, sync iOS, open in Xcode, run on iPhone 14 Pro Max simulator, verify all 12 checklist items from quickstart.md Testing section
- [x] T043 Code cleanup — remove any development-only Capacitor server URL overrides from `frontend/capacitor.config.ts`, ensure no debug logging remains in production code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — generates the iOS project required by all other stories
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs iOS project to exist)
- **User Story 3 (Phase 5)**: Depends on Phase 2 — can run in parallel with US1/US2 for CSS/verification work
- **User Story 4 (Phase 6)**: Depends on Phase 2 — can run in parallel with US1/US2 for hook development
- **User Story 5 (Phase 7)**: Depends on Phase 2 — can run in parallel with other stories
- **User Story 6 (Phase 8)**: Depends on Phase 3 (needs iOS project for APNs capability configuration)
- **User Story 7 (Phase 9)**: Depends on ALL previous user stories being complete
- **Polish (Phase 10)**: Depends on all user story phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: MUST complete first — generates the iOS Xcode project that other stories depend on
- **User Story 2 (P1)**: Depends on US1 (needs running iOS app to test navigation)
- **User Story 3 (P2)**: Can start CSS/verification work after Phase 2; iOS testing needs US1 complete
- **User Story 4 (P2)**: Can start hook development after Phase 2; iOS testing needs US1 complete
- **User Story 5 (P2)**: Can start accessibility audit after Phase 2; iOS testing needs US1 complete
- **User Story 6 (P3)**: Depends on US1 (needs iOS project for push notification capability)
- **User Story 7 (P3)**: Depends on all other stories (App Store submission is the final step)

### Within Each User Story

- Models/interfaces before services/hooks
- Services/hooks before integration into App.tsx
- Core implementation before verification/testing
- Story complete before moving to next priority

### Parallel Opportunities

- T005 (viewport meta tag) can run in parallel with T001-T004 (different files)
- T011, T012, T013 (Info.plist, app icons, splash screen) can run in parallel within US1
- T020, T021 (StatusBar config, ThemeProvider verification) can run in parallel within US3
- T027, T028, T029 (VoiceOver audit, Dynamic Type CSS, touch targets) can run in parallel within US5
- T035, T036, T037 (Info.plist strings, privacy manifest, ATS config) can run in parallel within US7
- US3 CSS work, US4 hook development, and US5 accessibility audit can overlap if US1 is not yet complete (web-only development)

---

## Parallel Example: User Story 1

```text
# After T009 (iOS platform initialized) and T010 (Xcode project configured):

# Launch these in parallel (different files, no dependencies):
Task T011: "Configure Info.plist with MinimumOSVersion in frontend/ios/App/App/Info.plist"
Task T012: "Add app icon set to frontend/ios/App/App/Assets.xcassets/AppIcon.appiconset/"
Task T013: "Configure splash screen assets in frontend/ios/App/App/Assets.xcassets/"
```

## Parallel Example: User Story 5

```text
# After Phase 2 foundational work is complete:

# Launch these in parallel (different concerns, different files):
Task T027: "VoiceOver audit of frontend/src/components/"
Task T028: "Dynamic Type font scaling in frontend/src/index.css"
Task T029: "Touch target enforcement in frontend/src/index.css and components"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T005) — install Capacitor, configure project
2. Complete Phase 2: Foundational (T006–T008) — safe area handling, App.tsx integration
3. Complete Phase 3: User Story 1 (T009–T015) — iOS platform, Xcode config, verify rendering
4. **STOP and VALIDATE**: Launch on iPhone 14 Pro Max simulator, verify all screens render correctly within safe areas
5. Deploy/demo the MVP — a working native iOS app with all existing functionality

### Incremental Delivery

1. Setup + Foundational → Capacitor installed, safe areas handled
2. User Story 1 → Native iOS app launches and renders correctly (MVP!)
3. User Story 2 → Native navigation patterns (swipe-back, tab bar, transitions)
4. User Story 3 → Dark Mode / Light Mode dynamic adaptation
5. User Story 4 → App lifecycle and state preservation
6. User Story 5 → Accessibility compliance (VoiceOver, Dynamic Type, touch targets)
7. User Story 6 → Push notifications via APNs
8. User Story 7 → App Store submission readiness
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Phase 1 + 2)
2. Developer A: User Story 1 (P1 — must complete first for iOS project)
3. Once US1 is done:
   - Developer A: User Story 2 (P1 — navigation)
   - Developer B: User Story 3 + 4 (P2 — dark mode + lifecycle)
   - Developer C: User Story 5 (P2 — accessibility)
4. After P2 stories complete:
   - Developer A: User Story 6 (P3 — push notifications)
   - Developer B: User Story 7 (P3 — App Store submission)
5. All: Polish phase

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 43 |
| **Phase 1 (Setup)** | 5 tasks |
| **Phase 2 (Foundational)** | 3 tasks |
| **US1 — Native App Launch (P1)** | 7 tasks |
| **US2 — Navigation & Gestures (P1)** | 4 tasks |
| **US3 — Dark/Light Mode (P2)** | 3 tasks |
| **US4 — Lifecycle & State (P2)** | 4 tasks |
| **US5 — Accessibility (P2)** | 4 tasks |
| **US6 — Push Notifications (P3)** | 4 tasks |
| **US7 — App Store Submission (P3)** | 5 tasks |
| **Phase 10 (Polish)** | 4 tasks |
| **Parallel opportunities** | 14 tasks marked [P] |
| **Suggested MVP scope** | Phases 1–3 (User Story 1): 15 tasks |
| **Backend changes** | None |

---

## Notes

- [P] tasks = different files, no dependencies on in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after foundational phases
- No test tasks generated (tests not requested in spec; manual Xcode Simulator testing per quickstart.md)
- Backend is entirely unchanged — iOS app consumes the same FastAPI endpoints
- Existing frontend tests must continue to pass (verified in T040)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
