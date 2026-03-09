# Contract: Review Checklists

**Feature**: 032-doc-sweep | **Date**: 2026-03-09
**Requirements**: FR-003–FR-013, FR-020, FR-021 | **Success Criteria**: SC-002, SC-003, SC-004

## Overview

Three review checklists exist in `docs/checklists/` for weekly, monthly, and quarterly cadences. This contract defines the required content for each and validates the existing implementations against 032-doc-sweep requirements.

## Weekly Sweep Checklist (`docs/checklists/weekly-sweep.md`)

### Required Content (FR-003–FR-006)

The weekly sweep checklist MUST include the following sections:

**API Reference Validation (FR-004)**:

- [ ] Scan `backend/src/api/` — confirm every route file has matching API table entries in `docs/api-reference.md`
- [ ] Confirm all path prefixes, methods, and path params are still accurate
- [ ] Flag any endpoints removed or deprecated but still listed

**Configuration Documentation Validation (FR-005)**:

- [ ] Compare documented env vars against `backend/src/config.py` — add any missing, remove any deleted
- [ ] Confirm default values and required/optional status are still correct

**Setup Guide Validation (FR-006)**:

- [ ] Confirm Docker Compose and manual setup steps still match project state
- [ ] Confirm prerequisite versions (Python, Node, Docker) still match `pyproject.toml` and `package.json`
- [ ] Confirm Codespaces badge and quick start flow still work end-to-end

### Weekly Sweep Constraints

- MUST be completable within ~30 minutes (SC-002)
- MUST be self-contained (no external tools or scripts required)
- MUST use GitHub-flavored markdown checkbox syntax (`- [ ]`)

## Monthly Review Checklist (`docs/checklists/monthly-review.md`)

### Required Content (FR-007–FR-010, FR-020, FR-021)

The monthly review checklist MUST include the following sections:

**Coverage Audit (FR-007)**:

- [ ] Every file in `docs/` is **Accurate** — reflects current code behavior
- [ ] Every file in `docs/` is **Complete** — no major features undocumented
- [ ] Every file in `docs/` is **Consistent** — terminology, naming, formatting uniform

**File-by-File Verification Table**:
Table listing each doc file, its ownership, and key things to verify.

**Cross-Reference Check (FR-008)**:

- [ ] All internal `docs/` links are valid and resolve to existing headings
- [ ] Code snippets in docs compile or run without error against current codebase (FR-009)
- [ ] README.md top-level links to correct doc files
- [ ] Any external links still resolve to relevant pages

**Readability & Usability (FR-010)**:

- [ ] Each page has a clear purpose statement at the top
- [ ] Step-by-step guides use numbered lists and include expected outcomes
- [ ] Configuration tables include: variable name, type, required/optional, default, description
- [ ] API tables include: method, path, auth required, brief description
- [ ] Troubleshooting entries follow the Symptom → Cause → Fix format (FR-020)

**Good Documentation Acceptance Bar (FR-021)**:

- [ ] All reviewed files meet the "good documentation" definition: accurate, minimal, actionable, discoverable, maintained

### Monthly Review Constraints

- MUST be completable within 2–3 hours (SC-003)
- MUST cover every documentation file listed in `docs/OWNERS.md`
- MUST result in zero unresolved issues older than one review cycle (SC-003)

## Quarterly Audit Checklist (`docs/checklists/quarterly-audit.md`)

### Required Content (FR-011–FR-013)

The quarterly audit checklist MUST include the following sections:

**Architecture Document Verification (FR-011)**:

- [ ] Service diagram reflects current Docker Compose topology
- [ ] All backend service modules are represented
- [ ] Data flow arrows are accurate — especially WebSocket paths and GitHub API interactions
- [ ] AI provider list is current

**Decision Records (FR-012)**:

- [ ] Any significant architectural decision made this quarter is captured as an ADR in `docs/decisions/`
- [ ] ADR format follows Context → Decision → Consequences
- [ ] ADR index in `docs/decisions/README.md` is up to date

**Developer Experience Audit (FR-013)**:

- [ ] Have a team member follow `docs/setup.md` from scratch — note any friction
- [ ] Time the full local setup end-to-end; document in setup guide
- [ ] Review `docs/troubleshooting.md` — add any issues encountered during the audit

**Docs Gaps Analysis**:

- [ ] List all features shipped in the last quarter — confirm each has adequate documentation
- [ ] Identify docs that exist but no one references — consider consolidating or removing
- [ ] Check if `CHANGELOG.md` should be started or updated

### Quarterly Audit Constraints

- MUST be completable within ~half day (SC-004)
- MUST run after major feature milestones
- MUST result in all gaps identified and tracked (SC-004)

## Compliance Assessment

| Checklist | File | Status | Gaps |
|-----------|------|--------|------|
| Weekly sweep | `docs/checklists/weekly-sweep.md` | ✅ Exists | None — content covers FR-004–FR-006 |
| Monthly review | `docs/checklists/monthly-review.md` | ✅ Exists | Verify FR-021 acceptance bar is referenced |
| Quarterly audit | `docs/checklists/quarterly-audit.md` | ✅ Exists | None — content covers FR-012 ADR format + FR-013 DX test |

## Changes Required

Verify each existing checklist against the contract above during implementation. The primary addition for 032-doc-sweep is ensuring the monthly review checklist references the "good documentation" definition (FR-021) as the acceptance bar for reviewed files.
