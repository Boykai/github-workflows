# Review Process Contract: Bug Basher

**Feature**: 001-bug-basher | **Date**: 2026-03-22

> This feature does not introduce new API endpoints or modify existing ones (FR-002: no public API surface changes). This contract defines the review process interface — the inputs, outputs, and rules that govern the bug bash workflow.

## Process Interface

### Input: Repository Files

All files under `solune/backend/src/` and `solune/frontend/src/` are review targets. Files are processed in dependency order within each bug category phase.

**Inclusion criteria**:
- All `.py` files in `solune/backend/src/`
- All `.ts` and `.tsx` files in `solune/frontend/src/`
- All test files in `solune/backend/tests/` and `solune/frontend/src/**/*.test.{ts,tsx}`
- Configuration files: `pyproject.toml`, `package.json`, `docker-compose.yml`
- Migration files: `solune/backend/src/migrations/*.sql`

**Exclusion criteria**:
- Generated files (build output, coverage reports)
- `.git/` directory
- `node_modules/`, `__pycache__/`, `.venv/`
- `.specify/` (specification tooling, not production code)
- `.github/` (CI/CD configuration — unless a security issue is found in workflow files)

### Output: Summary Report

Format (FR-011):

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
```

**Column contracts**:
- `#`: Sequential integer starting at 1
- `File`: Relative path from repository root (backtick-wrapped)
- `Line(s)`: Single line number or range (e.g., "42" or "42-45")
- `Category`: One of: Security, Runtime, Logic, Test Quality, Code Quality
- `Description`: Concise description of the finding
- `Status`: Either `✅ Fixed` or `⚠️ Flagged (TODO)`

### Output: Code Changes

**Fix contract** (for ✅ Fixed findings):
- Source file modified with minimal, focused change
- At least one regression test added in the appropriate test directory
- Test follows existing naming conventions and test patterns
- Commit message follows format: `fix(<category>): <description>`

**Flag contract** (for ⚠️ Flagged findings):
- `# TODO(bug-bash): <description>` comment added at the relevant code location
- Comment includes: issue description, available options, rationale for deferral
- No source code changes beyond the comment
- No test added (ambiguous issue, not confirmed bug)

## Validation Contract

After each category phase completes, the following must pass:

### Backend Validation

```bash
cd solune/backend
ruff check src tests          # Exit code 0
ruff format --check src tests # Exit code 0
pytest --timeout=60           # All tests pass (exit code 0)
```

### Frontend Validation

```bash
cd solune/frontend
npm run lint                  # Exit code 0
npm run type-check            # Exit code 0
npm run test                  # All tests pass (exit code 0)
```

### Final Validation (after all phases)

All of the above plus:

```bash
cd solune/backend
bandit -r src/                # Security scan passes
pyright src                   # Type checking passes

cd solune/frontend
npm run build                 # Production build succeeds
```

## Constraints Contract

| Constraint | Source | Enforcement |
|------------|--------|-------------|
| No new dependencies | FR-008 | `pyproject.toml` and `package.json` must have identical dependency lists before and after |
| No API surface changes | FR-002 | No changes to route decorators, endpoint signatures, or response models |
| No architecture changes | Constraints | No new modules, no moved files, no renamed exports |
| Minimal focused fixes | FR-010 | Each diff must relate directly to the identified bug |
| Preserve code style | FR-009 | `ruff format` and `eslint` must pass without new config changes |
| Full test suite passes | FR-005 | `pytest` and `vitest` exit code 0 |
