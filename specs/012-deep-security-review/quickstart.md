# Quickstart: Deep Security Review and Application Hardening

**Feature**: `012-deep-security-review`
**Date**: 2026-02-28

## Prerequisites

- Docker and Docker Compose installed
- Existing backend and frontend running (see root `README.md`)
- Python 3.11+ with pip (for backend dependency audit)
- Node.js 20+ with npm (for frontend dependency audit)

## 1. Verify GitHub Workflow Hardening

After the security changes are applied, verify the CI workflow:

```bash
# Check that all actions use full SHA pinning
grep -E 'uses:.*@' .github/workflows/ci.yml

# Each action should show a 40-character SHA, not a version tag
# GOOD: uses: actions/checkout@a5ac7e51b41094c7423fa4fb984512f522bbbc51
# BAD:  uses: actions/checkout@v4
```

Verify that permissions are explicitly set:

```bash
# Check for permissions blocks in the workflow
grep -A2 'permissions:' .github/workflows/ci.yml

# Should show explicit permissions like:
# permissions:
#   contents: read
```

## 2. Verify Error Message Sanitization

Test that API error responses don't leak internal details:

```bash
# Start the backend
cd backend && pip install -e ".[dev]"

# Test OAuth callback with invalid state (should return generic error)
curl -s http://localhost:8000/api/v1/auth/callback?code=invalid&state=invalid | python -m json.tool
# Expected: {"detail": "Invalid or expired OAuth state"}
# NOT expected: {"detail": "KeyError: 'invalid'"}
```

## 3. Run Dependency Audits

### Backend (Python)

```bash
cd backend
pip install pip-audit
pip-audit

# Should report zero critical/high severity vulnerabilities
```

### Frontend (npm)

```bash
cd frontend
npm audit

# Should report zero critical/high severity vulnerabilities
```

## 4. Run Existing Tests

Verify that all security changes maintain backward compatibility:

```bash
# Backend linting and type checking
cd backend
ruff check src tests
ruff format --check src tests
pyright src

# Frontend linting, type checking, and tests
cd frontend
npm run lint
npm run type-check
npm test
npm run build
```

## 5. Secrets Scan

Verify no hardcoded secrets exist:

```bash
# Search for common secret patterns (should return only placeholder/config references)
grep -rn "password\|secret\|api_key\|token" --include="*.py" --include="*.ts" --include="*.yml" --include="*.yaml" . \
  | grep -v node_modules | grep -v __pycache__ | grep -v ".git/"

# Verify .env is gitignored
git status .env  # Should show nothing (not tracked)
```

## 6. Review Security Findings Report

After the review is complete, a security findings report will be available at:

```
specs/012-deep-security-review/security-findings-report.md
```

This report documents:
- All vulnerabilities found (with severity ratings)
- Fixes applied (with verification)
- Accepted risks (with justification)

## Key Files Modified

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | SHA-pinned actions, added permissions blocks |
| `backend/src/api/auth.py` | Sanitized error messages in OAuth and dev-login |
| `backend/pyproject.toml` | Updated vulnerable dependencies (if any found) |
| `frontend/package.json` | Updated vulnerable dependencies (if any found) |

## Architecture Overview

This is a security hardening feature — no architectural changes. The existing structure remains:

```
┌─────────────┐    REST API    ┌─────────────┐
│   Backend   │ ◄────────────► │  Frontend   │
│  (FastAPI)  │                │  (React)    │
└──────┬──────┘                └─────────────┘
       │
       │ SQLite
       ▼
┌─────────────┐
│  Database   │
│  (aiosqlite)│
└─────────────┘
```

Security hardening touches all layers:
- **CI/CD**: GitHub Actions workflow hardening
- **Backend**: Error message sanitization, dependency updates
- **Frontend**: Dependency updates
- **Configuration**: Secrets management verification
