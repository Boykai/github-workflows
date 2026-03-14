# Research: Recurring Documentation Refresh Playbook

**Feature**: 040-doc-refresh-playbook
**Date**: 2026-03-14
**Status**: Complete

## Research Tasks

### R1: Baseline Storage Format — JSON File vs Git Tag

**Decision**: Use a JSON file at `docs/.last-refresh` containing `{"date": "YYYY-MM-DDTHH:MM:SSZ", "sha": "<commit-sha>", "documents_updated": [...]}`.

**Rationale**: The spec (Assumption 8) explicitly recommends JSON for queryability. A JSON file can be read programmatically by scripts, parsed by CI pipelines, and inspected manually. It also supports storing additional metadata (list of documents updated, summary statistics) that a git tag cannot carry. The file lives in `docs/` alongside the documentation it tracks, making the relationship self-evident.

The baseline file is committed to the repository so it survives branch merges and is available to all contributors. The file is updated atomically at the end of a successful refresh cycle (FR-017), ensuring partial refreshes do not corrupt the baseline.

**Alternatives considered**:

- **Git tag** (`docs-refresh-YYYY-MM-DD`): Simpler to create (`git tag`) but harder to query programmatically. Cannot store structured metadata. Multiple tags accumulate over time and clutter the tag namespace. Tags can be deleted accidentally.
- **Git notes**: Powerful but obscure — most contributors are unfamiliar with `git notes`. Not visible in standard GitHub UI.
- **Dedicated branch**: Overkill for a single metadata file. Adds branching complexity.

---

### R2: CHANGELOG Parsing Strategy

**Decision**: Parse CHANGELOG.md using section-header detection (lines matching `## [Unreleased]` or `## YYYY-MM-DD`) and category-header detection (lines matching `### Added`, `### Changed`, `### Removed`, `### Fixed`). Extract entries as bullet-point items between the last-refresh date and the current date.

**Rationale**: The repository CHANGELOG follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions (confirmed in CHANGELOG.md line 5). This means:

- Versions are delimited by `## [version]` or `## YYYY-MM-DD` headers
- Categories use `### Added`, `### Changed`, `### Removed`, `### Fixed` sub-headers
- Individual entries are markdown bullet points (`-`)

The `[Unreleased]` section captures changes that have landed but not been released yet — these are critical for the doc refresh since they represent the most recent drift. The parsing approach is simple line-by-line scanning that does not require a markdown AST parser.

**Alternatives considered**:

- **Full markdown parser** (e.g., Python `markdown-it` or `mistune`): More robust but introduces a dependency for a straightforward line-scanning task. The CHANGELOG format is consistent enough that regex/line matching suffices.
- **Git-based changelog generation** (e.g., `git log --format`): Does not capture the curated, human-written change descriptions. Commit messages are too granular and noisy for documentation purposes.

---

### R3: Code Diff Analysis — High-Churn File Detection

**Decision**: Use `git diff --stat <last-sha>..HEAD` for structural changes (added/deleted/renamed files) and `git log --oneline --since="<date>"` for commit volume. Surface files with >5 commits or >100 lines changed that are not already represented in the CHANGELOG.

**Rationale**: The two git commands provide complementary views:

- `git diff --stat` shows the net result: what files exist now that didn't before, what was renamed, what has the most churn
- `git log --oneline --since` shows the volume: frequently-touched files indicate active development even if the net diff is small

The threshold of >5 commits or >100 lines changed is a heuristic to filter noise. Files below these thresholds are unlikely to warrant documentation updates. The CHANGELOG cross-reference ensures we only surface undocumented changes — if a change is already in the CHANGELOG, the diff analysis confirms rather than duplicates it.

Key directories to monitor (from spec):

- `backend/src/api/` — new or changed endpoints
- `frontend/src/pages/` — new or changed pages/routes
- `backend/src/services/` — new or refactored services
- `backend/src/migrations/` — new database migrations
- `docker-compose.yml` — topology changes
- `backend/src/config.py` — configuration changes

**Alternatives considered**:

- **GitHub API (compare commits)**: Requires API access and authentication. The git CLI is simpler and works offline.
- **File-system `find -newer`**: Only detects modification time, not the nature of changes. Cannot identify renamed or deleted files.

---

### R4: Documentation-to-Source Mapping Registry

**Decision**: Maintain the documentation-to-source mapping as a static lookup table in the playbook itself (this plan and the quickstart guide). The mapping is small (11 entries per the spec) and changes infrequently.

**Rationale**: The spec (FR-012) requires maintaining a mapping of each documentation file to its source-of-truth. The current repository has exactly 11 documentation files with clear source-of-truth relationships:

| Documentation File | Source of Truth |
|---|---|
| `docs/api-reference.md` | `backend/src/api/` route files |
| `docs/architecture.md` | `backend/src/services/` + `docker-compose.yml` |
| `docs/agent-pipeline.md` | Pipeline/orchestrator service code |
| `docs/configuration.md` | `backend/src/config.py` |
| `docs/custom-agents-best-practices.md` | Agent MCP sync service + `.agent.md` files |
| `docs/project-structure.md` | Filesystem (`tree` output) |
| `docs/testing.md` | Test directories + `pyproject.toml` / `vitest.config.ts` |
| `docs/troubleshooting.md` | Recent bug fixes in Change Manifest |
| `docs/setup.md` | `pyproject.toml`, `package.json`, `docker-compose.yml` |
| `docs/signal-integration.md` | Signal-related backend code |
| `frontend/docs/findings-log.md` | Frontend audit results |

This mapping is stable — the documentation files and their sources do not change frequently. Encoding it in a configuration file or database would add unnecessary infrastructure for a 11-row static table.

**Alternatives considered**:

- **YAML/JSON config file** (e.g., `docs/.doc-mappings.yml`): Scriptable but adds a file to maintain. Worth considering when automation is implemented (after 2–3 manual cycles per spec Assumption 7).
- **Frontmatter in each doc file**: Would require modifying every doc file to add source-of-truth metadata. Invasive for minimal gain.

---

### R5: Change Manifest Format and Structure

**Decision**: The Change Manifest is a markdown document organized by the five categories defined in the spec: New features, Changed behavior, Removed functionality, Architectural shifts, and UX shifts. Each item includes a description, source attribution, and affected domain area.

**Rationale**: A markdown format is consistent with all other spec artifacts and is human-reviewable. The manifest is consumed by a human maintainer in Phase 2 (not by automated tooling in the initial manual cycles), so readability is paramount. The five-category structure directly mirrors the spec's FR-005 requirement.

Each manifest item includes:

- **Description**: What changed (1–2 sentences)
- **Source**: Where the change was detected — `CHANGELOG`, `specs/<dir>`, or `git diff <file>`
- **Domain**: Which area of the application is affected (pipeline, agents, chat, etc.)

Domain classification follows the list in FR-006: pipeline, agents, chat, projects, tools, settings, auth, signal, analytics, infra. Items affecting multiple domains are listed under the primary domain with cross-references.

**Alternatives considered**:

- **Structured JSON**: Machine-readable but harder for the maintainer to review and annotate. Better suited for automated phases (deferred to future automation work).
- **Spreadsheet/CSV**: Good for sorting and filtering but breaks markdown toolchain integration. Not version-controllable in a diff-friendly way.

---

### R6: Prioritization Algorithm — P0 through P3

**Decision**: Apply a rule-based prioritization using the criteria defined in the spec (FR-008):

| Priority | Trigger | Files |
|----------|---------|-------|
| **P0** | App pitch or primary workflow changed | `README.md` |
| **P1** | Docs directly affected by new/changed features | Feature-specific docs (e.g., `api-reference.md`, `agent-pipeline.md`) |
| **P2** | Modules added/removed/reorganized | Structural docs (`project-structure.md`, `architecture.md`) |
| **P3** | New config, errors, or test structure changed | Support docs (`troubleshooting.md`, `configuration.md`, `testing.md`) |

The evaluation is top-down: check P0 triggers first, then P1, P2, P3. A document can appear at multiple priority levels; it inherits the highest applicable priority.

**Rationale**: The spec's prioritization rules are explicit and deterministic — no ML or scoring model is needed. The rule-based approach is transparent (the maintainer can see exactly why a document was prioritized), auditable (the rules are documented in the plan and quickstart), and reproducible (two maintainers following the same rules will produce the same prioritization).

**Alternatives considered**:

- **Weighted scoring model**: Assigns numeric scores based on change volume, domain importance, and recency. More nuanced but harder to explain and debug. Overkill for a manual process with 11 documents.
- **LLM-based classification**: Could infer priority from change descriptions, but introduces non-determinism and requires API access. Deferred to the AI-assisted drafting consideration in the spec.

---

### R7: Cross-Reference Link Validation

**Decision**: Use `grep -rn '\[.*\](docs/' README.md docs/` to extract all internal documentation links, then verify each target path exists using a shell loop. Report broken links with file and line number.

**Rationale**: The spec (FR-013) requires validating all internal documentation links. The grep approach is simple, requires no dependencies, and works on any Unix system. The pattern `[text](docs/...)` captures all markdown links pointing to the `docs/` directory.

The validation loop checks:

1. Does the target file exist?
2. If the link includes an anchor (`#section-name`), does the target file contain a matching heading?

Anchor validation requires parsing markdown headings, which can be done with a second grep: `grep -i "^#.*section-name"`. This catches the common case of renamed or deleted sections.

The existing weekly sweep checklist (`docs/checklists/weekly-sweep.md`) includes a manual link check step — this automated grep replaces that manual step for the refresh cycle.

**Alternatives considered**:

- **markdown-link-check npm package**: The repo has a `.markdown-link-check.json` config file, indicating this tool may already be configured. However, it checks external links (HTTP) which is slower and not needed for internal-only validation. The grep approach is faster for internal links.
- **Custom Python script**: More robust anchor validation but adds a script dependency. Worth building when automation is implemented.

---

### R8: Mermaid Diagram Regeneration

**Decision**: Use the existing `scripts/generate-diagrams.sh` script to regenerate architecture diagrams when the Change Manifest includes architectural shifts.

**Rationale**: The script already exists in the repository and generates 5 Mermaid diagram files in `docs/architectures/`:

- `high-level.mmd`
- `deployment.mmd`
- `frontend-components.mmd`
- `backend-components.mmd`
- `data-flow.mmd`

The trigger for regeneration is the presence of items in the "Architectural shifts" category of the Change Manifest. If no architectural changes are detected, diagram regeneration is skipped to avoid unnecessary churn.

**Alternatives considered**:

- **Manual diagram editing**: Error-prone and inconsistent. The script ensures diagrams match the codebase.
- **CI-triggered generation**: Already in place (per CHANGELOG entry "Automated Mermaid architecture diagram generation via CI and commit hooks") but the refresh cycle may need to explicitly invoke it if changes are made outside CI.
