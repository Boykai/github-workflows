# Implementation Plan: Add Native iOS Support for iPhone 14 Pro Max

**Branch**: `014-native-ios-support` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-native-ios-support/spec.md`

## Summary

Package the existing React/TypeScript web application as a native iOS app for iPhone 14 Pro Max using Capacitor. The approach wraps the existing Vite-built frontend in a native iOS WebView shell, adds Capacitor plugins for native device APIs (push notifications, status bar, splash screen, keyboard), and configures the Xcode project for iOS 16+ with proper safe area handling, Dark Mode support, native navigation patterns, and accessibility compliance. The backend API remains unchanged — the iOS app communicates with the same FastAPI endpoints. See [research.md](./research.md) for decision rationale.

## Technical Context

**Language/Version**: TypeScript/React 18 (frontend), Python 3.11 (backend — unchanged), Swift (Capacitor native bridge)
**Primary Dependencies**: Capacitor 6 (iOS shell), @capacitor/ios, @capacitor/push-notifications, @capacitor/status-bar, @capacitor/splash-screen, @capacitor/keyboard, @capacitor/app (lifecycle)
**Storage**: Existing SQLite backend (unchanged); Capacitor Preferences plugin for client-side state persistence
**Testing**: Vitest (existing frontend tests), Xcode Simulator (manual iOS testing), Appium or XCUITest (optional E2E)
**Target Platform**: iOS 16+ (iPhone 14 Pro Max primary, other iOS devices secondary)
**Project Type**: Mobile + Web (hybrid — Capacitor wraps existing web frontend)
**Performance Goals**: App launch within 3 seconds, 60fps scrolling, touch response <100ms (spec SC-001)
**Constraints**: Requires macOS + Xcode 15+ for builds, Apple Developer Program ($99/year) for distribution, portrait orientation primary
**Scale/Scope**: ~10 screens (existing web app screens), 1 new Xcode project, 5-6 Capacitor plugins, CSS/layout updates for safe areas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with 7 prioritized user stories (P1-P3), Given-When-Then scenarios, 14 FRs, edge cases, and measurable success criteria |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md and Phase 0/1 artifacts |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; manual Xcode Simulator testing for verification. Existing frontend tests must continue to pass |
| V. Simplicity and DRY | ✅ PASS | Reuses existing React frontend via Capacitor wrapper — no rewrite. Minimal new code for native bridge configuration |

### Post-Design Check (Phase 1 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All FR items (FR-001 through FR-014) have corresponding design decisions in research.md and implementation steps |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all generated |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan ready for handoff to `speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No test mandate; existing tests must pass. Manual iOS Simulator testing documented in quickstart.md |
| V. Simplicity and DRY | ✅ PASS | Capacitor reuses 100% of existing React code. New code limited to: Capacitor config, CSS safe area adjustments, lifecycle hooks, and Xcode project config. No new frameworks or abstractions beyond Capacitor |

## Project Structure

### Documentation (this feature)

```text
specs/014-native-ios-support/
├── plan.md              # This file
├── research.md          # Phase 0: Technical decisions and rationale
├── data-model.md        # Phase 1: Entity definitions and state models
├── quickstart.md        # Phase 1: iOS development setup guide
├── contracts/
│   └── capacitor-plugins.md  # Phase 1: Capacitor plugin configuration contracts
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
backend/                              # UNCHANGED — existing FastAPI backend
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/                             # Existing React frontend + Capacitor additions
├── src/
│   ├── components/
│   │   └── ios/
│   │       └── SafeAreaWrapper.tsx   # Safe area inset wrapper component
│   ├── hooks/
│   │   ├── useIOSLifecycle.ts        # App lifecycle event handling (FR-006, FR-013)
│   │   └── usePushNotifications.ts   # APNs push notification hook (FR-007)
│   ├── pages/
│   ├── services/
│   │   └── capacitor.ts             # Capacitor plugin initialization and helpers
│   ├── index.css                     # Updated: safe area CSS variables, touch targets
│   └── App.tsx                       # Updated: SafeAreaWrapper, lifecycle integration
├── ios/                              # Capacitor-generated Xcode project
│   └── App/
│       ├── App.xcodeproj/
│       ├── App/
│       │   ├── Info.plist            # iOS config: permissions, min version, privacy manifest
│       │   ├── Assets.xcassets/      # App icons, splash screen assets
│       │   └── capacitor.config.ts   # Capacitor iOS-specific config
│       └── Podfile                   # CocoaPods dependencies for Capacitor plugins
├── capacitor.config.ts               # Root Capacitor configuration
├── package.json                      # Updated: Capacitor dependencies added
└── tests/                            # Existing tests (must continue to pass)
```

**Structure Decision**: Hybrid Mobile + Web structure. The existing `backend/` and `frontend/` directories are preserved. Capacitor adds an `ios/` subdirectory inside `frontend/` containing the generated Xcode project. New frontend code is minimal: a safe area wrapper component, lifecycle hook, push notification hook, and Capacitor service utility. The backend is entirely unchanged.

## Complexity Tracking

> No constitution violations detected. All design decisions follow existing patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
