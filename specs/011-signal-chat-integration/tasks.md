# Tasks: Signal Messaging Integration

**Input**: Design documents from `/specs/011-signal-chat-integration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in feature specification. Test tasks omitted.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- All paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Signal sidecar service and configure backend dependencies

- [x] T001 Add signal-api sidecar service (bbernhard/signal-cli-rest-api, json-rpc mode, styled text, signal-cli-config volume) to docker-compose.yml
- [x] T002 [P] Add SIGNAL_API_URL and SIGNAL_PHONE_NUMBER settings to backend/src/config.py
- [x] T003 [P] Add tenacity and websockets dependencies to backend/pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema, shared models, and base service layer that ALL user stories depend on

**⚠ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Create database migration with signal_connections, signal_messages, and signal_conflict_banners tables (per data-model.md) in backend/src/migrations/004_add_signal_tables.sql
- [x] T005 [P] Create Signal Pydantic models (SignalConnection, SignalMessage, SignalConflictBanner) and request/response schemas (SignalConnectionResponse, SignalLinkRequest, SignalLinkResponse, SignalLinkStatusResponse, SignalPreferencesResponse, SignalPreferencesUpdate, SignalInboundMessage, SignalBanner, SignalBannersResponse) per contracts/signal-api.yaml in backend/src/models/signal.py
- [x] T006 [P] Add Signal TypeScript types (SignalConnection, SignalLinkResponse, SignalLinkStatus, SignalPreferences, SignalBanner, SignalInboundMessage) to frontend/src/types/index.ts
- [x] T007 [P] Add Signal API client functions (getSignalConnection, initiateSignalLink, checkSignalLinkStatus, disconnectSignal, getSignalPreferences, updateSignalPreferences, getSignalBanners, dismissSignalBanner) to frontend/src/services/api.ts
- [x] T008 Create signal_bridge.py with core async HTTP client for signal-cli-rest-api (base URL from config, httpx.AsyncClient, methods: request_qr_code, check_link_complete, send_message, get_accounts) in backend/src/services/signal_bridge.py

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Connect Signal Account (Priority: P1) 🎯 MVP

**Goal**: Users link/disconnect their Signal account via QR code in Settings, see connection status, and receive conflict banners when displaced

**Independent Test**: Navigate to Settings → Connect Signal → scan QR code → see "Connected" status with masked phone number. Disconnect → status returns to "Not Connected". Link same phone from another account → displaced user sees dismissible banner.

### Implementation for User Story 1

- [x] T009 [US1] Implement connection lifecycle service methods (create_link_session with QR code proxy from signal-cli-rest-api, complete_link with Fernet-encrypted phone storage and SHA-256 hash, get_connection, disconnect_and_purge with immediate PII deletion per FR-014, detect_phone_conflict with old-link deactivation and banner creation per FR-015) in backend/src/services/signal_bridge.py
- [x] T010 [US1] Implement connection management endpoints: POST /api/v1/signal/connection/link (proxy QR code as base64 PNG), GET /api/v1/signal/connection/link/status (poll link completion), GET /api/v1/signal/connection (return status with masked phone), DELETE /api/v1/signal/connection (disconnect and purge PII) in backend/src/api/settings.py
- [x] T011 [US1] Implement conflict banner endpoints: GET /api/v1/signal/banners (return undismissed banners for current user), POST /api/v1/signal/banners/{banner_id}/dismiss (mark banner dismissed) in backend/src/api/settings.py
- [x] T012 [P] [US1] Add Signal connection React Query hooks (useSignalConnection, useInitiateSignalLink, useSignalLinkStatus with polling interval, useDisconnectSignal, useSignalBanners, useDismissBanner) to frontend/src/hooks/useSettings.ts
- [x] T013 [US1] Create SignalConnection.tsx component with QR code display (base64 img), connection status indicator (Connected/Not Connected/Error), masked phone number, disconnect button with confirmation, and conflict banner dismissal UI in frontend/src/components/settings/SignalConnection.tsx
- [x] T014 [US1] Integrate SignalConnection as a new SettingsSection in frontend/src/pages/SettingsPage.tsx

**Checkpoint**: User Story 1 fully functional — users can link, view status, disconnect, and see conflict banners in Settings

---

## Phase 4: User Story 2 — Receive App Chat Messages via Signal (Priority: P2)

**Goal**: Assistant and system chat messages are automatically forwarded to the user's linked Signal account with styled formatting and deep links

**Independent Test**: With a connected Signal account, send a message in app chat → receive corresponding Signal message within 30 seconds. Disconnect → no Signal messages sent. Simulate delivery failure → verify 3 retries with backoff then message dropped.

### Implementation for User Story 2

- [x] T015 [US2] Create signal_delivery.py with outbound message formatter: styled text (*bold* headers, _italic_ metadata, emoji anchors 📋✅❌👉), deep link URLs to app, action-bearing message summaries (task proposals, status changes per FR-005), and message truncation to Signal limits in backend/src/services/signal_delivery.py
- [x] T016 [US2] Add delivery execution to signal_delivery.py: tenacity retry decorator (stop_after_attempt=4, wait_exponential 30s/2min/8min per FR-008), asyncio.create_task fire-and-forget wrapper, signal_messages audit row creation (pending→delivered/retrying→failed), and structured logging (before_sleep_log) in backend/src/services/signal_delivery.py
- [x] T017 [US2] Hook outbound Signal delivery into chat message creation flow: after add_message() creates an assistant or system message, call fire-and-forget delivery if user has an active signal_connection with status='connected' in backend/src/api/chat.py

**Checkpoint**: User Story 2 fully functional — outbound messages reach Signal with retry resilience

---

## Phase 5: User Story 3 — Send Messages from Signal to App Chat (Priority: P3)

**Goal**: Inbound Signal messages from linked users appear in the app's chat and trigger the AI workflow, with project routing and auto-replies for edge cases

**Independent Test**: Send a Signal message to the app's number → message appears in app chat within 30 seconds and AI assistant responds. Send with `#project-name` → routes to that project. Send from unlinked number → receive auto-reply. Send image → receive "text only" auto-reply.

### Implementation for User Story 3

- [x] T018 [US3] Implement WebSocket listener with reconnection loop (5s/10s backoff) for inbound Signal messages from signal-cli-rest-api ws://signal-api:8080/v1/receive/{number} in backend/src/services/signal_bridge.py
- [x] T019 [US3] Implement inbound message processing: phone hash lookup in signal_connections, project routing via last_active_project_id (FR-006), #project-name override parsing and project update (FR-013), auto-reply for unlinked senders (FR-009), auto-reply for media/attachment messages (FR-010), message truncation at 100K chars in backend/src/services/signal_bridge.py
- [x] T020 [US3] Add inbound message handler that creates a user chat message via add_message flow and triggers AI assistant processing, with signal_messages audit row (direction=inbound) in backend/src/api/webhooks.py
- [x] T021 [US3] Register WebSocket listener as background task on application startup (lifespan context manager) and graceful shutdown in backend/src/main.py

**Checkpoint**: User Story 3 fully functional — bidirectional Signal↔App messaging works end-to-end

---

## Phase 6: User Story 4 — Manage Signal Notification Preferences (Priority: P4)

**Goal**: Users control which message categories (all, actions only, confirmations only, none) are forwarded to Signal

**Independent Test**: Set preference to "Action Proposals Only" → general assistant replies are NOT forwarded, but task proposals ARE forwarded. Change to "None" → no messages forwarded. Change to "All" → all messages forwarded.

### Implementation for User Story 4

- [x] T022 [US4] Implement GET /api/v1/signal/preferences (read notification_mode from signal_connections) and PUT /api/v1/signal/preferences (update notification_mode, validate enum: all/actions_only/confirmations_only/none) endpoints in backend/src/api/settings.py
- [x] T023 [P] [US4] Add notification preference filtering to outbound delivery pipeline: before sending, check connection.notification_mode and message type (action_type field), skip delivery if preference excludes this category (FR-007) in backend/src/services/signal_delivery.py
- [x] T024 [P] [US4] Add preference query/mutation hooks (useSignalPreferences, useUpdateSignalPreferences) to frontend/src/hooks/useSettings.ts
- [x] T025 [US4] Add notification preference toggle UI (radio group: All Messages, Action Proposals Only, System Confirmations Only, None) to the SignalConnection component in frontend/src/components/settings/SignalConnection.tsx

**Checkpoint**: User Story 4 fully functional — preference changes take effect within 60 seconds (SC-007)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that span multiple user stories

- [x] T026 [P] Add Signal conflict banner display to chat view layout (fetch active banners on chat/settings page load per FR-015, show dismissible banner component) in frontend/src/App.tsx or appropriate layout wrapper
- [x] T027 [P] Update root README.md with Signal integration section (setup, environment variables, architecture diagram)
- [x] T028 Add signal-api health check and production-ready depends_on with service_healthy condition to docker-compose.yml
- [x] T029 Validate full end-to-end flow against specs/011-signal-chat-integration/quickstart.md scenarios (link, send outbound, receive inbound, preferences, disconnect)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start immediately after Phase 2
  - US2 (Phase 4): Can start after Phase 2; independent of US1 at code level, but US1 creates the connection US2 needs at runtime
  - US3 (Phase 5): Can start after Phase 2; independent of US1/US2 at code level
  - US4 (Phase 6): Can start after Phase 2; adds filtering to US2's delivery pipeline
  - **Recommended sequential order**: US1 → US2 → US3 → US4 (each builds on runtime state from prior stories)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Code Dependencies | Runtime Dependencies |
|-------|-------------------|---------------------|
| **US1** (Connect) | Phase 2 only | None — standalone |
| **US2** (Outbound) | Phase 2 only | Needs active connection (US1) |
| **US3** (Inbound) | Phase 2 only | Needs active connection (US1) |
| **US4** (Preferences) | Phase 2 + T015/T016 (signal_delivery.py) | Needs active connection (US1) |

### Within Each User Story

- Service layer before API endpoints
- Backend before frontend (frontend needs API to call)
- Hooks before components (components use hooks)
- Components before page integration
- Core implementation before integration points

### Parallel Opportunities

**Phase 1** — All 3 tasks touch different files:
```
T001 (docker-compose.yml) ‖ T002 (config.py) ‖ T003 (pyproject.toml)
```

**Phase 2** — 4 of 5 tasks are independent:
```
T004 (migration SQL) ‖ T005 (models/signal.py) ‖ T006 (types/index.ts) ‖ T007 (api.ts)
→ then T008 (signal_bridge.py, depends on T002+T005)
```

**Phase 3 (US1)** — Backend and frontend tracks run in parallel:
```
Backend:  T009 → T010 → T011
                              ↘
Frontend: T012 ──────→ T013 → T014
```

**Phase 6 (US4)** — Backend and frontend tracks partially parallel:
```
T022 (settings.py)  ‖  T023 (signal_delivery.py)  ‖  T024 (useSettings.ts)
                                                        → T025 (SignalConnection.tsx)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (5 tasks)
3. Complete Phase 3: User Story 1 — Connect Signal Account (6 tasks)
4. **STOP AND VALIDATE**: Link a Signal account via QR code, verify status display, test disconnect
5. Deploy/demo if ready — **14 tasks to MVP**

### Incremental Delivery

1. Setup + Foundational → Foundation ready (8 tasks)
2. **Add US1** → Link/disconnect Signal accounts → Deploy/Demo (**MVP!**)
3. **Add US2** → Outbound message delivery with retry → Deploy/Demo
4. **Add US3** → Inbound message routing with AI workflow → Deploy/Demo
5. **Add US4** → Notification preference controls → Deploy/Demo
6. Polish → Production hardening → Final release
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers after Phase 2 completes:
- **Developer A**: US1 backend (T009–T011) → US2 (T015–T017)
- **Developer B**: US1 frontend (T012–T014) → US4 frontend (T024–T025)
- **Developer C**: US3 (T018–T021) → US4 backend (T022–T023)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [USn] label maps task to user story for traceability
- No test tasks included — tests were not requested in the feature specification
- signal-cli-rest-api runs in `json-rpc` mode for lowest latency (research.md Topic 1)
- Phone numbers encrypted with existing Fernet `EncryptionService`; SHA-256 hash for lookup (data-model.md)
- WebSocket used for inbound messages, NOT polling (research.md Topic 5)
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
