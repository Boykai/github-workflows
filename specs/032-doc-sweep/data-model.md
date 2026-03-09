# Data Model: Recurring Documentation Update Process

**Feature**: 032-doc-sweep | **Date**: 2026-03-09

## Entities

> This feature is process-oriented. Entities are markdown documents and checklists — not database tables or API models. The data model describes the structure and relationships of these artifacts.

### Documentation File

A markdown file or documentation directory within the `docs/` directory, `frontend/docs/`, or at the repository root that describes a specific aspect of the project.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `path` | string | Path to a markdown file or documentation directory relative to the repository root (e.g., `docs/setup.md`, `docs/decisions/`) |
| `owner_role` | string | Designated responsible role from `docs/OWNERS.md` |
| `content_category` | enum | `setup` / `configuration` / `api-reference` / `architecture` / `agent-pipeline` / `best-practices` / `integration` / `testing` / `troubleshooting` / `project-structure` / `frontend` / `checklist` / `decision-record` |
| `last_reviewed` | date | Date of most recent review (tracked informally; target: within current quarter per SC-009) |
| `review_status` | enum | `current` / `needs-review` / `deprecated` |

**Relationships**: Each Documentation File has exactly one owner role mapping in `docs/OWNERS.md` (FR-018).

**Validation Rules**:

- Every file in `docs/` MUST have a corresponding entry in `docs/OWNERS.md` (FR-017)
- Files MUST use ATX-style headings, language-tagged code blocks, and appropriate list formatting (FR-014)
- Filenames referenced in documentation MUST use inline code formatting (FR-014)
- Last-reviewed date MUST be within the current quarter to be considered "maintained" (SC-009)
- Files MUST satisfy the "good documentation" definition: accurate, minimal, actionable, discoverable, maintained (FR-021)

**Current Instances** (15 files):

| Path | Category | Owner Role |
|------|----------|-----------|
| `docs/setup.md` | setup | Infra/DX lead |
| `docs/configuration.md` | configuration | Backend lead |
| `docs/api-reference.md` | api-reference | Backend lead |
| `docs/architecture.md` | architecture | Tech lead |
| `docs/agent-pipeline.md` | agent-pipeline | Backend lead |
| `docs/custom-agents-best-practices.md` | best-practices | Backend lead |
| `docs/signal-integration.md` | integration | Backend lead |
| `docs/testing.md` | testing | QA / full-stack lead |
| `docs/troubleshooting.md` | troubleshooting | Rotating |
| `docs/project-structure.md` | project-structure | Full-stack lead |
| `docs/checklists/weekly-sweep.md` | checklist | Rotating dev |
| `docs/checklists/monthly-review.md` | checklist | Tech lead |
| `docs/checklists/quarterly-audit.md` | checklist | Tech lead |
| `docs/decisions/` | decision-record | Tech lead |
| `frontend/docs/findings-log.md` | frontend | Frontend lead |

### Documentation Checklist

A structured list of verification items used at different review cadences.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `type` | enum | `pr-level` / `weekly-sweep` / `monthly-review` / `quarterly-audit` |
| `file_path` | string | Location of the checklist markdown file |
| `items` | list | Ordered list of checkbox items (`- [ ]` syntax) |
| `cadence` | string | How often this checklist is used |
| `estimated_duration` | string | Expected time to complete |
| `responsible_role` | string | Who performs this checklist |
| `trigger` | string | What initiates this review |

**Instances**:

| Type | File | Cadence | Duration | Role | Trigger |
|------|------|---------|----------|------|---------|
| PR-level | `.github/pull_request_template.md` (Documentation section) | Every PR | ~2 min | PR author | Opening a pull request |
| Weekly sweep | `docs/checklists/weekly-sweep.md` | Weekly | ~30 min | Dev (rotation) | Dev rotation schedule |
| Monthly review | `docs/checklists/monthly-review.md` | Monthly | ~2–3 hours | Tech lead | Sprint planning item |
| Quarterly audit | `docs/checklists/quarterly-audit.md` | Quarterly | ~half day | Tech lead | After major feature milestones |

**Validation Rules**:

- PR-level checklist MUST cover: endpoint docs, configuration docs, setup docs, agent pipeline docs, schema/data model docs, and doc update summary (FR-001)
- PR-level checklist MUST allow "no doc changes needed" with rationale (FR-002)
- Weekly sweep MUST cover: API reference accuracy, configuration accuracy, setup guide accuracy (FR-003–FR-006)
- Monthly review MUST cover: accuracy, completeness, consistency, cross-references, code snippet correctness, readability (FR-007–FR-010)
- Quarterly audit MUST cover: service topology, ADR completeness, developer experience test, docs gaps analysis (FR-011–FR-013)
- Troubleshooting entries reviewed during monthly review MUST follow Symptom → Cause → Fix format (FR-020)
- All review phases MUST apply the "good documentation" definition as the acceptance bar (FR-021)

### Architecture Decision Record (ADR)

A document capturing a significant architectural decision, stored in `docs/decisions/`.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `number` | integer | Sequential ADR number (e.g., 001, 002) |
| `title` | string | Short descriptive title (kebab-case filename) |
| `context` | text | Background and problem being addressed |
| `decision` | text | What was decided |
| `consequences` | text | Impact of the decision (positive and negative) |
| `date` | date | When the decision was made |
| `status` | enum | `accepted` / `superseded` / `deprecated` |

**Validation Rules**:

- ADRs MUST follow the Context → Decision → Consequences format (FR-012)
- Significant architectural decisions made after process adoption MUST have a corresponding ADR (SC-004)
- ADR numbering MUST be sequential with zero-padded three-digit prefix

**Existing State**: 6 ADRs in `docs/decisions/` (001–006) with a `README.md` template. No structural changes needed.

### Documentation Ownership Record

An entry in `docs/OWNERS.md` mapping a documentation file to its responsible role.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `doc_path` | string | Path to the documentation file |
| `owner_role` | string | Role responsible (e.g., "Backend lead", "Tech lead") |
| `key_things_to_verify` | string | Summary of what the owner should check during reviews |
| `rotation_indicator` | boolean | Whether ownership rotates (e.g., `troubleshooting.md`) |

**Validation Rules**:

- Every file in `docs/` MUST have a corresponding ownership entry (FR-017, SC-005)
- Each file MUST have exactly one designated owner or explicit rotation scheme (FR-018)
- Default owner for unassigned files is the tech lead (edge case from spec)

**Existing State**: `docs/OWNERS.md` exists with 15 file-to-owner mappings and a review cadence table. Fully satisfies FR-017, FR-018, FR-019.

### Review Cadence Entry

A scheduled documentation review activity defined in `docs/OWNERS.md`.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `review_type` | enum | `pr-level` / `weekly` / `monthly` / `quarterly` / `on-demand` |
| `frequency` | string | How often the review occurs |
| `trigger` | string | What initiates the review |
| `responsible_role` | string | Who performs the review |
| `estimated_duration` | string | Expected time to complete |
| `scope` | string | Which files are reviewed |

**Instances** (from spec FR-019):

| Review Type | Frequency | Trigger | Role | Duration | Scope |
|-------------|-----------|---------|------|----------|-------|
| Inline doc check | Every PR | Author + reviewer responsibility | PR author | ~2 min | Files changed by PR |
| Staleness sweep | Weekly | Dev rotation | Rotating dev | ~30 min | API reference, configuration, setup |
| Full doc review | Monthly | Sprint planning item | Tech lead | ~2–3 hours | All `docs/` files |
| Architecture audit | Quarterly | After major feature milestones | Tech lead | ~half day | Architecture, decisions |
| New contributor review | On demand | Before onboarding | Tech lead | Variable | Setup guide, troubleshooting |

## State Transitions

### Documentation File Lifecycle

```text
[New] → [Current] → [Needs Review] → [Current]
                  ↘ [Deprecated] → [Removed]
```

- **New → Current**: File is created with accurate content and added to `docs/OWNERS.md`
- **Current → Needs Review**: File's last-reviewed date exceeds one quarter (SC-009)
- **Needs Review → Current**: File is reviewed and confirmed accurate during a review cycle
- **Current → Deprecated**: Monthly review identifies file as no longer needed
- **Deprecated → Removed**: No objections raised within one review cycle; file deleted and `OWNERS.md` updated

### Checklist Execution Lifecycle

```text
[Not Started] → [In Progress] → [Complete]
                              ↗ [Blocked] → [In Progress]
```

- **Not Started → In Progress**: Developer/lead begins the checklist at scheduled cadence
- **In Progress → Blocked**: Significant discrepancy found that cannot be resolved in-session (edge case: >30 min for weekly sweep)
- **Blocked → In Progress**: Tracking issue filed; checklist continues with remaining items
- **In Progress → Complete**: All items checked or explicitly blocked with issues filed

## Entity Relationship Diagram

```text
Documentation File 1..* ──── 1 Ownership Record (in OWNERS.md)
       │
       │ reviewed-by
       ▼
Documentation Checklist 1..* ──── items ──── Checklist Item 1..*
       │
       │ governed-by
       ▼
Review Cadence Entry 1..* (in OWNERS.md)
       │
       │ references (quarterly only)
       ▼
Architecture Decision Record 0..*
```

- Each Documentation File is reviewed by one or more Checklist types at different cadences
- Each Checklist contains multiple Checklist Items (checkbox rows)
- Review Cadence Entries define when each Checklist is executed
- The quarterly audit Checklist references ADRs as part of its review scope
- The Ownership Record assigns exactly one role to each Documentation File
- All review outcomes are evaluated against the "good documentation" definition (FR-021)
