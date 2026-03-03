# Research: Bug Bash — Full Codebase Review & Fix

## R1: Audit Scope and File Inventory

**Decision**: Audit all ~342 source files across backend (Python), frontend (TypeScript/React), SQL migrations, GitHub workflows, Docker configuration, and shell scripts. Exclude auto-generated files (`package-lock.json`, `__pycache__`, build artifacts) and vendored third-party code.

**Rationale**: The spec requires "every file in the repository on `main`" to be audited. The file inventory is approximately: ~87 backend Python source files, ~55 backend test files, ~122 frontend TypeScript/TSX files, 9 E2E test files, 9 SQL migrations, 3 GitHub workflows, 2 shell scripts, 3 Docker files, and ~52 configuration files. Counts are approximate as they depend on how `__init__.py`, type stubs, and minor config files are counted. Auto-generated files (lockfiles, compiled output) provide no meaningful audit surface — bugs in those files originate from their source.

**Alternatives considered**:
- Audit only backend or frontend: Rejected — the spec explicitly requires "entire codebase."
- Include `package-lock.json` and `node_modules`: Rejected — these are generated artifacts; dependency vulnerabilities are checked via tooling, not manual review.

---

## R2: Audit Tool Strategy — Static Analysis + Manual Review

**Decision**: Use existing configured tools (Ruff, Pyright, ESLint, TypeScript compiler) as the first-pass automated scan, then perform targeted manual review for each bug category. No new tools will be introduced.

**Rationale**: The project already has Ruff (Python linting + formatting), Pyright (Python type checking), ESLint (TypeScript linting), and TypeScript strict mode configured. These tools catch a large class of issues automatically (unused imports, type errors, formatting violations). Manual review is required for security vulnerabilities, logic bugs, and test quality issues that static analysis cannot detect. The spec prohibits introducing new dependencies.

**Alternatives considered**:
- Add Bandit (Python security scanner): Rejected — spec says "no new third-party dependencies." Bandit is a dev dependency but adding it changes the project's tooling configuration.
- Add SonarQube or Semgrep: Rejected — same constraint; also requires infrastructure setup.
- Skip automated tools and only do manual review: Rejected — wasteful when existing tools can catch low-hanging fruit.

---

## R3: Bug Category Priority Execution Order

**Decision**: Execute the audit in strict priority order: Security (P1) → Runtime Errors (P1) → Logic Bugs (P2) → Test Gaps (P2) → Code Quality (P3). Within each category, audit backend first, then frontend, then infrastructure (Docker, workflows, scripts).

**Rationale**: The spec mandates this priority order (FR-010). Security and runtime errors are P1 because they pose the highest risk to users. Within each priority tier, backend-first ordering makes sense because the backend handles authentication, data access, and business logic — the highest-risk surface. Frontend issues are typically lower severity (XSS is the main security concern). Infrastructure files (Docker, CI) are audited last within each category.

**Alternatives considered**:
- File-by-file sequential audit (audit one file completely across all categories before moving on): Rejected — makes it harder to maintain consistent severity assessment across the codebase. Category-first ensures apples-to-apples comparison.
- Parallel audit of all categories: Rejected — fixing a security bug might reveal a logic bug; sequential ordering allows cascading discovery.

---

## R4: Fix Isolation and Commit Strategy

**Decision**: Each bug fix is a single isolated commit with the format: `fix(<category>): <what was fixed> in <file>`. Each commit includes the minimal code fix plus at least one regression test. No bundled changes.

**Rationale**: The spec requires "each fix must be minimal and focused; no drive-by refactors" and "descriptive commit messages (what/why/how)." Isolated commits enable easy reversal if a fix introduces regressions, and descriptive messages create a traceable audit trail.

**Alternatives considered**:
- Batch fixes by file: Rejected — violates the "one bug per commit" requirement and makes reversal harder.
- Batch fixes by category: Rejected — same issue; a single bad fix would require reverting the entire category.

---

## R5: Ambiguous Issue Documentation Pattern

**Decision**: Use the `# TODO(bug-bash):` comment format directly at the code location. The comment must include: (1) description of the issue, (2) available options for resolution, (3) why a human decision is needed. Use a structured format for machine-parseability.

**Rationale**: The spec explicitly requires `TODO(bug-bash)` comments (FR-004). Placing them at the code location rather than in a separate file ensures they are visible during normal development and can be found with simple grep. The structured format enables automated extraction for the summary report.

**Pattern**:
```python
# TODO(bug-bash): <Issue Category> — <Brief description>
# Options: (a) <option 1>  (b) <option 2>
# Needs human decision because: <rationale>
```

**Alternatives considered**:
- Separate `FINDINGS.md` file: Rejected — the spec requires comments at the code location, and a separate file would diverge from code over time.
- GitHub issue per ambiguous finding: Rejected — the spec says to use inline comments; issues are a separate tracking concern.

---

## R6: Testing Strategy for Bug Fixes

**Decision**: Use the existing test infrastructure — pytest with asyncio for backend, Vitest with happy-dom for frontend. Each regression test targets the specific bug: set up the conditions that triggered the bug, verify the fix produces correct behavior, and (where possible) verify the old behavior was incorrect.

**Rationale**: The project has ~55 backend test files and ~29 frontend test files with established patterns (factories, mock API, render helpers). Adding regression tests within the existing framework ensures consistency and avoids infrastructure changes. The spec requires "at least one regression test per bug" (FR-003).

**Backend test commands**:
```bash
cd backend && pytest -v                    # Full suite
cd backend && ruff check src tests         # Lint
cd backend && ruff format --check src tests # Format check
cd backend && pyright                       # Type check
```

**Frontend test commands**:
```bash
cd frontend && npm test                    # Full suite
cd frontend && npm run lint                # ESLint
cd frontend && npm run type-check          # TypeScript check
```

**Alternatives considered**:
- Add property-based testing (Hypothesis): Rejected — new dependency.
- Add mutation testing: Rejected — new dependency and significant runtime cost.

---

## R7: Security Audit Focus Areas

**Decision**: Focus security review on: (1) authentication/session management (`backend/src/api/auth.py`, `backend/src/dependencies.py`), (2) input validation in API endpoints (`backend/src/api/`), (3) token/secret handling (`backend/src/config.py`, environment variables), (4) SQL injection risks (raw queries in `backend/src/services/`), (5) XSS risks in frontend (user-generated content rendering), (6) CORS and cookie configuration.

**Rationale**: These are the standard OWASP Top 10 categories applied to this specific tech stack (FastAPI + React + SQLite). The backend handles OAuth tokens, session cookies, and direct SQL queries — all high-risk surfaces. The frontend renders user-provided content (issue titles, chat messages) which could contain XSS payloads.

**Key files for security review**:
- `backend/src/api/auth.py` — OAuth flow, session cookies, token handling
- `backend/src/dependencies.py` — Admin authorization, session validation
- `backend/src/config.py` — Secret management, environment variables
- `backend/src/services/github_projects/service.py` — GitHub API calls, token usage
- `backend/src/services/database.py` — SQL query construction
- `backend/src/api/chat.py` — User input handling
- `frontend/src/services/api.ts` — API client, credential handling

---

## R8: Runtime Error Audit Focus Areas

**Decision**: Focus runtime error review on: (1) async exception handling in FastAPI routes and background tasks, (2) SQLite connection/transaction management, (3) null/None reference patterns in service layer, (4) missing import detection via type checker, (5) resource leaks in file/connection handling, (6) WebSocket lifecycle management.

**Rationale**: The backend uses async Python extensively (asyncio, aiosqlite), which has unique error-handling patterns. Unhandled exceptions in async contexts can silently fail or crash the event loop. SQLite connections via aiosqlite need proper cleanup. The frontend uses WebSocket connections (Socket.io) and React Query, both of which have lifecycle management concerns.

**Key patterns to check**:
- `async with` for database connections (proper cleanup on exception)
- `try/except` around external API calls (GitHub API, AI providers)
- Null checks before attribute access on optional types
- WebSocket reconnection and cleanup in frontend hooks

---

## R9: Summary Report Format

**Decision**: Generate a markdown summary table with columns: File, Line(s), Category, Description, Status. Group findings by category. Include counts per category and an overall status (all tests passing or not).

**Rationale**: The spec requires a "summary table listing every finding with file, line(s), category, description, and status" (FR-009). Markdown format is consistent with all other project artifacts. Grouping by category enables quick triage by priority.

**Table format**:
```markdown
| File | Line(s) | Category | Description | Status |
|------|---------|----------|-------------|--------|
| `backend/src/api/auth.py` | 42-45 | 🔴 Security | Unvalidated redirect URL | ✅ Fixed |
| `backend/src/main.py` | 100 | 🟡 Logic | Off-by-one in pagination | ⚠️ Flagged |
```

**Alternatives considered**:
- JSON report: Rejected — less readable for humans; markdown is the project standard.
- CSV export: Rejected — same readability concern; markdown tables render nicely in GitHub.

---

## R10: Backend vs. Frontend Audit Depth

**Decision**: Allocate approximately 60% of audit effort to backend, 30% to frontend, and 10% to infrastructure. Backend receives more attention because it handles security-critical operations (auth, data access, API surface). Frontend is audited with emphasis on XSS, state management, and error boundary coverage.

**Rationale**: The backend has 87 source files handling authentication, database operations, GitHub API integration, AI agent execution, and WebSocket communication — all high-risk areas. The frontend has 122 files but primarily renders UI with well-established patterns (React Query for data fetching, controlled components for forms). Infrastructure files (Docker, CI) are small in number and typically have fewer subtle bugs.

**Alternatives considered**:
- Equal time across all areas: Rejected — not all code carries equal risk. A SQL injection in the backend is far more severe than a CSS misalignment in the frontend.
- Backend-only audit: Rejected — the spec requires "entire codebase" coverage.
