# Feature Specification: Startup Config Validation for AI Provider, Azure OpenAI, and Database Path

**Feature Branch**: `001-startup-config-validation`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Add Startup Config Validation for AI Provider, Azure OpenAI Completeness, and Database Path"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject Unknown AI Provider at Startup (Priority: P1)

As a backend engineer deploying the application, I want the system to immediately reject any unrecognized AI provider value at boot time so that I receive a clear, actionable error message instead of encountering cryptic failures later at runtime.

**Why this priority**: An unknown AI provider renders all AI features non-functional. Catching this universally (in both debug and production modes) prevents the application from entering a state where core functionality silently fails, making it the highest-impact validation.

**Independent Test**: Can be fully tested by providing an invalid `ai_provider` value (e.g., "openai") and verifying that the application refuses to start with an error message that names the invalid value and lists the valid options.

**Acceptance Scenarios**:

1. **Given** the configuration contains `ai_provider` set to an unrecognized value (e.g., "openai"), **When** the application starts in production mode, **Then** a fatal error is raised immediately with a message stating what value is invalid and listing the accepted values ("copilot", "azure_openai").
2. **Given** the configuration contains `ai_provider` set to an unrecognized value, **When** the application starts in debug mode, **Then** the same fatal error is raised (this check is mode-independent).
3. **Given** the configuration contains `ai_provider` set to "copilot", **When** the application starts, **Then** no AI provider validation error occurs.
4. **Given** the configuration contains `ai_provider` set to "azure_openai", **When** the application starts, **Then** no AI provider validation error occurs.

---

### User Story 2 - Validate Azure OpenAI Credential Completeness (Priority: P2)

As a backend engineer configuring Azure OpenAI as the AI provider, I want the system to verify that both the endpoint and key are provided so that incomplete Azure OpenAI configurations are caught before any AI requests are attempted.

**Why this priority**: When Azure OpenAI is selected but credentials are incomplete, all AI-powered features fail. Validating completeness at startup prevents delayed failures when users first try to use AI features, reducing troubleshooting time.

**Independent Test**: Can be fully tested by setting `ai_provider` to "azure_openai" with one or both credentials missing and verifying the appropriate error (production) or warning (debug) is produced.

**Acceptance Scenarios**:

1. **Given** `ai_provider` is "azure_openai" and `azure_openai_endpoint` is missing, **When** the application starts in production mode, **Then** an error is accumulated indicating the missing endpoint and how to set it.
2. **Given** `ai_provider` is "azure_openai" and `azure_openai_key` is missing, **When** the application starts in production mode, **Then** an error is accumulated indicating the missing key and how to set it.
3. **Given** `ai_provider` is "azure_openai" and both `azure_openai_endpoint` and `azure_openai_key` are provided, **When** the application starts in production mode, **Then** no Azure OpenAI credential errors occur.
4. **Given** `ai_provider` is "azure_openai" and credentials are missing, **When** the application starts in debug mode, **Then** a warning is logged indicating AI features will not work, but the application continues to start without a fatal error.

---

### User Story 3 - Validate Database Path in Production (Priority: P3)

As a backend engineer deploying the application to production, I want the system to reject empty or non-absolute database paths so that the database is always stored at a predictable, absolute location in production environments.

**Why this priority**: A misconfigured database path in production can lead to data being written to unexpected locations or initialization failures. While less critical than AI provider validation (as the database layer has its own error handling for directory creation), catching path issues early prevents hard-to-diagnose data storage problems.

**Independent Test**: Can be fully tested by providing an empty or relative database path in production mode and verifying an error is produced, or providing a valid absolute path and verifying acceptance.

**Acceptance Scenarios**:

1. **Given** `database_path` is an empty string, **When** the application starts in production mode, **Then** an error is accumulated indicating the path is empty and how to set a valid absolute path.
2. **Given** `database_path` is a relative path (e.g., "data/settings.db") and is not ":memory:", **When** the application starts in production mode, **Then** an error is accumulated indicating that the path must be absolute.
3. **Given** `database_path` is a valid absolute path (e.g., "/var/lib/solune/data/settings.db"), **When** the application starts in production mode, **Then** no database path errors occur.
4. **Given** `database_path` is a relative path, **When** the application starts in debug mode, **Then** no database path error is raised, allowing flexible paths for test environments.
5. **Given** `database_path` is ":memory:", **When** the application starts in production mode, **Then** no database path error is raised for path absoluteness (":memory:" is a recognized special value).

---

### Edge Cases

- What happens when `ai_provider` is set to an empty string? It should be rejected as an unknown provider since it is not in the accepted set.
- What happens when `ai_provider` has correct value but with different casing (e.g., "Copilot", "AZURE_OPENAI")? It should be rejected since validation is case-sensitive against the exact accepted values.
- What happens when `ai_provider` is "copilot" and Azure OpenAI credentials are provided? No error should occur — the Azure OpenAI credential check only applies when the provider is "azure_openai".
- What happens when `database_path` contains only whitespace? It should be treated as effectively empty and rejected in production mode.
- What happens when both `azure_openai_endpoint` and `azure_openai_key` are missing? Both missing fields should be reported, following the error-accumulation pattern.
- The system must not perform directory existence checks for `database_path`, since the database initialization layer already handles directory creation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST reject any `ai_provider` value not in the accepted set ("copilot", "azure_openai") with a fatal error that is raised before the debug/production mode split, making it fatal in both modes. The error message MUST state the invalid value and list the accepted options.
- **FR-002**: System MUST accumulate an error in production mode when `ai_provider` is "azure_openai" and `azure_openai_endpoint` is missing or empty, following the existing error-accumulation pattern.
- **FR-003**: System MUST accumulate an error in production mode when `ai_provider` is "azure_openai" and `azure_openai_key` is missing or empty, following the existing error-accumulation pattern.
- **FR-004**: System SHOULD log a warning in debug mode when `ai_provider` is "azure_openai" and either `azure_openai_endpoint` or `azure_openai_key` is missing, indicating that AI features will not function.
- **FR-005**: System MUST accumulate an error in production mode if `database_path` is empty.
- **FR-006**: System MUST accumulate an error in production mode if `database_path` is not ":memory:" and is not an absolute path.
- **FR-007**: System MUST NOT enforce database path absoluteness in debug mode, allowing ":memory:" and relative paths to support test environments.
- **FR-008**: System MUST NOT perform directory existence checks for `database_path`, as the database initialization layer already handles directory creation.
- **FR-009**: Every error message MUST include two components: (1) what is wrong, and (2) how to fix it.
- **FR-010**: System MUST include automated tests covering all validation scenarios: unknown provider rejection, valid provider acceptance ("copilot" and "azure_openai"), Azure OpenAI missing credential errors in production, Azure OpenAI missing credential warnings in debug, empty/relative database path rejection in production, absolute database path acceptance, and relative path allowance in debug.

### Key Entities

- **AI Provider**: The configured AI backend for the application. Accepted values are "copilot" and "azure_openai". Determines which AI integration credentials are required.
- **Azure OpenAI Credentials**: A pair of values (endpoint URL and API key) required when the AI provider is set to "azure_openai". Both must be present for the AI integration to function.
- **Database Path**: The filesystem path where the application stores its persistent database. Must be an absolute path in production, but may be relative or ":memory:" in debug/test environments.

## Assumptions

- The accepted set of AI provider values is limited to "copilot" and "azure_openai" and is not expected to change frequently.
- Validation is case-sensitive — "Copilot" or "AZURE_OPENAI" are not accepted alternatives.
- The ":memory:" database path is a recognized special value that bypasses absoluteness checks in all modes.
- The existing error-accumulation pattern in the production validation block collects all errors and raises a single combined error at the end, rather than failing on the first error found.
- Debug mode is designed for development and testing environments where relaxed validation improves developer ergonomics.
- All new validations fit within the existing startup configuration validation flow — no new validation steps or configuration fields are needed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of deployments with an unknown AI provider value fail immediately at startup with an actionable error message, rather than entering a broken state.
- **SC-002**: 100% of production deployments with incomplete Azure OpenAI credentials (missing endpoint or key) are blocked at startup with a clear error identifying the missing field.
- **SC-003**: 100% of production deployments with an empty or non-absolute database path are blocked at startup with an actionable error message.
- **SC-004**: Debug-mode startup with incomplete Azure OpenAI credentials produces a visible warning but does not prevent the application from starting, preserving developer workflow.
- **SC-005**: Debug-mode startup with relative or ":memory:" database paths succeeds without errors, supporting test environments.
- **SC-006**: All new validation scenarios have corresponding automated tests that pass, covering both positive (valid config accepted) and negative (invalid config rejected) cases.
- **SC-007**: All existing configuration tests continue to pass without modification, confirming no regression in existing validation behavior.
