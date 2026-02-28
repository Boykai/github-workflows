# Quickstart: Deep Security Review Implementation

**Feature**: 012-deep-security-review
**Date**: 2026-02-28

## Prerequisites

- Python 3.11+ with pip
- Node.js 20+ with npm
- Docker & Docker Compose
- Access to the repository on branch `012-deep-security-review`

## Getting Started

### 1. Environment Setup

```bash
# Clone and checkout the feature branch
cd /path/to/github-workflows

# Copy environment template and configure secrets
cp .env.example .env

# REQUIRED: Generate and set encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy the output into .env as ENCRYPTION_KEY=<generated_key>

# REQUIRED: Set a strong session secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output into .env as SESSION_SECRET_KEY=<generated_secret>
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -e ".[dev]"

# Run security audit on dependencies
pip-audit

# Run existing tests to establish baseline
pytest

# Run linting
ruff check src/
ruff format --check src/
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run security audit on dependencies
npm audit --audit-level=high

# Run existing tests to establish baseline
npm run test

# Run linting
npm run lint
```

### 4. Security Review Workflow

The implementation follows this order based on user story priorities:

#### Phase 1: Critical Fixes (P1 Stories 1-3)

1. **Encryption enforcement** — Make token encryption mandatory
   - File: `backend/src/services/encryption.py`
   - Verify: Startup fails without `ENCRYPTION_KEY` when `DEBUG=false`

2. **GitHub Actions hardening** — Pin actions to SHA commits
   - File: `.github/workflows/ci.yml`
   - Verify: `grep -c '@[a-f0-9]\{40\}' .github/workflows/ci.yml` shows all actions pinned

3. **CORS tightening** — Replace wildcard with explicit lists
   - File: `backend/src/main.py`
   - Verify: Response headers show restricted CORS policy

4. **Security headers middleware** — Add HTTP security headers
   - File: `backend/src/middleware/security_headers.py` (new)
   - Verify: `curl -I http://localhost:8000/health` shows all required headers

5. **Secrets scan** — Verify no hardcoded secrets
   - Tool: `grep -rn 'password\|secret\|api_key\|token' --include='*.py' --include='*.ts' --include='*.yml' .`
   - Verify: Only references to environment variables, no actual values

#### Phase 2: High-Priority Enhancements (P2 Stories 4-5)

6. **Dependency audit** — Scan and remediate vulnerable packages
   - Tools: `pip-audit`, `npm audit`
   - Verify: Zero critical/high findings

7. **Rate limiting** — Add rate limiting middleware
   - File: `backend/src/middleware/rate_limit.py` (new)
   - Verify: Auth endpoints return 429 after 10 rapid requests

8. **Security logic consolidation** — Create shared utilities
   - Directory: `backend/src/services/security/` (new)
   - Verify: All shared utilities have passing tests

#### Phase 3: Documentation (P3 Story 6)

9. **Security review report** — Document all findings and actions
   - Output: Security review report with severity classifications

### 5. Verification

```bash
# Run all backend tests including new security tests
cd backend && pytest -v

# Run all frontend tests
cd frontend && npm run test

# Run full CI pipeline locally (optional)
cd .. && docker compose build
docker compose up -d
# Verify health: curl http://localhost:8000/health

# Check security headers
curl -I http://localhost:8000/health

# Verify CORS policy
curl -I -H "Origin: http://malicious-site.com" http://localhost:8000/health
```

### 6. Key Files Reference

| File | Purpose |
|------|---------|
| `backend/src/main.py` | CORS config, middleware registration |
| `backend/src/services/encryption.py` | Token encryption (enforce mandatory) |
| `backend/src/middleware/security_headers.py` | HTTP security headers (new) |
| `backend/src/middleware/rate_limit.py` | Rate limiting (new) |
| `backend/src/services/security/` | Shared security utilities (new) |
| `backend/src/dependencies.py` | Auth dependencies, admin checks |
| `backend/src/api/auth.py` | OAuth endpoints, dev-login guard |
| `backend/src/api/webhooks.py` | Webhook verification |
| `.github/workflows/ci.yml` | CI pipeline (pin actions) |
| `backend/tests/test_security/` | Security utility tests (new) |
