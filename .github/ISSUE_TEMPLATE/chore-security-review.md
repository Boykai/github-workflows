# Recurring Security Review Process

## Overview

A structured, repeatable cadence for auditing security, vulnerability exposure, and privacy posture across the full stack (backend, frontend, infrastructure, third-party integrations).

---

## Cadence

| Review Type       | Frequency     | Trigger                                      |
|-------------------|---------------|----------------------------------------------|
| Automated Scan    | Every PR      | CI pipeline                                  |
| Quick Spot Check  | Weekly        | Dev team rotation                            |
| Full Security Review | Monthly    | Scheduled sprint item                        |
| Deep Audit        | Quarterly     | Planned milestone + external tooling         |
| Incident Postmortem | On demand  | After any security incident or near-miss     |

---

## Phase 1 — Automated Checks (Every PR / CI)

Run on every pull request via CI. Fail the build on critical findings.

- [ ] **Dependency vulnerability scan** — `pip-audit` (backend), `npm audit --audit-level=high` (frontend)
- [ ] **Static analysis / SAST** — `bandit -r backend/src` for Python, `eslint` with security plugin for TypeScript
- [ ] **Secret detection** — `gitleaks detect` or `truffleHog` to catch credentials committed to source
- [ ] **Docker image scan** — `trivy image` on both `backend` and `frontend` images
- [ ] **License compliance** — flag new dependencies with restrictive or unknown licenses

---

## Phase 2 — Weekly Spot Check (Dev Rotation, ~1 hour)

Assign to a rotating team member each week.

### Authentication & Session Security
- [ ] Confirm OAuth tokens are **not** passed via URL query params
- [ ] Confirm session cookies use `HttpOnly; SameSite=Strict; Secure` flags
- [ ] Verify no credentials appear in application or access logs

### Configuration Drift
- [ ] Confirm `DEBUG=false` in all deployed environments
- [ ] Confirm `ENCRYPTION_KEY` and `GITHUB_WEBHOOK_SECRET` are set and meet entropy requirements
- [ ] Verify `SESSION_SECRET_KEY` is ≥ 64 characters
- [ ] Check that API docs (`/docs`, `/redoc`) are not publicly accessible

### Access Control
- [ ] Spot-check 2–3 project-scoped endpoints — confirm they reject cross-user project IDs
- [ ] Review any newly added endpoints for missing auth dependencies

---

## Phase 3 — Monthly Full Security Review (~half day)

### OWASP Top 10 Checklist

| # | Category | Checks |
|---|----------|--------|
| A01 | Broken Access Control | All resource endpoints verify ownership; no IDOR paths exist |
| A02 | Cryptographic Failures | Encryption at rest enforced; no plaintext token storage; TLS enforced |
| A03 | Injection | All DB queries use parameterized statements; no `eval` or shell injection paths |
| A04 | Insecure Design | Rate limits active on chat, auth, agent, and workflow endpoints |
| A05 | Security Misconfiguration | HTTP security headers present (CSP, HSTS, Referrer-Policy, Permissions-Policy); nginx `server_tokens off`; no root containers |
| A06 | Vulnerable Components | All deps at latest patch; no known CVEs in `pip-audit` / `npm audit` output |
| A07 | Auth Failures | Constant-time comparison on all secrets/tokens; session management reviewed |
| A08 | Data Integrity | Webhook signatures verified unconditionally; no skip-in-debug paths |
| A09 | Logging & Monitoring | Sensitive data absent from logs; auth failures and anomalies are logged |
| A10 | SSRF | Any outbound HTTP calls (GitHub API, Signal) use allowlists; no user-controlled URLs |

### Privacy Review
- [ ] Confirm only minimum necessary GitHub OAuth scopes are requested
- [ ] Audit what user data is stored — confirm it matches stated data model
- [ ] Verify database file and directory permissions are `0600` / `0700`
- [ ] Review data retention — confirm no stale tokens or orphaned user records accumulate
- [ ] Check that no PII is included in error responses returned to clients

### Infrastructure Review
- [ ] Confirm Docker services are **not** bound to `0.0.0.0` (use `127.0.0.1` or proxy-only)
- [ ] Confirm all containers run as non-root users
- [ ] Review `docker-compose.yml` for hardcoded secrets or unsafe volume mounts
- [ ] Verify nginx config has all required security headers and hides version info
- [ ] Check base image versions — update if newer patch images are available

### Third-Party Integration Review
- [ ] Review GitHub App / OAuth permissions — confirm least-privilege scopes still apply
- [ ] Review Signal integration webhook secret handling — confirm constant-time comparison
- [ ] Audit any new third-party libraries added since last review

---

## Phase 4 — Quarterly Deep Audit (~1–2 days)

### External Tooling
- [ ] Run **OWASP ZAP** or **Burp Suite** (passive + active scan) against staging environment
- [ ] Run **`semgrep`** with `p/security-audit` and `p/owasp-top-ten` rulesets
- [ ] Run **`sqlmap`** (non-destructive, read-only mode) against parameterized endpoints in staging
- [ ] Run **`trivy fs .`** for full filesystem vulnerability scan
- [ ] Review GitHub Security Advisories and Dependabot alerts

### Architecture Review
- [ ] Re-evaluate threat model — have new features introduced new trust boundaries?
- [ ] Review WebSocket endpoint security — auth enforced at connection and message level?
- [ ] Confirm AI agent pipeline does not expose prompt injection vectors to end users
- [ ] Review caching layer — confirm no sensitive data is cached without TTL or user scoping

### Penetration Testing
- [ ] Attempt IDOR on project, task, and workflow endpoints with a second test user
- [ ] Attempt session fixation / replay on OAuth callback flow
- [ ] Attempt webhook replay attacks with stale/forged signatures
- [ ] Test rate limits — confirm they block after threshold

---

## Phase 5 — Remediation & Tracking

### Severity SLA

| Severity | Remediation Target |
|----------|--------------------|
| Critical | Patch within 24 hours; hotfix deployed same day |
| High     | Patch within 1 week; included in next release |
| Medium   | Patch within current sprint (≤2 weeks) |
| Low      | Backlog; addressed within next quarter |

### Process
1. File a GitHub Issue using the `chore: security review` template for every finding
2. Label with `security` + severity (`critical` / `high` / `medium` / `low`)
3. Assign to the on-call dev; set milestone matching the SLA date
4. After fix, verify in staging before closing the issue
5. Add a regression test where applicable (unit or integration)
6. Document in a `SECURITY_CHANGELOG.md` entry for audit trail

---

## Roles & Responsibilities

| Role | Responsibility |
|------|---------------|
| Dev (rotation) | Weekly spot check; triage new findings |
| PR author | Resolve all CI security gate failures before merge |
| Tech lead | Monthly review sign-off; quarterly deep audit coordination |
| All contributors | Never commit secrets; follow secure coding checklist in PR template |

---

## Tooling Reference

| Tool | Purpose | Run Command |
|------|---------|-------------|
| `pip-audit` | Python CVE scan | `pip-audit -r backend/pyproject.toml` |
| `bandit` | Python SAST | `bandit -r backend/src -ll` |
| `npm audit` | JS CVE scan | `npm audit --audit-level=high` |
| `trivy` | Container + FS scan | `trivy image <name>` / `trivy fs .` |
| `gitleaks` | Secret detection | `gitleaks detect --source .` |
| `semgrep` | Multi-language SAST | `semgrep --config p/owasp-top-ten .` |
| OWASP ZAP | DAST (dynamic scan) | Via staging environment |