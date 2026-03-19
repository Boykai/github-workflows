---
name: Librarian
about: Recurring chore — update documentation assets to ensure accuracy relative to application
title: '[CHORE] Librarian'
labels: chore
assignees: ''
---

## Librarian

A repeatable process for keeping project documentation accurate as software evolves. Language-agnostic, structure-agnostic, applicable to any codebase. Detects what changed, infers how the product's focus shifted, and rewrites docs to match reality.

---

### Principles

- **Docs describe reality, not intent** — documentation should reflect what the app does *now*, not what was planned
- **Source code is the single source of truth** — every doc claim must be traceable to running code
- **Detect drift, don't assume accuracy** — always diff docs against code; never trust that "nothing changed"
- **Shift the narrative with the product** — as features rise or fall in importance, docs should reorder and re-emphasize accordingly

---

### Phase 1 — Build the Change Manifest

> Goal: Catalog everything that changed since the last refresh.

**1.1 — Establish the baseline**
- Retrieve the last refresh marker (git tag, metadata file, or last known good commit SHA)
- If no baseline exists, use the last release tag or a reasonable time window (e.g., 2 weeks)

**1.2 — Harvest from structured sources**
- Parse the changelog (e.g., `CHANGELOG.md`, GitHub Releases, or equivalent) for Added/Changed/Removed/Fixed entries since baseline
- Scan any feature spec, RFC, or ADR directories for new or updated proposals

**1.3 — Harvest from code diffs**
- Run `git diff --stat <baseline>..HEAD` to identify files with significant churn
- Run `git log --oneline --since=<baseline>` for a commit-level view
- Flag high-signal changes:
  - New or deleted **entry points** (routes, endpoints, CLI commands, event handlers)
  - New or deleted **public-facing modules** (pages, screens, exports, plugins)
  - Changes to **configuration schemas** (env vars, config files, feature flags)
  - Changes to **dependency manifests** (new deps, major version bumps, removed deps)
  - Changes to **data models / schemas / migrations**
  - Changes to **build or deployment scripts**

**1.4 — Compile the manifest**
Categorize all findings into:

| Category | What to look for |
|----------|-----------------|
| **New capabilities** | New user-facing features, pages, commands, integrations |
| **Changed behavior** | Altered workflows, renamed concepts, changed defaults |
| **Removed functionality** | Deleted features, deprecated APIs, removed UI |
| **Architectural changes** | New services, refactored module boundaries, changed infra |
| **UX changes** | Navigation changes, renamed screens, altered user flows |
| **Config / ops changes** | New env vars, changed deployment steps, new dependencies |

---

### Phase 2 — Infer Focus Shifts

> Goal: Understand *how the product has evolved*, not just what lines changed.

**2.1 — Measure change density by domain**
- Group manifest items by functional area (e.g., auth, data pipeline, editor, API, admin, analytics)
- Domains with the most entries represent the current development focus

**2.2 — Detect narrative-level shifts**
Answer these questions from the manifest:
- Has a **new top-level capability** been added that deserves prominent mention?
- Has a previously prominent feature been **reduced, removed, or folded into another**?
- Has the product's **primary value proposition** shifted? (e.g., from "data viewer" to "data editor")
- Has the **primary user workflow** changed? (different starting point, different happy path)
- Have **new user personas** been introduced? (e.g., admin panel added → admin persona)

**2.3 — Prioritize updates**

| Priority | Trigger | What to update |
|----------|---------|----------------|
| **P0** | Product pitch or primary workflow changed | Top-level README, landing page of docs |
| **P1** | Feature added/changed/removed | Feature-specific docs, API reference, guides |
| **P2** | Architecture or structure changed | Architecture docs, directory/module maps |
| **P3** | Config, setup, or ops changed | Setup guides, config reference, deployment docs |
| **P4** | Bugs fixed or edge cases resolved | Troubleshooting, FAQ, known issues |

---

### Phase 3 — Update the README

> Goal: The README is the storefront. It must reflect the current product accurately.

**3.1 — Revalidate the project description**
- Does the one-liner / elevator pitch still describe what the product does today?
- If a narrative shift was detected in Phase 2, rewrite the description

**3.2 — Audit the feature list**
- Add newly shipped capabilities
- Remove or mark deprecated features
- Reorder by current importance (most-used or most-differentiated first)

**3.3 — Verify getting-started instructions**
- Run the quickstart from scratch in a clean environment (container, fresh clone, or CI)
- Check prerequisite versions against current dependency manifests
- Validate that all commands produce the expected output

**3.4 — Update visual / structural references**
- Replace outdated screenshots, diagrams, or GIFs if the UI changed
- Update architecture-at-a-glance diagrams if topology changed
- Verify all badge URLs and status links still resolve

---

### Phase 4 — Update Documentation Files

> Goal: Each doc page is accurate to the current codebase and UX.

**4.1 — Map each doc to its source of truth**

Every documentation page should have an explicit source-of-truth mapping. Common patterns:

| Doc Type | Source of Truth | How to Diff |
|----------|----------------|-------------|
| API reference | Route/controller/handler definitions | List all endpoints in code → compare to doc |
| Configuration reference | Config schema / env var definitions | Extract all config keys from code → compare to doc |
| Architecture overview | Service/module structure + infra config | List top-level modules + deployment topology → compare to doc |
| Setup / installation | Dependency manifests + build scripts | Run setup steps → note any failures or drift |
| Feature guides | Feature implementation code + UI | Walk the feature in the running app → compare to doc |
| CLI reference | Command definitions / argument parsers | Run `--help` output → compare to doc |
| Data model reference | Schema definitions / migrations | Export current schema → compare to doc |
| Troubleshooting | Recent bug fixes + support tickets | Review closed bugs → add new entries, prune resolved ones |

**4.2 — For each affected doc (based on Phase 2 priorities):**
1. Read the current doc
2. Diff against its source of truth
3. Identify gaps: **missing** (new things not documented), **stale** (documented things that changed), **dead** (documented things that no longer exist)
4. Rewrite affected sections — don't patch; rewrite the section to read naturally
5. If a narrative shift occurred, adjust the doc's framing and emphasis accordingly

**4.3 — Structural docs**
- Regenerate module/directory maps from the actual filesystem
- Update dependency graphs or architecture diagrams from current code
- Verify all code examples compile/run against current codebase

---

### Phase 5 — Validate Consistency

> Goal: Docs are internally consistent and all references resolve.

**5.1 — Link validation**
- Check all internal cross-references between doc files (automated: `markdown-link-check`, `lychee`, or equivalent)
- Check all external URLs still resolve (automated with same tools)
- Verify all anchor links point to existing headings

**5.2 — Terminology audit**
- Grep docs for renamed concepts (from the change manifest) — replace old names with new
- Ensure consistent naming across README and all doc files (e.g., don't call it "Pipeline" in one doc and "Workflow" in another unless intentional)

**5.3 — Diagram freshness**
- Regenerate any auto-generated diagrams (Mermaid, PlantUML, D2, etc.)
- Manually verify non-generated diagrams still match reality

**5.4 — Code sample validation**
- Extract embedded code snippets and verify they compile/run
- Or: run doc-test frameworks if available (`doctest`, `mdx-js`, `rustdoc`, etc.)

---

### Phase 6 — Verify Against the Running Application

> Goal: Docs match the actual user experience, not just the code.

**6.1 — Smoke-test documented workflows**
- Pick 3–5 key user flows described in docs
- Walk each flow in the running application
- Verify: screen names, navigation paths, button labels, terminology, expected outcomes all match docs

**6.2 — Verify config and setup docs**
- Confirm all documented env vars / config keys are recognized by the application
- Confirm default values in docs match actual defaults

**6.3 — Verify API docs (if applicable)**
- Hit 3–5 documented endpoints and confirm request/response shapes match docs
- Or: compare against auto-generated OpenAPI/Swagger spec

---

### Phase 7 — Stamp & Reset Baseline

> Goal: Record the refresh so the next cycle starts clean.

**7.1 — Commit documentation changes**
- Commit all doc updates in a single, well-described commit (or PR)
- Use a conventional commit message: `docs: refresh documentation for <period>`

**7.2 — Update the changelog**
- Add a Documentation section noting which docs were updated and key changes

**7.3 — Set the new baseline**
- Tag the commit: `docs-refresh-YYYY-MM-DD` or update a metadata file with the SHA + date
- This becomes the starting point for the next cycle's Phase 1

---

### Automation Opportunities

Start manual. Automate incrementally after 2–3 cycles validate the process.

| Step | Automation Approach |
|------|-------------------|
| Change manifest generation (1.2–1.4) | Script that parses changelog + `git log` + `git diff --stat` into a structured report |
| Link validation (5.1) | CI job running `lychee`, `markdown-link-check`, or `linkinator` |
| Code sample validation (5.4) | Doc-test frameworks (`doctest`, `mdx`, `rustdoc`) in CI |
| Stale config detection (4.1) | Script that extracts config keys from code and diffs against config docs |
| Endpoint drift detection (4.1) | Script that extracts routes from code and diffs against API reference |
| Terminology consistency (5.2) | Custom linter rule or grep script for deprecated term → replacement mapping |
| Diagram generation (5.3) | Build step that regenerates diagrams from source files |

---

### Anti-Patterns to Avoid

- **Patching instead of rewriting** — Don't append "UPDATE: this changed" notes. Rewrite the section so it reads as if it was always correct.
- **Documenting aspirations** — Don't document planned features. Docs describe the current release.
- **Orphan docs** — Every doc should be reachable from the README or a docs index. Unreachable docs rot fastest.
- **Screenshot graveyards** — Screenshots go stale instantly. Prefer text descriptions of UI flows; use screenshots sparingly and regenerate them.
- **Copy-paste config tables** — Generate config references from code when possible, or at minimum diff against code each cycle.

---

### Cadence & Ownership

| Cadence | Activity | Owner |
|---------|----------|-------|
| Per-PR | Author updates docs affected by their change | PR author |
| Bi-weekly | Full refresh (this playbook) | Rotating team member |
| Per-release | Changelog entry + README audit for pitch accuracy | Release manager |

---

### Verification Checklist (End of Each Refresh)

- [ ] Change manifest accounted for all commits since last baseline
- [ ] All internal doc links resolve
- [ ] All documented features exist in the running application
- [ ] All config keys in docs exist in the config schema
- [ ] Getting-started guide runs clean from a fresh environment
- [ ] No references to removed features remain in docs
- [ ] README feature list matches current capabilities in priority order
- [ ] New baseline (tag or metadata) is set for next cycle
- [ ] Changelog updated with documentation changes
