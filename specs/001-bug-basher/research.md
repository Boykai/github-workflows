# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher
**Date**: 2026-03-22
**Status**: Complete — all unknowns resolved

## Research Tasks

### R1 — Bug-Bash Audit Strategy: Priority-Ordered Category Passes

**Context**: The spec mandates auditing all files across five bug categories in priority order (security → runtime → logic → tests → quality). Need to determine whether to audit file-by-file or category-by-category.

**Decision**: Category-by-category passes, with each pass covering all files for that specific category before moving to the next.

**Rationale**:
- Category-by-category allows using specialized tools per pass (e.g., `bandit` for security, `pyright` for type errors, coverage analysis for test gaps).
- Fixes in higher-priority categories (security, runtime) may affect lower-priority findings — sequential passes avoid rework.
- Each category pass produces a coherent set of commits with clear thematic commit messages.
- Aligns with the spec's priority ordering: P1 categories (security, runtime) are completed first, ensuring the most critical issues are addressed even if time constraints arise.

**Alternatives Considered**:
1. **File-by-file audit**: Rejected — requires context-switching between all five categories per file, increases cognitive load, and makes it harder to use category-specific tooling.
2. **Parallel category passes**: Rejected — fixes in security pass may change code that runtime pass needs to audit, creating merge conflicts and rework.

---

### R2 — Backend Security Scanning Tools

**Context**: The backend uses Python 3.13 with FastAPI. Need to confirm which security tools are already available and how to run them.

**Decision**: Use `bandit -r src/` (already in dev dependencies) for security-focused static analysis, supplemented by manual review for auth/authz logic.

**Rationale**:
- Bandit (≥1.8.0) is already listed in `pyproject.toml` dev dependencies — no new dependency needed.
- Bandit covers common Python security issues: SQL injection, shell injection, hardcoded passwords, insecure crypto, XML vulnerabilities, and more.
- `pip-audit` (≥2.9.0) is also available for dependency vulnerability scanning but is out of scope for code-level bug-bashing.
- Manual review is still needed for business logic security (auth bypasses, authorization checks) that static analysis cannot detect.

**Alternatives Considered**:
1. **Adding Semgrep or CodeQL**: Rejected — adds new dependencies, which violates FR-012.
2. **Bandit only (no manual review)**: Rejected — Bandit cannot detect business logic security flaws like incorrect authorization checks.

---

### R3 — Frontend Security Scanning Approach

**Context**: The frontend uses TypeScript with React and ESLint. Need to confirm available security linting.

**Decision**: Use existing ESLint security plugin (already configured in `eslint.config.js`) plus manual review for XSS, prototype pollution, and unsafe patterns.

**Rationale**:
- `eslint-plugin-security` is already in the frontend devDependencies and configured in `eslint.config.js`.
- ESLint catches common issues: `eval()`, `dangerouslySetInnerHTML`, dynamic `require()`, etc.
- Manual review covers React-specific concerns: unescaped user input in JSX, prototype pollution via `Object.assign`, unsafe `innerHTML` patterns.

**Alternatives Considered**:
1. **Adding additional ESLint plugins**: Rejected — violates FR-012 (no new dependencies).

---

### R4 — Test Regression Strategy: One Test Per Fix

**Context**: FR-004 requires at least one new regression test per bug fix. Need to determine where regression tests go and how to name them.

**Decision**: Add regression tests to the existing test file for the module being fixed. If no test file exists for that module, create one following existing naming conventions (`test_{module_name}.py` for backend, `{Component}.test.tsx` for frontend).

**Rationale**:
- Placing regression tests alongside existing module tests keeps related test logic co-located and easy to discover.
- Following existing naming conventions ensures tests are automatically picked up by pytest/vitest test discovery.
- Each regression test should be clearly named to indicate it's a bug-bash regression test (e.g., `test_fix_null_check_on_empty_response` or descriptive test name indicating the fix).

**Alternatives Considered**:
1. **Separate `tests/regression/` directory**: Rejected — breaks co-location with module tests, adds unnecessary directory structure, and deviates from existing test organization.
2. **No new tests, rely on existing coverage**: Rejected — violates FR-004 which mandates at least one new regression test per fix.

---

### R5 — Ambiguous Issue Flagging: TODO(bug-bash) Format

**Context**: FR-006 requires `TODO(bug-bash)` comments for ambiguous issues. Need to standardize the format.

**Decision**: Use the format `# TODO(bug-bash): {description} | Options: {option1}, {option2} | Reason: {why human decision needed}` for Python, and `// TODO(bug-bash): ...` for TypeScript.

**Rationale**:
- The `TODO(bug-bash)` prefix is machine-searchable (`grep -rn "TODO(bug-bash)"`) for easy discovery during human review.
- Including options and rationale inline ensures context is not lost when the reviewer reads the code.
- Follows the spec's requirement: "describing the issue, the options, and why it needs a human decision."
- The comment should be at the exact line where the issue exists, not in a separate file.

**Alternatives Considered**:
1. **GitHub Issues for each ambiguous item**: Rejected — spec explicitly requires in-code comments, not external tracking.
2. **Separate `AMBIGUOUS.md` document**: Rejected — divorces context from code; developers must cross-reference.

---

### R6 — Commit Strategy for Bug Fixes

**Context**: FR-005 requires clear commit messages explaining what the bug was, why it's a bug, and how the fix resolves it. Need to determine commit granularity.

**Decision**: One commit per logical bug fix (which may span multiple files if the fix + test are tightly coupled). Group by category when filing commits.

**Rationale**:
- One-bug-per-commit ensures each commit message can clearly explain a single issue, satisfying FR-005.
- Related changes (fix + regression test + affected test updates) belong in the same commit since they form one logical unit.
- Category grouping in the commit history makes the summary table easy to generate.

**Alternatives Considered**:
1. **One large commit per category**: Rejected — makes it impossible to write clear per-bug commit messages as required by FR-005.
2. **Separate commits for fix vs. test**: Rejected — creates intermediate states where tests fail, violating FR-009 ("must not commit when tests fail").

---

### R7 — Validation Pipeline: Running All Checks

**Context**: FR-007 and FR-008 require all tests and lint checks to pass. Need to confirm the full validation command sequence.

**Decision**: Run the following validation pipeline after all fixes:

**Backend**:
```bash
cd solune/backend
pip install -e ".[dev]"
pytest --timeout=60
ruff check src tests
pyright src
bandit -r src/
```

**Frontend**:
```bash
cd solune/frontend
npm install
npm run test
npm run lint
npm run type-check
npm run build
```

**Rationale**:
- This sequence covers all existing quality gates: unit tests, linting, type checking, security scanning, and build verification.
- The `--timeout=60` flag prevents hanging tests from blocking the pipeline.
- Running `npm run build` ensures TypeScript compilation and Vite bundling succeed (catches import errors that tests might miss).

**Alternatives Considered**:
1. **Running only `pytest` and `npm run test`**: Rejected — misses lint, type check, and security scan requirements.
2. **Adding E2E tests**: Rejected — E2E tests (Playwright) require a running backend and are out of scope for the bug-bash validation.

---

### R8 — Summary Table Generation

**Context**: FR-010 requires a single summary table at the end. Need to determine format and generation approach.

**Decision**: Generate the summary table manually as part of the final commit, following the format specified in the issue:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description | ⚠️ Flagged (TODO) |
```

**Rationale**:
- The format is explicitly defined in the spec — no design decision needed.
- Manual generation ensures accuracy: each entry is verified against the actual fix.
- The summary is included in the final PR description or commit body.

**Alternatives Considered**:
1. **Auto-generated from commit messages**: Rejected — requires structured commit parsing and may miss `TODO(bug-bash)` items that don't have commits.
2. **Separate `BUGS.md` file**: Rejected — spec says "single summary comment", not a file.
