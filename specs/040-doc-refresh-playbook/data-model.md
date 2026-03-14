# Data Model: Recurring Documentation Refresh Playbook

**Feature**: 040-doc-refresh-playbook
**Date**: 2026-03-14
**Status**: Complete

## Overview

This feature defines a bi-weekly documentation refresh process. It does not introduce persistent database entities or API endpoints. The entities below describe the conceptual data structures used throughout the refresh workflow — stored as markdown documents and a single JSON baseline file.

## Entities

### 1. RefreshBaseline

**Description**: A persistent record of the last completed refresh cycle, stored as `docs/.last-refresh`. Used by the next cycle to determine the diff window for change detection (FR-001, FR-017, FR-020).

| Field | Type | Description |
|-------|------|-------------|
| date | string (ISO 8601) | Date and time of last completed refresh (e.g., `"2026-03-14T18:00:00Z"`) |
| sha | string | Git commit SHA at the time of the last completed refresh |
| documents_updated | string[] | List of document paths updated in the last cycle |
| documents_skipped | string[] | List of document paths reviewed but not needing updates |
| broken_links_found | number | Count of broken internal links discovered |
| manual_followups | string[] | Items flagged for manual follow-up in the next cycle |

**Validation Rules**:
- `date` must be a valid ISO 8601 timestamp
- `sha` must be a valid 40-character hex string (full SHA) or 7+ character abbreviated SHA
- `documents_updated` must contain valid file paths relative to the repository root
- File must be valid JSON parseable by standard JSON tools

**State Transitions**:
- **Missing → Created**: First refresh cycle creates the baseline file
- **Existing → Updated**: Each successful refresh cycle overwrites with new values
- **Corrupted → Fallback**: If JSON is malformed, the process falls back to date-based heuristic (2 weeks prior)

**Storage**: `docs/.last-refresh` (committed to repository)

---

### 2. ChangeManifest

**Description**: A categorized inventory of all changes detected since the last refresh. Produced during Phase 1 (Detection) and consumed by Phase 2 (Prioritization) and all subsequent phases (FR-005).

| Field | Type | Description |
|-------|------|-------------|
| refresh_window_start | string | Baseline date from the last refresh |
| refresh_window_end | string | Current date |
| sha_range | string | `<last-sha>..HEAD` |
| categories | Category[] | Five change categories (see below) |

**Category Structure**:

| Category | Description | Example Items |
|----------|-------------|---------------|
| New features | New pages, endpoints, services, UX flows | "Added /api/v1/videos/ endpoint" |
| Changed behavior | Renamed concepts, altered workflows, config changes | "Renamed 'Chat' nav item to 'Assistant'" |
| Removed functionality | Deleted routes, deprecated features, removed UI | "Removed /api/v1/legacy/ endpoint" |
| Architectural shifts | New services, refactored modules, changed dependencies | "Added Redis cache service to docker-compose" |
| UX shifts | New pages, removed pages, changed navigation | "New VideosPage added at /videos route" |

**ManifestItem Structure**:

| Field | Type | Description |
|-------|------|-------------|
| description | string | What changed (1–2 sentences) |
| source | enum | `"CHANGELOG"` \| `"specs"` \| `"git-diff"` |
| source_detail | string | Specific file/entry that surfaced the change |
| domain | string | Affected area: pipeline, agents, chat, projects, tools, settings, auth, signal, analytics, infra |
| affected_docs | string[] | Documentation files likely impacted |

**Validation Rules**:
- Every item must have exactly one source attribution
- Items must not be duplicated across categories
- Domain must be one of the predefined area labels from FR-006
- At minimum, description and source are required

**Relationships**:
- Produced from: RefreshBaseline (determines diff window), CHANGELOG.md, specs/ directories, git history
- Consumed by: PriorityAssignment, all doc update phases

**Storage**: `docs/.change-manifest.md` (working document, may be committed or treated as ephemeral)

---

### 3. PriorityAssignment

**Description**: A classification applied to each documentation file based on the Change Manifest analysis. Determines the order and urgency of documentation updates (FR-008).

| Field | Type | Description |
|-------|------|-------------|
| document_path | string | Path to the documentation file (e.g., `docs/api-reference.md`) |
| priority | enum | `P0` \| `P1` \| `P2` \| `P3` |
| trigger_reason | string | Why this priority was assigned (e.g., "New API endpoints detected") |
| manifest_items | string[] | References to ChangeManifest items that triggered this priority |
| source_of_truth | string[] | File(s) to diff the document against |

**Priority Rules** (from FR-008):

| Priority | Condition | Target Documents |
|----------|-----------|-----------------|
| P0 | App pitch or primary workflow changed | `README.md` |
| P1 | Directly affected by new/changed features | `api-reference.md`, `agent-pipeline.md`, `custom-agents-best-practices.md`, `signal-integration.md` |
| P2 | Modules added/removed/reorganized | `project-structure.md`, `architecture.md` |
| P3 | Config, errors, or test structure changed | `troubleshooting.md`, `configuration.md`, `testing.md`, `setup.md` |

**Validation Rules**:
- A document inherits its highest applicable priority (if triggered by multiple rules)
- Documents with no applicable triggers are not assigned a priority (skipped)
- P0 assignment requires confirmation of narrative shift (not just any change)

**Relationships**:
- Derived from: ChangeManifest
- Consumed by: README update phase, docs update phase

---

### 4. DocumentationMapping

**Description**: A static registry that associates each documentation file with its source-of-truth file(s) in the codebase. Used to determine what to diff each doc against and when a doc needs updating (FR-012).

| Documentation File | Source of Truth | Update Trigger |
|---|---|---|
| `README.md` | Feature list, `docker-compose.yml`, `pyproject.toml`, `package.json` | Pitch/workflow change (P0) |
| `docs/api-reference.md` | `backend/src/api/` route files | New/changed/removed endpoints |
| `docs/architecture.md` | `backend/src/services/` + `docker-compose.yml` | New services, changed topology |
| `docs/agent-pipeline.md` | Pipeline/orchestrator service code | Changed stages, execution groups, status flow |
| `docs/configuration.md` | `backend/src/config.py` | New/changed/removed env vars |
| `docs/custom-agents-best-practices.md` | Agent MCP sync service + `.agent.md` files | Changed frontmatter, MCP sync behavior |
| `docs/project-structure.md` | Filesystem (`tree` output) | Any structural refactor |
| `docs/testing.md` | Test dirs + `pyproject.toml` / `vitest.config.ts` | New test categories, changed commands |
| `docs/troubleshooting.md` | Recent bug fixes in Change Manifest | New error patterns, fixed issues removed |
| `docs/setup.md` | `pyproject.toml`, `package.json`, `docker-compose.yml` | Changed prerequisites or setup steps |
| `docs/signal-integration.md` | Signal-related backend code | Signal code changed |

**Validation Rules**:
- Every documentation file in `docs/` must have a mapping entry
- Source-of-truth paths must exist in the repository
- Mapping is reviewed during each refresh cycle for staleness

---

### 5. RefreshSummaryReport

**Description**: An output produced at the end of each refresh cycle listing all actions taken. Satisfies FR-021.

| Field | Type | Description |
|-------|------|-------------|
| cycle_date | string | Date of this refresh cycle |
| previous_baseline | object | The RefreshBaseline from cycle start |
| documents_updated | UpdateEntry[] | List of documents that were modified |
| documents_skipped | string[] | Documents reviewed but not needing changes |
| broken_links | BrokenLink[] | Internal links that do not resolve |
| diagrams_regenerated | boolean | Whether Mermaid diagrams were regenerated |
| adr_index_updated | boolean | Whether the ADR index was modified |
| changelog_entry | string | The CHANGELOG entry added for this refresh |
| manual_followups | string[] | Items requiring manual attention in next cycle |

**UpdateEntry Structure**:

| Field | Type | Description |
|-------|------|-------------|
| path | string | Document file path |
| sections_added | string[] | New sections added |
| sections_removed | string[] | Stale sections removed |
| sections_updated | string[] | Sections modified for accuracy |

**BrokenLink Structure**:

| Field | Type | Description |
|-------|------|-------------|
| source_file | string | File containing the broken link |
| line_number | number | Line number of the broken link |
| target_path | string | The link target that does not resolve |
| link_text | string | The display text of the broken link |

**Storage**: Committed as part of the CHANGELOG entry (summary) and stored in the updated RefreshBaseline (structured data)

## Entity Relationships

```text
RefreshBaseline ──produces──▶ ChangeManifest
     │                            │
     │                            ├──derives──▶ PriorityAssignment
     │                            │                   │
     │                            │                   ▼
     │                            │            DocumentationMapping
     │                            │                   │
     │                            ▼                   ▼
     │                     [Doc Update Phases]──▶ RefreshSummaryReport
     │                                                │
     ◀────────────────updated by────────────────────────┘
```

1. **RefreshBaseline** provides the diff window for creating the **ChangeManifest**
2. **ChangeManifest** is analyzed to produce **PriorityAssignment** for each doc
3. **PriorityAssignment** + **DocumentationMapping** determine which docs to update and against what source
4. All update actions are recorded in the **RefreshSummaryReport**
5. **RefreshSummaryReport** data is written back to update the **RefreshBaseline** for the next cycle
