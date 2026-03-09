# Data Model: Add Help Documentation or Support Resource

**Feature**: 032-help-docs | **Date**: 2026-03-09 | **Plan**: [plan.md](plan.md)

## Entities

### Help Document

The primary help resource file containing structured sections for user guidance.

| Field | Type | Description |
|-------|------|-------------|
| title | string | Document heading ("Help & Support") |
| lastUpdated | date (ISO 8601) | Date of last content update |
| contributionNote | string | Encouragement for contributors to keep content current |
| sections | Section[] | Ordered list of content sections |

**Location**: `docs/help.md`

### Section

A top-level content area within the help document.

| Field | Type | Description |
|-------|------|-------------|
| heading | string | Section title (e.g., "Getting Started", "Frequently Asked Questions") |
| content | markdown | Section body content |
| subsections | Subsection[] | Optional nested content areas |

**Sections defined in spec**:
1. Getting Started (FR-002)
2. Frequently Asked Questions (FR-003)
3. Support Channels (FR-004)
4. Agent Pipeline Overview (FR-005)
5. Further Reading (FR-007)

### FAQ Entry

An individual question-and-answer pair within the FAQ section.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| category | enum | One of: "Setup", "Usage", "Pipeline", "Contributing" | Required; must be one of the 4 defined categories |
| question | string | The user question in plain language | Required; must end with "?" |
| answer | string | Concise answer with optional links to detailed docs | Required; must be actionable |
| detailLink | string (URL) | Optional relative link to detailed documentation page | Must be a valid relative path to an existing `docs/` file |

**Validation rules**:
- FAQ section must contain ≥ 8 entries (SC-002)
- FAQ entries must span ≥ 3 categories (SC-002)
- All `detailLink` values must resolve to existing documentation files (SC-003)

### Frontend FAQ Item (TypeScript)

The TypeScript interface used in `HelpPage.tsx` to render FAQ content.

```typescript
interface FaqItem {
  question: string;
  answer: string;
  category: 'Setup' | 'Usage' | 'Pipeline' | 'Contributing';
}
```

**Current implementation**: `frontend/src/pages/HelpPage.tsx` defines `FAQ_ITEMS: FaqItem[]` with 10 entries matching the `docs/help.md` content.

## Relationships

```text
Help Document (docs/help.md)
├── Getting Started Section
│   └── Links to: setup.md, configuration.md
├── FAQ Section
│   ├── Setup Questions → Links to: configuration.md, setup.md
│   ├── Usage Questions → Links to: (inline answers)
│   ├── Pipeline Questions → Links to: troubleshooting.md
│   └── Contributing Questions → Links to: testing.md, custom-agents-best-practices.md
├── Support Channels Section
│   └── Links to: GitHub Issues, GitHub Discussions, README
├── Pipeline Overview Section
│   └── Links to: agent-pipeline.md
└── Further Reading Section
    └── Links to: All docs/*.md files

Frontend HelpPage (HelpPage.tsx)
├── Mirrors: Help Document content
├── Renders: FAQ accordion with category filter
└── Navigation: Sidebar HelpCircle icon → /help route
```

## State Transitions

This feature has no state transitions. The help document is static content that is updated manually by contributors. The "Last Updated" date (FR-008) is maintained through the standard PR review process.
