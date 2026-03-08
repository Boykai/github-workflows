# Contract: PR Template — Documentation Checklist

**Feature**: 030-doc-sweep | **Date**: 2026-03-08
**Requirements**: FR-001, FR-002 | **Success Criteria**: SC-001

## Current State

The PR template at `.github/pull_request_template.md` already includes a comprehensive documentation checklist section. This contract validates the existing template against 030-doc-sweep requirements.

## Contract Specification

### Required Sections

The PR template MUST contain the following sections:

1. **Description** — Free-text area for change motivation
2. **Type of Change** — Checkbox list of change categories
3. **Documentation** — Checklist of documentation update obligations
4. **Testing** — Checkbox list of test obligations

### Documentation Checklist Items (FR-001)

The Documentation section MUST include the following checklist items:

| # | Checklist Item | Spec Mapping |
|---|---------------|--------------|
| 1 | Any new endpoint added to `backend/src/api/` has a corresponding entry in `docs/api-reference.md` | FR-001 |
| 2 | Any new environment variable added to `backend/src/config.py` is documented in `docs/configuration.md` | FR-001 |
| 3 | Any change to startup behavior, Docker setup, or prerequisites is reflected in `docs/setup.md` | FR-001 |
| 4 | Any new agent, workflow module, or AI provider change is reflected in `docs/agent-pipeline.md` | FR-001 |
| 5 | Any schema or data model change is reflected in relevant API or architecture docs | FR-001 |
| 6 | Documentation updated (or confirmed not needed — explain below) | FR-002 |

### Rationale Field (FR-002)

The template MUST include a field where the author can specify which doc files were updated, or explicitly state "no doc changes needed" with a rationale.

**Format**: `**Doc files updated**: <!-- List files or write "None — no doc changes needed" with rationale -->`

## Compliance Assessment

| Requirement | Current Template | Status |
|-------------|-----------------|--------|
| FR-001: 6 documentation checklist items | ✅ All 6 items present | Compliant |
| FR-002: "No doc changes needed" option | ✅ "confirmed not needed — explain below" + rationale field | Compliant |
| SC-001: 100% of PRs include completed checklist | ✅ Template auto-populates for every PR | Compliant (by design) |

## Changes Required

**None.** The existing PR template is fully compliant with FR-001 and FR-002. No modifications needed.
