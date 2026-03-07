# Contract: Review Checklists

**Feature**: 027-doc-sweep | **Date**: 2026-03-07
**Requirements**: FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009

## File Locations

```text
docs/checklists/
├── weekly-sweep.md          # FR-003, FR-004
├── monthly-review.md        # FR-005, FR-006, FR-007
└── quarterly-audit.md       # FR-008, FR-009
```

---

## Weekly Staleness Sweep Checklist

**File**: `docs/checklists/weekly-sweep.md`
**Cadence**: Weekly (~30 minutes, dev rotation)
**Requirements**: FR-003, FR-004

### Required Sections

#### Header

```markdown
# Weekly Documentation Staleness Sweep

**Estimated time**: ~30 minutes
**Frequency**: Weekly (dev rotation)
**Purpose**: Catch documentation that has drifted from the codebase since the last review.
```

#### API Reference Check (FR-003)

Must include items for:
- Route-to-documentation mapping: scan `backend/src/api/` and confirm every route file has matching entries in `docs/api-reference.md`
- Path prefix, method, and path parameter accuracy
- Deprecated/removed endpoints still listed

#### Configuration Check (FR-003)

Must include items for:
- Environment variable parity: compare `docs/configuration.md` against `backend/src/config.py`
- Default value and required/optional status correctness

#### Setup Guide Check (FR-003)

Must include items for:
- Docker Compose and manual setup step accuracy
- Prerequisite version accuracy: compare against `pyproject.toml` and `package.json`
- Codespaces badge and quick start flow validity

#### Completion Record

```markdown
## Completion

- **Date**: YYYY-MM-DD
- **Reviewer**: @username
- **Issues found**: [count] (link to issues if filed)
```

### Constraints

- Total checklist MUST be completable in ~30 minutes (FR-004)
- Items requiring >15 minutes of investigation should be filed as separate issues

---

## Monthly Full Documentation Review Checklist

**File**: `docs/checklists/monthly-review.md`
**Cadence**: Monthly (~2–3 hours, tech lead)
**Requirements**: FR-005, FR-006, FR-007

### Required Sections

#### Header

```markdown
# Monthly Full Documentation Review

**Estimated time**: 2–3 hours
**Frequency**: Monthly (sprint planning item)
**Purpose**: Comprehensive quality gate ensuring accuracy, completeness, and consistency across all documentation.
```

#### Coverage Audit (FR-005)

For each file in `docs/`, verify:
- **Accurate**: reflects current code behavior
- **Complete**: no major features undocumented
- **Consistent**: uniform terminology and formatting

Must include a table mapping each doc file to ownership and verification items.

#### Cross-Reference Check (FR-006)

Must include items for:
- Internal `docs/` links resolve to existing headings
- Code snippets compile/run against current codebase
- `README.md` top-level links point to correct doc files
- External links resolve to relevant pages

#### Readability Assessment (FR-007)

Must include items for:
- Each page has a clear purpose statement
- Step-by-step guides use numbered lists with expected outcomes
- Configuration tables include: variable name, type, required/optional, default, description
- API tables include: method, path, auth required, brief description
- Troubleshooting entries follow: Symptom → Cause → Fix format

#### Completion Record

Same format as weekly sweep.

---

## Quarterly Architecture Audit Checklist

**File**: `docs/checklists/quarterly-audit.md`
**Cadence**: Quarterly (~half day, tech lead)
**Requirements**: FR-008, FR-009

### Required Sections

#### Header

```markdown
# Quarterly Architecture Audit

**Estimated time**: ~half day
**Frequency**: Quarterly (after major feature milestones)
**Purpose**: Deep structural documentation review covering architecture, decision records, developer experience, and documentation gaps.
```

#### Architecture Document Review (FR-008)

Must include items for:
- Service diagram reflects current Docker Compose topology
- All backend service modules represented
- Data flow arrows accurate (WebSocket paths, GitHub API interactions)
- AI provider list current

#### Architecture Decision Records (FR-008, FR-009)

Must include items for:
- Significant architectural decisions from the quarter have corresponding ADRs
- ADRs follow Context-Decision-Consequences format (FR-009)
- ADR index (`docs/decisions/README.md`) is up to date

#### Developer Experience Audit (FR-008)

Must include items for:
- Team member follows `docs/setup.md` from scratch — document friction
- Time full local setup end-to-end
- Update `docs/troubleshooting.md` with issues encountered

#### Documentation Gaps Analysis (FR-008)

Must include items for:
- All features shipped in the quarter have adequate documentation
- Identify docs that exist but no one references — consider consolidating/removing
- Evaluate need for changelog (`CHANGELOG.md`)

#### Completion Record

Same format as weekly sweep.

---

## Validation Rules (All Checklists)

- All checklists MUST use GitHub-flavored markdown checkbox syntax (`- [ ]`)
- All checklists MUST include a header with purpose, estimated time, and frequency
- All checklists MUST include a completion record section
- All checklists MUST be subject to markdownlint CI validation
- All checklists MUST follow ATX-style headings (FR-014)
- Filenames in checklists MUST use inline code formatting (FR-015)
