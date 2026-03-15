# Data Model: Audit Pipelines Page for UI Consistency, Quality & UX

**Feature**: 033-audit-pipelines-ux | **Date**: 2026-03-10

## Audit Entities

### Audit Finding

The primary entity representing a single issue discovered during the audit. This maps directly to the "Audit Finding" Key Entity defined in the spec. Findings are documented in `audit-report.md` and tracked through remediation.

**Fields**:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique identifier (format: `PIPE-NNN`) | `PIPE-004` |
| `severity` | enum | Impact level: Critical, High, Medium, Low | `Medium` |
| `category` | enum | Audit category (see categories below) | `Accessibility` |
| `status` | enum | Current state: Open, Fixed, Deferred | `Open` |
| `description` | string | What was found | "Pipeline name validation feedback is visual-only" |
| `affected_files` | string[] | Source file paths | `["frontend/src/components/pipeline/PipelineBoard.tsx"]` |
| `wcag_mapping` | string[] | WCAG 2.1 success criteria (a11y findings only) | `["3.3.1", "4.1.2"]` |
| `reproduction_steps` | string[] | How to reproduce (bug findings) | `["1. Open pipeline", "2. Clear name", "3. Tab away"]` |
| `expected_behavior` | string | What should happen | "Input exposes aria-invalid and aria-describedby" |
| `actual_behavior` | string | What currently happens | "Error shown visually but not announced to AT" |
| `remediation` | string | Recommended fix | "Add aria-invalid and aria-describedby to name input" |

**Validation Rules**:

- `id` must be unique across all findings
- `severity` must be one of: Critical, High, Medium, Low
- `category` must be one of the five audit categories
- `status` must be one of: Open, Fixed, Deferred
- `affected_files` must contain at least one file path
- `wcag_mapping` is required only when `category` is "Accessibility"
- `reproduction_steps` is required only when `category` is "Functional bug"

### Audit Category (Enum)

| Value | Spec Reference | Description |
|-------|---------------|-------------|
| `Visual consistency` | User Story 1 (P1) | Design token deviations, cross-page pattern mismatches |
| `Functional bug` | User Story 2 (P1) | Broken interactions, missing state handling, data loss risks |
| `Accessibility` | User Story 3 (P2) | WCAG 2.1 AA violations, keyboard/screen reader gaps |
| `UX quality` | User Story 4 (P2) | Information hierarchy, responsiveness, interaction feedback |
| `Code quality` | User Story 5 (P3) | Pattern violations, console errors, DRY/reusability issues |

### Severity Level (Enum)

Severity criteria as defined in FR-010:

| Level | Criteria | Example |
|-------|----------|---------|
| `Critical` | Blocks core functionality or causes data loss | Hero CTA bypassing unsaved-change protection (PIPE-001, fixed) |
| `High` | Significantly degrades user experience | Unsaved work loss from prominent action (PIPE-001, fixed) |
| `Medium` | Noticeable issue but has a workaround | Validation feedback not announced to AT (PIPE-004) |
| `Low` | Cosmetic or minor improvement | Generic skeleton styling (PIPE-005), activity capping (PIPE-006) |

### Audit Report

The consolidated deliverable entity containing all findings. Maps to the "Audit Report" Key Entity in the spec.

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Audit date (ISO 8601) |
| `scope` | string | Page and components audited |
| `reviewer` | string | Who conducted the audit |
| `comparison_baseline` | string | Reference pages/patterns used for comparison |
| `executive_summary` | string | High-level summary of findings |
| `findings` | AuditFinding[] | All findings, grouped by category and sorted by severity |
| `total_by_severity` | Record<Severity, number> | Count per severity level |
| `total_by_category` | Record<Category, number> | Count per audit category |
| `remediation_roadmap` | RemediationItem[] | Prioritized list of fixes |

## Frontend Component Models (Existing — Audit Targets)

### Pipeline Validation State

The validation state model used by `PipelineBoard.tsx` for the pipeline name input. This is the component modified for PIPE-004 remediation.

```typescript
// Existing type from usePipelineConfig hook
interface PipelineValidationErrors {
  name?: string;       // Error message for pipeline name
  stages?: string;     // Error message for stages
  [key: string]: string | undefined;
}
```

**PIPE-004 Remediation — New Attributes on Name Input**:

| Attribute | When Applied | Value |
|-----------|-------------|-------|
| `aria-invalid` | `validationErrors.name` is truthy | `"true"` |
| `aria-describedby` | `validationErrors.name` is truthy | `"pipeline-name-error"` |
| `id` on error `<p>` | Always (hidden when no error) | `"pipeline-name-error"` |

### SavedWorkflowsList Loading State

The loading skeleton model for `SavedWorkflowsList.tsx`. This is the component modified for PIPE-005 remediation.

```typescript
// Existing props
interface SavedWorkflowsListProps {
  pipelines: PipelineConfigSummary[];
  isLoading: boolean;          // Controls skeleton display
  activePipelineId?: string;
  assignedPipelineId?: string;
  onSelect: (id: string) => void;
  onAssign?: (id: string) => void;
}
```

**PIPE-005 Remediation — Skeleton Upgrade**:

| Current | Proposed |
|---------|----------|
| `h-32 rounded-xl border-border/50 bg-muted/20 animate-pulse` | Structured card skeleton with header, body, and stats placeholders using `celestial-panel` border treatment |

### Recent Activity Display

The recent activity section in `AgentsPipelinePage.tsx`. Modified for PIPE-006 remediation.

**PIPE-006 Remediation — Overflow Indicator**:

| Condition | Display |
|-----------|---------|
| `totalPipelines <= 3` | No change (show all) |
| `totalPipelines > 3` | Add text: "Showing 3 of {total} — see all in Saved Pipelines" with anchor link to `#saved-pipelines` |

## State Transitions

### Audit Finding Lifecycle

```text
[Discovered] → Open
     │
     ├── [Fix applied + verified] → Fixed
     │
     └── [Justified deferral] → Deferred
```

- **Open → Fixed**: Remediation code is implemented, tested, and verified
- **Open → Deferred**: Finding is documented with justification for deferral (e.g., requires design system changes beyond this audit's scope)

### Pipeline Name Validation State (PIPE-004 Context)

```text
[Input focused] → Editing
     │
     ├── [Valid name entered] → Valid (border-primary/30, no error)
     │
     ├── [Empty/invalid name] → Invalid (border-red-500, aria-invalid="true", error shown)
     │
     └── [Escape pressed] → Reverted (original name restored)
```
