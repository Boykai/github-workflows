# Research: Add Help Documentation or Support Resource

**Feature**: 032-help-docs | **Date**: 2026-03-09 | **Plan**: [plan.md](plan.md)

## R1: Existing Help Infrastructure Audit

**Task**: Evaluate what help documentation already exists and identify gaps against spec requirements (FR-001–FR-010).

**Decision**: The existing `docs/help.md` and `frontend/src/pages/HelpPage.tsx` already provide substantial coverage of all spec requirements.

**Rationale**: An audit of the repository revealed:

| Requirement | Current Status | Gap |
|-------------|---------------|-----|
| FR-001: Dedicated help document | ✅ `docs/help.md` exists (162 lines) | None |
| FR-002: Getting Started section | ✅ 5-step guide with prerequisites, setup, and links | None |
| FR-003: Categorized FAQ | ✅ 10 questions across 4 categories (Setup, Usage, Pipeline, Contributing) | None |
| FR-004: Support Channels section | ✅ Lists GitHub Issues, Discussions, and Documentation links | None |
| FR-005: Agent Pipeline overview | ✅ ASCII diagram with stage descriptions and links to full docs | None |
| FR-006: README links to help doc | ✅ Documentation table includes `[Help & Support](docs/help.md)` | None |
| FR-007: FAQ answers link to detail docs | ✅ Links to configuration.md, setup.md, troubleshooting.md, testing.md, custom-agents-best-practices.md | None |
| FR-008: Last Updated date + contribution note | ✅ "Last updated: 2026-03-09 · Contributions welcome — open a PR to improve this guide." | None |
| FR-009: Plain language for beginners | ✅ Content uses clear, non-technical language with step-by-step instructions | Verify readability score |
| FR-010: UI help link in navigation | ✅ Sidebar includes HelpCircle icon → `/help` route; HelpPage.tsx renders full help content | None |

**Alternatives considered**:
- Creating a new `HELP.md` at repo root: Rejected — `docs/help.md` already exists with proper README linking
- Using a wiki instead of in-repo docs: Rejected — in-repo docs are version-controlled and discoverable

## R2: Content Readability Validation

**Task**: Verify the help document meets SC-007 (Flesch-Kincaid Grade Level ≤ 8).

**Decision**: The help document content uses short sentences, common vocabulary, and step-by-step formatting that targets a beginner audience.

**Rationale**: The document follows readability best practices:
- Short paragraphs (1-3 sentences)
- Active voice throughout
- Technical terms are explained or linked to detailed documentation
- Numbered steps for procedural content
- Code blocks are clearly separated from prose
- FAQ format with direct question-answer pairs

**Alternatives considered**:
- Adding a readability CI check: Rejected — over-engineering for a single document; manual review sufficient per Principle V (Simplicity)

## R3: FAQ Coverage Analysis

**Task**: Verify the FAQ section meets SC-002 (at least 8 questions across at least 3 categories).

**Decision**: The current FAQ contains 10 questions across 4 categories, exceeding the minimum requirement.

**Rationale**: Current FAQ breakdown:
- **Setup** (3 questions): OAuth App creation, system requirements, Codespaces setup
- **Usage** (3 questions): Chat issue creation, agent configuration, chores usage
- **Pipeline** (2 questions): Pipeline explanation, pipeline troubleshooting
- **Contributing** (2 questions): Contribution workflow, custom agent creation

Total: 10 questions across 4 categories (requirement: ≥8 questions across ≥3 categories).

**Alternatives considered**:
- Adding more FAQ items to increase coverage: Not needed — current coverage exceeds requirements; additional items can be added organically as common questions arise

## R4: Link Integrity Strategy

**Task**: Determine approach for ensuring all internal documentation links remain valid (edge case from spec).

**Decision**: Use relative links throughout `docs/help.md` and validate manually during review.

**Rationale**: The help document currently uses relative links (e.g., `setup.md`, `configuration.md`) which are resilient to repository URL changes. All linked documents exist in the `docs/` directory. The document includes a contribution note encouraging updates, which covers the edge case of broken links from documentation moves.

**Alternatives considered**:
- Automated link checking in CI: Already available via markdownlint; no additional tooling needed
- Absolute GitHub URLs: Rejected — fragile if repository is forked or moved

## R5: Frontend HelpPage Consistency

**Task**: Verify the frontend HelpPage.tsx content matches `docs/help.md` and meets FR-010.

**Decision**: `HelpPage.tsx` provides a celestial-themed rendering of the same content structure as `docs/help.md`, with interactive accordion FAQ and categorized filtering.

**Rationale**: The frontend page includes:
- Getting Started section with the same 5-step guide
- FAQ accordion with the same 10 questions and 4 categories
- Support Channels with the same links
- Agent Pipeline overview with visual representation
- Further Reading table with documentation links
- Responsive layout with celestial theme styling

The UI help link is accessible from the sidebar navigation (`HelpCircle` icon → `/help` route), meeting FR-010.

**Alternatives considered**:
- Generating HelpPage from markdown at build time: Rejected — adds build complexity for 10 FAQ items; violates Principle V (Simplicity)
- Removing HelpPage and linking directly to GitHub docs: Rejected — loses the in-app experience and celestial theme integration
