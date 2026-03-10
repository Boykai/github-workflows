# Feature Specification: Fix Silent Failures & Security

**Feature Branch**: `033-fix-silent-failures-security`  
**Created**: 2026-03-10  
**Status**: Draft  
**Input**: User description: "Phase 1: Critical — Fix Silent Failures & Security"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Eliminate Critical Silent Exception Swallowing (Priority: P1)

As a platform operator, I need all critical system errors to be logged so that I can detect, diagnose, and resolve runtime failures before they impact users. Currently, 4 critical locations silently discard exceptions with `except: pass`, hiding workflow configuration failures, database read failures, branch update failures, and cleanup errors from all monitoring and observability.

**Why this priority**: Silent failures in core services (workflow config, database reads, branch updates) can cascade into data inconsistencies and broken user experiences with zero visibility. This is the highest-impact reliability fix since it directly prevents hidden runtime bugs across the entire platform.

**Independent Test**: Can be fully tested by triggering exceptions in each of the 4 critical code paths and verifying that log output is produced at the expected level (warning or debug). Delivers immediate value by making previously invisible failures observable.

**Acceptance Scenarios**:

1. **Given** a workflow config fetch fails during project processing, **When** the exception occurs, **Then** a warning-level log entry is recorded with the project identifier and full exception details.
2. **Given** a branch HEAD OID update fails, **When** the exception occurs, **Then** a warning-level log entry is recorded with the branch name and full exception details.
3. **Given** the client cleanup loop encounters an error during shutdown, **When** the exception occurs, **Then** a debug-level log entry is recorded with full exception details.
4. **Given** a metadata read from the local database fails, **When** the exception occurs and the system falls back to hardcoded defaults, **Then** a warning-level log entry is recorded with the repository key and full exception details.
5. **Given** any of the above exceptions occur, **When** the system logs the error, **Then** the exception traceback is included via `exc_info` to support root-cause analysis.

---

### User Story 2 - Log Database Update Failures in Agent Pipeline (Priority: P1)

As a platform operator, I need database update failures in the agent creation pipeline to be logged at error level so that I can detect when critical metadata (issue numbers, branch names, PR numbers) fails to persist. Currently, 4 locations silently discard database write failures, which can lead to orphaned resources and broken cross-references.

**Why this priority**: Database write failures that silently pass can cause agents to operate without correct issue numbers, branch names, or PR references — leading to broken automation pipelines and data integrity issues that are extremely difficult to diagnose after the fact.

**Independent Test**: Can be fully tested by simulating database write failures in each of the 4 agent creator code paths and verifying that error-level or warning-level log output is produced with agent/project identifiers and full exception details.

**Acceptance Scenarios**:

1. **Given** updating `github_issue_number` for an agent fails, **When** the exception occurs, **Then** an error-level log entry is recorded with the agent identifier and full exception details.
2. **Given** updating `branch_name` for an agent fails, **When** the exception occurs, **Then** an error-level log entry is recorded with the agent identifier and full exception details.
3. **Given** updating `github_pr_number` for an agent fails, **When** the exception occurs, **Then** an error-level log entry is recorded with the agent identifier and full exception details.
4. **Given** owner/repo resolution fails during the agent pipeline, **When** the exception occurs, **Then** a warning-level log entry is recorded with the project identifier and full exception details.

---

### User Story 3 - Prevent Exception Detail Leaks to End Users (Priority: P1)

As a security-conscious platform operator, I need to ensure that raw exception messages and internal system details are never exposed to end users through external messaging channels. Currently, at least 3 locations in the Signal messaging integration send raw Python exception text directly to users, which can reveal internal file paths, database schemas, library versions, and other sensitive implementation details.

**Why this priority**: Information disclosure through error messages is a well-known security vulnerability. Exposing internal exception details can aid attackers in crafting targeted exploits and violates the principle of least information. This must be fixed alongside silent failures since both relate to exception handling hygiene.

**Independent Test**: Can be fully tested by triggering exceptions in each Signal message handling path and verifying that (a) the user receives a generic, friendly error message and (b) the full exception details are logged server-side at the appropriate level.

**Acceptance Scenarios**:

1. **Given** an `#agent` command fails with an internal exception, **When** the error response is sent to the user via Signal, **Then** the user receives a generic friendly error message (no internal details) and the full exception is logged server-side at error level.
2. **Given** any Signal command handler encounters an unexpected exception, **When** the error is communicated to the user, **Then** the response message contains no Python exception text, file paths, stack traces, or internal identifiers.
3. **Given** multiple distinct exception types occur in Signal handlers, **When** errors are reported to users, **Then** all error messages follow a consistent, user-friendly format.

---

### User Story 4 - Log Signal Context Resolution Failures (Priority: P2)

As a platform operator, I need to know when the Signal messaging flow cannot resolve repository context for a project, so that I can investigate and fix configuration issues. Currently, this failure is silently swallowed, causing the signal flow to proceed without essential owner/repo context.

**Why this priority**: While not as critical as data loss or security issues, silent context resolution failures can lead to confusing downstream behavior and misrouted messages. Logging provides the diagnostic foundation needed to identify and fix these issues.

**Independent Test**: Can be fully tested by simulating a repository resolution failure in the Signal chat flow and verifying that a warning-level log entry is produced with the project identifier.

**Acceptance Scenarios**:

1. **Given** the Signal flow cannot resolve the repository for a project, **When** the exception occurs, **Then** a warning-level log entry is recorded with the project identifier and full exception details.
2. **Given** the repository resolution fails, **When** the flow continues without context, **Then** the missing context does not cause additional unlogged errors downstream.

---

### User Story 5 - Narrow Exception Types and Add Binding (Priority: P2)

As a developer maintaining this codebase, I need overly broad `except Exception:` blocks to be narrowed to specific exception types where possible, and all exception blocks to bind the exception variable (`as e`), so that exception handling is precise and debuggable. Currently, 94 occurrences of bare `except Exception:` (without `as e`) exist, many of which could be narrowed to specific types.

**Why this priority**: While broad exception handling doesn't cause immediate failures, it masks unexpected errors and makes debugging harder. Narrowing exceptions and binding variables is a code quality improvement that supports long-term maintainability and complements the critical fixes in Stories 1-4.

**Independent Test**: Can be fully tested by running a static analysis pass across the codebase to verify that (a) no bare `except Exception:` blocks remain without `as e`, (b) high-priority targets are narrowed to specific types, and (c) intentional broad catches are documented with comments.

**Acceptance Scenarios**:

1. **Given** an `except Exception:` block that currently has `pass`, **When** the fix is applied, **Then** the block includes appropriate logging with the exception bound via `as e`.
2. **Given** an `except Exception:` block that has logging but no `as e`, **When** the fix is applied, **Then** `as e` is added and `e` is included in the log message.
3. **Given** an `except Exception:` block where specific exception types can be identified, **When** the fix is applied, **Then** the `except` clause is narrowed to the appropriate specific type(s).
4. **Given** an intentional broad `except Exception:` block (e.g., `CancelledError` during shutdown, `ImportError` for optional modules), **When** the code is reviewed, **Then** a comment is added documenting why the broad catch is intentional, and no other changes are made.

---

### Edge Cases

- What happens when a logging call itself fails (e.g., logger is misconfigured or disk is full)? The system should not crash; logging failures should be handled gracefully by the logging framework.
- What happens when an exception occurs in a tight loop (e.g., client cleanup)? Debug-level logging is appropriate to avoid log flooding.
- What happens when exception text contains user-provided data? Logged exception details must not be sent to end users, but internal logs may contain this data for debugging.
- What happens when narrowing exception types causes a previously-caught exception to propagate? All exception type narrowing must be verified to cover the actual exceptions that can occur in each code path.
- What happens when multiple exceptions occur in rapid succession in the same handler? Each exception should be logged independently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST log all critical silent failures (workflow config fetch, branch OID update, client cleanup, metadata read) with appropriate severity levels and contextual identifiers.
- **FR-002**: System MUST log all database update failures in the agent creator pipeline (issue number, branch name, PR number updates) at error level with agent identifiers.
- **FR-003**: System MUST log owner/repo resolution failures in the agent pipeline at warning level with project identifiers.
- **FR-004**: System MUST log Signal context resolution failures at warning level with project identifiers.
- **FR-005**: System MUST include full exception tracebacks (`exc_info`) in all newly added log statements to support root-cause analysis.
- **FR-006**: System MUST NOT expose raw exception messages, stack traces, file paths, or internal identifiers to end users through Signal messages or any other external-facing channel.
- **FR-007**: System MUST replace all user-facing exception detail messages with generic, friendly error messages that guide the user without revealing internal details.
- **FR-008**: System MUST bind all `except Exception` blocks with `as e` to capture the exception variable, except in specifically documented resilience blocks (e.g., logging utility internals).
- **FR-009**: System MUST narrow overly broad `except Exception` catches to specific exception types where the set of possible exceptions can be determined from the code context.
- **FR-010**: System MUST preserve intentional broad exception catches (e.g., `CancelledError` during shutdown, `ImportError` for optional modules) and document them with inline comments explaining the rationale.
- **FR-011**: System MUST maintain existing error recovery behavior (e.g., fallback to defaults, graceful degradation) while adding logging — no changes to control flow.

### Key Entities

- **Exception Handler**: A try/except block in the codebase; categorized as critical, high, medium, or intentional based on the impact of silent failure.
- **Log Entry**: A structured log message with severity level (debug, warning, error), contextual identifiers (project ID, agent ID, branch name), and optional exception traceback.
- **User-Facing Error Message**: A generic, friendly message sent to end users when an internal error occurs, containing no implementation details.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the 4 critical silent failure locations produce log entries when exceptions occur, with zero exceptions silently discarded.
- **SC-002**: 100% of the 4 high-priority database update failure locations produce error-level log entries when exceptions occur.
- **SC-003**: 0 locations in external-facing message handlers expose raw exception text to end users.
- **SC-004**: All newly added log entries include exception tracebacks (`exc_info`) and contextual identifiers (project ID, agent ID, etc.).
- **SC-005**: Existing error recovery behavior (fallbacks, graceful degradation) remains unchanged after all fixes are applied — no regressions in system behavior.
- **SC-006**: All bare `except Exception:` blocks (without `as e`) that contain `pass` are replaced with logging and exception binding.
- **SC-007**: High-priority exception type narrowing targets are updated to use specific exception types instead of generic `Exception`.
- **SC-008**: All intentional broad exception catches are documented with inline comments.

## Assumptions

- The existing logging infrastructure (Python `logging` module) is properly configured and available in all affected modules.
- Log levels follow standard severity conventions: `debug` for low-impact/expected conditions, `warning` for degraded-but-recoverable states, `error` for failures that may cause data loss or broken functionality.
- The `exc_info=True` parameter is the standard pattern used in this codebase to include exception tracebacks in log messages.
- Signal messaging is the only external-facing channel that currently leaks exception details; other API endpoints are assumed to already handle errors generically.
- The 94 bare `except Exception:` occurrences include both the critical/high/medium targets and many additional locations that should be improved as part of the broader code quality sweep.
- Intentional exception catches identified in the issue (11 locations) are already correct and need only documentation comments, not behavioral changes.
