# Quickstart: Solune v0.1.0 Public Release

**Branch**: `050-solune-v010-release` | **Date**: 2026-03-17 | **Plan**: [plan.md](./plan.md)

## Overview

This quickstart guide provides the essential commands and workflows for developing, testing, and deploying the Solune v0.1.0 release. It covers local development setup, running the test suite, building Docker images, and verifying the release.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ (3.13 recommended) | Backend runtime |
| Node.js | 20+ (22 recommended) | Frontend build and dev |
| npm | 10+ | Frontend package manager |
| Docker | 24+ | Container builds |
| Docker Compose | v2+ | Multi-service orchestration |
| Git | 2.40+ | Version control |

---

## Local Development Setup

### 1. Backend Setup

```bash
cd solune/backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies (including dev tools)
pip install -e ".[dev]"

# Copy environment configuration
cp ../.env.example ../.env
# Edit ../.env with your GitHub OAuth credentials

# Run database migrations (automatic on first startup)
# Migrations are in src/migrations/ and run by the backend on startup via init_database()

# Start the backend development server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
cd solune/frontend

# Install dependencies
npm ci

# Start the development server (proxies /api to backend on port 8000)
npm run dev
# Open http://localhost:5173
```

### 3. Signal API (Optional)

```bash
# Only needed for Signal integration testing
docker run -d --name solune-signal-api \
  -p 8080:8080 \
  bbernhard/signal-cli-rest-api:0.83
```

---

## Running Tests

### Backend Tests

```bash
cd solune/backend

# Run unit tests with coverage
pytest --cov=src --cov-report=term-missing --durations=20

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/property/ --timeout=120  # Property-based tests (Hypothesis)
pytest tests/fuzz/ --timeout=120      # Fuzz tests
pytest tests/chaos/ --timeout=120     # Chaos tests
pytest tests/concurrency/ --timeout=120  # Concurrency tests

# Run mutation testing (by shard)
python scripts/run_mutmut_shard.py --shard auth-and-projects
python scripts/run_mutmut_shard.py --shard orchestration
python scripts/run_mutmut_shard.py --shard app-and-data
python scripts/run_mutmut_shard.py --shard agents-and-integrations
```

### Backend Linting & Static Analysis

```bash
cd solune/backend

# Lint check
ruff check src tests

# Format check
ruff format --check src tests

# Security scan
bandit -r src/ -ll -ii --skip B104,B608

# Type check
pyright src

# Dependency audit
pip-audit
```

### Frontend Tests

```bash
cd solune/frontend

# Run unit/component tests
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run accessibility tests
npm run test:a11y

# Run mutation testing
npm run test:mutate
```

### Frontend Linting & Static Analysis

```bash
cd solune/frontend

# Lint check
npm run lint

# Type check
npm run type-check

# Theme audits
npm run audit:theme-colors      # Find hardcoded colors
npm run audit:theme-contrast     # Check contrast ratios
```

### End-to-End Tests

```bash
cd solune/frontend

# Install Playwright browsers
npx playwright install --with-deps chromium

# Run E2E tests
npm run test:e2e

# Run with UI mode
npm run test:e2e:ui

# Run headed (visible browser)
npm run test:e2e:headed

# View test report
npm run test:e2e:report
```

---

## Docker Build & Deploy

### Full Stack (Docker Compose)

```bash
cd solune

# Build and start all services
docker compose up --build -d

# Check service health
docker compose ps
# All 3 services should show "healthy":
# solune-backend    → http://localhost:8000
# solune-frontend   → http://localhost:5173
# solune-signal-api → internal port 8080

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

### Individual Images

```bash
# Build backend
docker build -t solune-backend ./solune/backend

# Build frontend
docker build -t solune-frontend ./solune/frontend \
  --build-arg VITE_API_BASE_URL=/api/v1

# Verify images
docker images | grep solune
```

---

## CI/CD Commands

The following commands mirror what CI runs (`.github/workflows/ci.yml`):

```bash
# Full backend CI pipeline
cd solune/backend
pip install -e ".[dev]"
pip-audit
ruff check src tests
ruff format --check src tests
bandit -r src/ -ll -ii --skip B104,B608
pyright src
pytest --cov=src --cov-report=term-missing --durations=20

# Full frontend CI pipeline
cd solune/frontend
npm ci
npm audit --audit-level=high
npm run lint
npm run type-check
npm run test:coverage
npm run build
```

---

## Phase-Specific Development Workflows

### Phase 1: Security & Data Integrity

```bash
# Test pipeline state persistence
cd solune/backend
pytest tests/unit/test_pipeline_state*.py -v

# Test security middleware
pytest tests/unit/test_middleware*.py -v

# Scan for hardcoded secrets
bandit -r src/ -ll -ii
grep -rn "password\|secret\|api_key\|token" src/ --include="*.py" | grep -v "test\|#\|config\|env"
```

### Phase 2: Code Quality

```bash
# Measure cyclomatic complexity
# (Use radon or similar — not a current dependency, use pyright/ruff complexity warnings)
ruff check src --select C901  # McCabe complexity

# Check file line counts
find src -name "*.py" -exec wc -l {} + | sort -rn | head -20

# Check frontend module sizes
find src -name "*.tsx" -o -name "*.ts" | xargs wc -l | sort -rn | head -20
```

### Phase 6: Accessibility

```bash
cd solune/frontend

# Run all accessibility checks
npm run audit:theme-contrast
npm run test:a11y

# Run Playwright with accessibility assertions
npm run test:e2e -- --grep "accessibility"
```

---

## Release Verification Checklist

```bash
# 1. Version string consistency
grep -r "0.1.0" solune/backend/pyproject.toml solune/frontend/package.json solune/CHANGELOG.md

# 2. Full test suite
cd solune/backend && pytest --cov=src
cd solune/frontend && npm run test:coverage

# 3. Static analysis clean
cd solune/backend && ruff check src tests && pyright src
cd solune/frontend && npm run lint && npm run type-check

# 4. Security clean
cd solune/backend && bandit -r src/ -ll -ii --skip B104,B608 && pip-audit
cd solune/frontend && npm audit --audit-level=high

# 5. Docker from scratch
cd solune && docker compose down -v && docker compose up --build -d
# Wait for all services to report healthy

# 6. Build frontend production bundle
cd solune/frontend && npm run build
# Verify no build errors
```

---

## Key File Locations

| Purpose | Path |
|---------|------|
| Backend entry point | `solune/backend/src/main.py` |
| Backend config | `solune/backend/src/config.py` |
| Database migrations | `solune/backend/src/migrations/` |
| API routes | `solune/backend/src/api/` |
| Services | `solune/backend/src/services/` |
| God class (to split) | `solune/backend/src/services/github_projects/service.py` |
| Pipeline polling | `solune/backend/src/services/copilot_polling/` |
| Middleware | `solune/backend/src/middleware/` |
| Frontend entry | `solune/frontend/src/main.tsx` |
| Components | `solune/frontend/src/components/` |
| Hooks | `solune/frontend/src/hooks/` |
| API client | `solune/frontend/src/services/api.ts` |
| Constants | `solune/frontend/src/constants.ts` |
| Environment template | `solune/.env.example` |
| Docker Compose | `solune/docker-compose.yml` |
| CI config | `.github/workflows/ci.yml` |
| Documentation | `solune/docs/` |
