# Data Model: Recurring Documentation Update Process

**Feature**: 027-doc-sweep | **Date**: 2026-03-07

## Entities

> This feature is process-oriented. Entities are markdown documents and checklists — not database tables or API models. The data model describes the structure and relationships of these artifacts.

### Documentation File

A markdown file within the `docs/` directory or at the repository root that describes a specific aspect of the project.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `path` | string | File path relative to repository root (e.g., `docs/setup.md`) |
| `owner_role` | string | Designated responsible role from `docs/OWNERS.md` |
| `last_reviewed` | date | Date of most recent review (tracked informally; target: within current quarter) |
| `review_status` | enum | `current` / `needs-review` / `deprecated` |

**Relationships**: Each Documentation File has exactly one owner role mapping in `docs/OWNERS.md`.

**Validation Rules**:
- Every file in `docs/` MUST have a corresponding entry in `docs/OWNERS.md` (FR-013)
- Files MUST use ATX-style headings, language-tagged code blocks, and appropriate list formatting (FR-014)
- Filenames referenced in documentation MUST use inline code formatting (FR-015)
- Last-reviewed date MUST be within the current quarter to be considered "maintained" (FR-018)

### Documentation Checklist

A structured list of verification items used at different review cadences.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `type` | enum | `pr-level` / `weekly-sweep` / `monthly-review` / `quarterly-audit` |
| `file_path` | string | Location of the checklist markdown file |
| `items` | list | Ordered list of checkbox items |
| `cadence` | string | How often this checklist is used |
| `estimated_duration` | string | Expected time to complete |
| `responsible_role` | string | Who performs this checklist |

**Instances**:

| Type | File | Cadence | Duration | Role |
|------|------|---------|----------|------|
| PR-level | `.github/pull_request_template.md` (section) | Every PR | ~2 min | PR author |
| Weekly sweep | `docs/checklists/weekly-sweep.md` | Weekly | ~30 min | Dev (rotation) |
| Monthly review | `docs/checklists/monthly-review.md` | Monthly | ~2–3 hours | Tech lead |
| Quarterly audit | `docs/checklists/quarterly-audit.md` | Quarterly | ~half day | Tech lead |

**Validation Rules**:
- PR-level checklist MUST cover: endpoint docs, configuration docs, setup docs, agent pipeline docs, schema/data model docs, and doc update summary (FR-001)
- Weekly sweep MUST cover: API reference accuracy, configuration accuracy, setup guide accuracy (FR-003)
- Weekly sweep MUST be completable in ~30 minutes (FR-004)
- Monthly review MUST cover: accuracy, completeness, consistency, cross-references, readability (FR-005–FR-007)
- Quarterly audit MUST cover: architecture document, ADRs, developer experience, docs gaps (FR-008)

### Architecture Decision Record (ADR)

A document capturing a significant architectural decision, stored in `docs/decisions/`.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `number` | integer | Sequential ADR number (e.g., 001, 002) |
| `title` | string | Short descriptive title |
| `context` | text | Background and problem being addressed |
| `decision` | text | What was decided |
| `consequences` | text | Impact of the decision (positive and negative) |
| `date` | date | When the decision was made |
| `status` | enum | `accepted` / `superseded` / `deprecated` |

**Validation Rules**:
- ADRs MUST follow the Context-Decision-Consequences format (FR-009)
- Significant architectural decisions made after process adoption MUST have a corresponding ADR (SC-007)

**Existing State**: 6 ADRs exist in `docs/decisions/` (001–006) with a README.md template. No structural changes needed.

### Documentation Ownership Mapping

A file mapping each documentation file to its responsible role, stored at `docs/OWNERS.md`.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `doc_path` | string | Path to the documentation file |
| `owner_role` | string | Role responsible (e.g., "Backend lead", "Tech lead") |

**Current Mappings** (from existing `docs/OWNERS.md`):

| Document | Owner Role |
|----------|-----------|
| `docs/setup.md` | Infra/DX lead |
| `docs/configuration.md` | Backend lead |
| `docs/api-reference.md` | Backend lead |
| `docs/architecture.md` | Tech lead |
| `docs/agent-pipeline.md` | Backend lead |
| `docs/custom-agents-best-practices.md` | Backend lead |
| `docs/signal-integration.md` | Backend lead |
| `docs/testing.md` | QA / full-stack lead |
| `docs/troubleshooting.md` | Rotating (whoever fixes the bug) |
| `docs/project-structure.md` | Full-stack lead |
| `docs/decisions/` | Tech lead |

**Validation Rules**:
- Every file in `docs/` MUST have a corresponding ownership entry (FR-013, SC-005)
- Default owner for unassigned files is the tech lead (edge case from spec)

**Existing State**: `docs/OWNERS.md` already exists and satisfies FR-013. The `docs/checklists/` directory (new) will need an ownership entry added.

## State Transitions

### Documentation File Lifecycle

```text
[New] → [Current] → [Needs Review] → [Current]
                  ↘ [Deprecated] → [Removed]
```

- **New → Current**: File is created with accurate content and added to `docs/OWNERS.md`
- **Current → Needs Review**: File's last-reviewed date exceeds one quarter (SC-008)
- **Needs Review → Current**: File is reviewed and confirmed accurate during a review cycle
- **Current → Deprecated**: Monthly review identifies file as no longer needed (edge case from spec)
- **Deprecated → Removed**: No objections raised within one review cycle; file deleted and references updated

### Checklist Execution Lifecycle

```text
[Not Started] → [In Progress] → [Complete]
                              ↗ [Blocked] → [In Progress]
```

- **Not Started → In Progress**: Developer/lead begins the checklist at scheduled cadence
- **In Progress → Blocked**: Significant discrepancy found requiring separate issue (edge case: weekly sweep finds major rewriting needed)
- **Blocked → In Progress**: Issue filed; checklist continues with remaining items
- **In Progress → Complete**: All items checked or explicitly blocked with issues filed

## Entity Relationship Diagram

```text
Documentation File 1..* ──── 1 Ownership Mapping
       │
       │ reviewed-by
       ▼
Documentation Checklist 1..* ──── items ──── Checklist Item 1..*
       │
       │ references
       ▼
Architecture Decision Record 0..*
```

- Each Documentation File is reviewed by one or more Checklist types
- Each Checklist contains multiple Checklist Items (checkbox rows)
- The quarterly audit Checklist references ADRs as part of its review scope
- The Ownership Mapping assigns exactly one role to each Documentation File
