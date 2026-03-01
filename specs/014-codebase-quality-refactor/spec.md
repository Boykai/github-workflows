# Feature Specification: Refactor Codebase for Quality, Best Practices, and UX Improvements

**Feature Branch**: `014-codebase-quality-refactor`  
**Created**: 2026-02-28  
**Status**: Draft  
**Input**: User description: "Refactor Codebase for Quality, Best Practices, and UX Improvements"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct Default Status Column Values (Priority: P1)

An administrator sets up a new project and expects the default status columns to match the application's canonical workflow statuses. Currently, the system uses "Todo" as a default status column, but "Todo" is not a recognized status name — the valid statuses are Backlog, Ready, In Progress, In Review, and Done. This mismatch can cause status lookups and comparisons to silently fail, producing confusing behavior for any user managing project workflows.

**Why this priority**: This is a data correctness bug that affects every newly created project. Incorrect default values propagate throughout the system and can cause downstream failures in workflow automation, status filtering, and agent task assignments.

**Independent Test**: Can be verified by creating a new project with default settings and confirming all default status columns correspond to valid `StatusNames` values.

**Acceptance Scenarios**:

1. **Given** a fresh project with no custom status configuration, **When** the system assigns default status columns, **Then** all column names are valid `StatusNames` values (no "Todo" appears).
2. **Given** the `DEFAULT_STATUS_COLUMNS` constant, **When** inspected by a developer, **Then** every entry references a `StatusNames` enum attribute rather than a hardcoded string.

---

### User Story 2 - Prevent Duplicate Admin Promotion (Priority: P1)

The first authenticated user is automatically promoted to administrator. However, if two users authenticate at nearly the same time before any admin exists, both could be promoted due to a time-of-check-to-time-of-use (TOCTOU) race condition. This means the system could end up with an incorrectly recorded admin, undermining the single-admin authorization model.

**Why this priority**: This is a security-relevant bug. If the wrong user becomes admin, they gain full control of global settings. Fixing this ensures exactly one user is atomically promoted as the system administrator.

**Independent Test**: Can be verified by simulating two concurrent admin-promotion requests against a database with no admin set and confirming only one succeeds.

**Acceptance Scenarios**:

1. **Given** no admin is configured in global settings, **When** two users authenticate simultaneously, **Then** exactly one user is promoted to admin and the other receives a 403 Forbidden response.
2. **Given** an admin is already configured, **When** a new user authenticates, **Then** the existing admin remains unchanged and the new user receives 403 if they attempt admin actions.

---

### User Story 3 - Resilient Application Startup (Priority: P2)

An operations engineer deploys the application. If the database initialization or settings seeding fails during startup, the application should clean up any partially started background tasks and signal listeners rather than leaving orphaned processes running. This prevents resource leaks and confusing error states.

**Why this priority**: Startup failures that leave orphaned tasks can cause cascading problems — stale connections, log noise, and difficult-to-diagnose issues in production. Proper cleanup on failure is a reliability best practice.

**Independent Test**: Can be verified by simulating a startup failure (e.g., database connection error) and confirming that no background tasks or listeners remain running after the failure.

**Acceptance Scenarios**:

1. **Given** a database initialization failure during startup, **When** the lifespan handler exits, **Then** all background tasks (cleanup loop) and listeners (Signal WebSocket) are cancelled or stopped.
2. **Given** a successful startup, **When** the application shuts down normally, **Then** all resources are cleaned up as before (no regression).

---

### User Story 4 - Lightweight Docker Health Checks (Priority: P2)

An operations engineer monitors the backend container's health via Docker. The current healthcheck spawns a full Python interpreter with the `httpx` library imported every 30 seconds, consuming unnecessary memory and CPU. Switching to a lightweight alternative reduces resource overhead without sacrificing health monitoring.

**Why this priority**: In resource-constrained environments (small VMs, CI runners), the repeated Python startup adds measurable overhead. A stdlib or system utility approach is a well-established best practice for container healthchecks.

**Independent Test**: Can be verified by building the Docker image and confirming the healthcheck command runs successfully using a lightweight utility instead of the full Python/httpx stack.

**Acceptance Scenarios**:

1. **Given** the backend Docker container is running, **When** the healthcheck fires every 30 seconds, **Then** it uses a stdlib module or system utility instead of importing `httpx`.
2. **Given** the backend is unhealthy, **When** the healthcheck fires, **Then** it correctly reports failure (non-zero exit code).

---

### User Story 5 - Auto-Detect Secure Cookie Flag (Priority: P2)

A developer deploys the application with `frontend_url` set to an HTTPS URL but forgets to set `cookie_secure=True`. The application should automatically detect that HTTPS is in use and enforce the secure cookie flag, preventing session cookies from being transmitted over insecure connections.

**Why this priority**: Misconfigured cookie security is a common deployment mistake that can expose session tokens to network interception. Auto-detection provides defense-in-depth without requiring extra configuration.

**Independent Test**: Can be verified by configuring `frontend_url` with an HTTPS URL and confirming the effective cookie secure flag is True, even when `cookie_secure` is not explicitly set.

**Acceptance Scenarios**:

1. **Given** `frontend_url` starts with `https://` and `cookie_secure` is not explicitly set, **When** the application reads cookie configuration, **Then** the effective cookie secure flag is True.
2. **Given** `frontend_url` starts with `http://` and `cookie_secure` is False, **When** the application reads cookie configuration, **Then** the effective cookie secure flag is False (local development behavior preserved).
3. **Given** `cookie_secure` is explicitly set to True, **When** the application reads cookie configuration, **Then** the effective cookie secure flag is True regardless of `frontend_url`.

---

### User Story 6 - Complete Dictionary Interface for BoundedDict (Priority: P3)

A developer uses the `BoundedDict` utility class and expects it to support standard dictionary operations such as `get()`, `pop()`, `keys()`, `values()`, `items()`, iteration, `clear()`, and a meaningful string representation. Missing methods force workarounds or prevent the class from being used as a drop-in dictionary replacement.

**Why this priority**: This is a code quality improvement. While `BoundedDict` is functional for basic use cases, a complete dict-like API improves developer experience and prevents subtle bugs when the class is passed to code expecting a standard dictionary interface.

**Independent Test**: Can be verified by calling each dictionary method on a `BoundedDict` instance and confirming correct behavior matches Python's built-in dict.

**Acceptance Scenarios**:

1. **Given** a populated `BoundedDict`, **When** `get()`, `pop()`, `keys()`, `values()`, `items()`, `__iter__()`, `clear()`, and `__repr__()` are called, **Then** each method behaves consistently with Python's built-in dict semantics.

---

### User Story 7 - Remove Unused DOM Testing Library (Priority: P3)

A developer installs frontend dependencies and notices both `happy-dom` and `jsdom` are listed. Since the Vitest configuration only uses one of them (`happy-dom`), the unused library adds unnecessary install size and potential confusion about which library is authoritative for tests.

**Why this priority**: This is a maintenance and developer experience improvement. Removing unused dependencies reduces install time, avoids confusion, and keeps the dependency tree lean.

**Independent Test**: Can be verified by removing the unused library, running all frontend tests, and confirming they pass without changes.

**Acceptance Scenarios**:

1. **Given** the Vitest configuration uses `happy-dom` as the test environment, **When** `jsdom` is removed from `package.json`, **Then** all frontend tests continue to pass.
2. **Given** the updated `package.json`, **When** a developer runs `npm install`, **Then** only one DOM testing library is installed.

---

### User Story 8 - Settings Cache Clearing Utility (Priority: P3)

A developer writes tests that mock the `get_settings()` function. Between tests, the LRU cache retains stale `MagicMock` instances, causing test pollution and hard-to-diagnose failures. A dedicated `clear_settings_cache()` utility makes it straightforward and explicit to reset the cache in test teardown.

**Why this priority**: Test reliability improvements prevent flaky tests and reduce developer frustration. While `get_settings.cache_clear()` already exists via `lru_cache`, a named utility is more discoverable and communicates intent.

**Independent Test**: Can be verified by calling `clear_settings_cache()` between tests and confirming that mock settings from a previous test do not leak into subsequent tests.

**Acceptance Scenarios**:

1. **Given** a test that patches `get_settings()` with a mock, **When** `clear_settings_cache()` is called after the test, **Then** subsequent calls to `get_settings()` do not return the stale mock.

---

### User Story 9 - Exponential Backoff for Session Cleanup Errors (Priority: P3)

An operations engineer monitors application logs. If the session cleanup background task encounters a persistent error (e.g., database lock), it currently retries at a fixed interval, flooding logs with identical error messages. Adding exponential backoff (capped at 5 minutes) reduces log noise and gives the system time to recover.

**Why this priority**: This is an operational improvement. Log spam from repeated failures makes it harder to spot genuine new issues and can fill disk space. Capped backoff is a standard reliability pattern.

**Independent Test**: Can be verified by simulating repeated cleanup failures and confirming the retry interval increases with each consecutive failure up to the cap, then resets on success.

**Acceptance Scenarios**:

1. **Given** the session cleanup task encounters a persistent error, **When** it retries, **Then** the wait interval increases exponentially (e.g., 1×, 2×, 4× the base interval) up to a maximum of 5 minutes.
2. **Given** the cleanup task recovers after a series of failures, **When** the next successful run completes, **Then** the backoff interval resets to the base interval.

---

### User Story 10 - Flexible Environment File Resolution (Priority: P3)

A developer runs the application locally (from the `backend/` directory) and also via Docker (where the working directory is `/app`). The Settings configuration should resolve the `.env` file from both locations so that environment configuration works seamlessly in both contexts without manual path adjustment.

**Why this priority**: This is a developer experience improvement that reduces friction during local development. Incorrect `.env` resolution can silently fall back to defaults, causing confusing behavior.

**Independent Test**: Can be verified by placing a `.env` file in the expected location for each context and confirming that Settings loads values from it correctly.

**Acceptance Scenarios**:

1. **Given** a `.env` file exists in the `backend/` directory, **When** the application is run from `backend/`, **Then** Settings loads values from that `.env` file.
2. **Given** a `.env` file exists one directory above the working directory, **When** the application is run from a subdirectory (e.g., Docker `/app`), **Then** Settings loads values from `../.env`.

---

### Edge Cases

- What happens if the `DEFAULT_STATUS_COLUMNS` constant is referenced in code that compares against user-supplied status names — are all comparison points updated?
- How does the admin auto-promotion behave if the global_settings table has no rows (race condition on initial seed)?
- What happens if the Docker healthcheck URL changes or the health endpoint is disabled?
- What happens if `frontend_url` is set to an invalid URL or uses a non-standard scheme?
- What happens if `BoundedDict.pop()` is called on an empty dict with no default?
- What if both `.env` and `../.env` exist — which takes precedence?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use `StatusNames` enum values exclusively in `DEFAULT_STATUS_COLUMNS` — the literal string `"Todo"` MUST be replaced with the correct canonical status name.
- **FR-002**: System MUST use an atomic database operation for admin auto-promotion that prevents race conditions when no admin is set — specifically, the promotion MUST only succeed if `admin_github_user_id IS NULL` at the time of the update.
- **FR-003**: System MUST wrap application startup logic (database init, settings seeding) in error-handling that guarantees cleanup of background tasks and listeners on failure.
- **FR-004**: Docker Compose backend healthcheck MUST use a lightweight approach (stdlib `urllib.request` or system `curl`) instead of importing the `httpx` library.
- **FR-005**: Settings MUST expose a computed property (`effective_cookie_secure`) that returns True when `cookie_secure` is True OR when `frontend_url` starts with `https://`.
- **FR-006**: All cookie-setting code MUST use the `effective_cookie_secure` property instead of the raw `cookie_secure` field.
- **FR-007**: `BoundedDict` MUST implement the complete dict-like interface: `get()`, `pop()`, `keys()`, `values()`, `items()`, `__iter__()`, `clear()`, and `__repr__()`.
- **FR-008**: Frontend `package.json` MUST contain only the DOM testing library that is actively used in the Vitest configuration (currently `happy-dom`); the unused library (`jsdom`) MUST be removed.
- **FR-009**: A `clear_settings_cache()` utility function MUST be provided alongside `get_settings()` to explicitly clear the settings LRU cache.
- **FR-010**: The session cleanup background task MUST implement exponential backoff on repeated failures, with the backoff interval capped at 5 minutes, and MUST reset the interval after a successful run.
- **FR-011**: Settings MUST check both `.env` and `../.env` for environment file resolution to support both local development and Docker deployment contexts.

### Key Entities *(include if feature involves data)*

- **StatusNames**: Enum-like class defining canonical workflow status column names (Backlog, Ready, In Progress, In Review, and Done). Referenced by `DEFAULT_STATUS_COLUMNS` and agent mappings.
- **GlobalSettings**: Database table (singleton row, id=1) storing application configuration including `admin_github_user_id`. Subject to atomic update for admin promotion.
- **BoundedDict**: Generic utility class providing a capacity-limited dictionary with FIFO eviction, backed by `OrderedDict`.
- **Settings**: Application settings model loaded from environment variables, cached via LRU cache. Extended with `effective_cookie_secure` property.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All default status column values match canonical status names — zero instances of "Todo" remain in status column defaults or enum-dependent code paths.
- **SC-002**: Concurrent admin promotion attempts result in exactly one admin — verified by simulating simultaneous requests.
- **SC-003**: Application startup failures result in zero orphaned background tasks or listeners — verified by inspecting running tasks after a simulated startup failure.
- **SC-004**: Docker healthcheck command execution completes in under 1 second on average (compared to multi-second full interpreter startup with transitive dependencies).
- **SC-005**: Cookie secure flag is automatically True when `frontend_url` uses HTTPS — verified across all deployment configurations without manual `cookie_secure` override.
- **SC-006**: `BoundedDict` passes a comprehensive dict-interface test suite covering all standard dictionary methods.
- **SC-007**: Frontend dependency install includes exactly one DOM testing library — no unused DOM library remains in the dependency manifest.
- **SC-008**: Settings cache can be reliably cleared between tests — zero mock leaks detected across the test suite.
- **SC-009**: Session cleanup errors produce logarithmically decreasing log frequency — verified by counting log entries during sustained failure simulation.
- **SC-010**: Environment file resolution works in both local and containerized working directories — verified by running settings loading in both contexts.
