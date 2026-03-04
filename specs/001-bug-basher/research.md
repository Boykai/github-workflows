# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-04

## Research Tasks

### R1: Bug Bash Methodology for Python/FastAPI + React/TypeScript Codebases

**Decision**: Audit files in priority order by bug category (Security → Runtime → Logic → Test Quality → Code Quality), processing backend before frontend within each category since the backend handles authentication, data persistence, and API security.

**Rationale**: Security vulnerabilities in the backend (auth bypasses, injection, exposed secrets) have the highest blast radius. Addressing them first prevents compound risk where a logic bug in an authenticated endpoint becomes an exploit. Processing categories in priority order matches spec FR-001 and the five user stories (P1–P5).

**Alternatives considered**:
- File-by-file sequential audit: Rejected because it mixes priorities and makes it harder to track category-specific patterns across modules.
- Random sampling with coverage targets: Rejected because the spec requires 100% file review (SC-001).

---

### R2: Existing Codebase Patterns for Error Handling

**Decision**: Follow the established `handle_service_error()` / `safe_error_response()` pattern from `logging_utils.py`. API error responses must use static messages with server-side `exc_info=True` logging. Never expose `str(e)` in responses.

**Rationale**: The codebase already has a centralized error handling pattern. Bug fixes that touch error paths must conform to this existing convention to satisfy FR-012 (preserve existing code style). Multiple API modules (board.py, chat.py, workflow.py, cleanup.py) already follow this pattern.

**Alternatives considered**:
- Introducing a new error handling middleware: Rejected — violates FR-011 (no architecture changes) and FR-013 (minimal fixes).

---

### R3: Testing Patterns and Regression Test Strategy

**Decision**: Backend regression tests go in the existing `backend/tests/unit/` directory, following the `test_{module_name}.py` convention. Each test uses pytest with `pytest-asyncio` for async code. Frontend tests use Vitest with `@testing-library/react`. Each bug fix gets at least one targeted regression test that would fail if the bug reoccurred.

**Rationale**: The codebase has well-established test patterns with 1200+ backend tests and 277+ frontend tests. Following existing conventions (fixture patterns from `conftest.py`, mock patterns from `helpers/mocks.py`, factory patterns from `helpers/factories.py`) satisfies FR-012 and reduces review friction.

**Alternatives considered**:
- Creating a separate `tests/regression/` directory: Rejected — deviates from existing structure and makes it harder to run related tests together.
- Integration-level regression tests only: Rejected — unit tests are faster and more targeted; the spec requires per-bug validation (FR-004).

---

### R4: Backend Security Audit Scope

**Decision**: Focus security audit on: (1) API route handlers in `backend/src/api/` for auth bypasses and input validation, (2) `config.py` and `.env.example` for exposed secrets/insecure defaults, (3) `services/encryption.py` and `services/github_auth.py` for cryptographic issues, (4) `services/database.py` and `services/session_store.py` for injection risks, (5) `middleware/` for missing security headers.

**Rationale**: These modules handle external input, authentication, secrets management, and data persistence — the primary attack surfaces in a web application. The FastAPI framework provides some built-in protections (Pydantic validation, CORS middleware) but custom logic in these modules can introduce vulnerabilities.

**Alternatives considered**:
- Automated SAST-only approach: Rejected — automated tools miss logic-level auth bypasses and context-specific issues that manual review catches.

---

### R5: Frontend Security and Quality Audit Scope

**Decision**: Focus frontend audit on: (1) `services/` for API call security (token handling, error exposure), (2) `hooks/` for state management bugs (race conditions, stale closures), (3) `components/` for XSS risks (dangerouslySetInnerHTML, unsanitized rendering), (4) `types/` for type safety gaps.

**Rationale**: Frontend security issues primarily involve token leakage, XSS, and insecure API interactions. React's JSX escaping provides baseline XSS protection, but explicit HTML rendering or URL construction can bypass it. State management bugs in hooks cause runtime errors and incorrect UI behavior.

**Alternatives considered**:
- Skip frontend security audit: Rejected — the spec requires auditing every file (SC-001), and frontend token handling is a valid security concern.

---

### R6: Linting and Validation Toolchain

**Decision**: Use existing toolchain for validation: Backend: `ruff check src tests && ruff format --check src tests` for lint/format, `timeout 30 python -m pytest tests/unit/test_X.py -q` per file for tests. Frontend: `npx eslint .` for lint, `npx tsc --noEmit` for type-check, `npx vitest run` for tests.

**Rationale**: These tools are already configured in the repository (`pyproject.toml` for Ruff/pytest, `eslint.config.js` for ESLint, `package.json` scripts for Vitest/TypeScript). Using existing configuration satisfies FR-008 and ensures consistent baselines. Running backend tests individually prevents hanging (known issue from repository memory).

**Alternatives considered**:
- Adding additional analysis tools (e.g., Bandit, Semgrep): Rejected — violates FR-011 (no new dependencies).

---

### R7: Ambiguity Handling and TODO Convention

**Decision**: Use `# TODO(bug-bash): <description>` format for Python and `// TODO(bug-bash): <description>` for TypeScript. Each TODO must include: (1) what the issue is, (2) the options considered, (3) why it needs human decision. Ambiguous issues include: design trade-offs, API surface changes, dependency additions, and architectural changes.

**Rationale**: The spec explicitly defines this format (FR-006) and the conditions under which it applies. Consistent formatting enables grep-based discovery of all flagged items after the bug bash.

**Alternatives considered**:
- Using GitHub issue comments instead of inline TODOs: Rejected — the spec requires in-code comments (FR-006).

---

### R8: Commit and Validation Strategy

**Decision**: Group fixes by category and module. Each commit addresses one logical bug with a message format: `fix(<category>): <what was wrong> in <file> — <how fixed>`. Run the full test suite (backend + frontend) after each category sweep to ensure no regressions.

**Rationale**: Atomic commits per bug satisfy FR-005 (clear commit messages) and SC-008 (each fix independently verifiable). Category-based grouping makes the review process systematic and the summary table easier to produce.

**Alternatives considered**:
- Single mega-commit: Rejected — impossible to independently verify fixes (violates SC-008).
- File-by-file commits: Rejected — a single bug may span multiple files; logical grouping is more meaningful.
