# Data Model: Deep UX/UI Review, Polish & Meaningful Frontend Test Coverage

**Feature**: 014-ux-ui-review-testing | **Date**: 2026-02-28

> This feature does not introduce new application data entities. The "entities" below describe the conceptual artifacts produced and consumed during the UX/UI audit, polish, and test coverage process.

## Entity: Findings Log Entry

**Purpose**: A single issue discovered during the UX/UI review, driving all fix and regression work.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string | Unique identifier (e.g., `F-001`) | Required, sequential |
| category | enum | `visual-consistency` \| `accessibility` \| `interactive-state` \| `form-validation` \| `ui-state` \| `responsive` \| `content-integrity` \| `performance` | Required |
| severity | enum | `critical` \| `major` \| `minor` \| `cosmetic` | Required |
| affected_view | string | Customer-facing view where the issue appears | Required (Home, Board, Settings) |
| affected_component | string | Specific component name | Required |
| description | string | Clear description of the issue | Required, non-empty |
| expected_behavior | string | What the correct behavior should be | Required |
| status | enum | `open` \| `fixed` \| `wont-fix` | Required, default: `open` |
| regression_test | string | Path to regression test file (if applicable) | Required when status is `fixed` |
| requirement_ref | string | Spec requirement this finding maps to | Required (e.g., FR-001) |

**Validation Rules**:
- Every finding must map to at least one spec requirement (FR-001 through FR-013)
- `critical` and `major` findings must be resolved (`fixed` or justified `wont-fix`) before the feature is considered complete
- `fixed` findings must have a corresponding `regression_test` path

---

## Entity: Design Token

**Purpose**: A centralized visual value used across the application, tracked to ensure no hardcoded alternatives exist.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| token_name | string | CSS variable name (e.g., `--primary`) | Required, unique |
| value_light | string | HSL value in light theme | Required |
| value_dark | string | HSL value in dark theme | Required |
| category | enum | `color` \| `spacing` \| `typography` \| `radius` | Required |
| tailwind_class | string | Corresponding Tailwind utility class | Required (e.g., `bg-primary`) |
| usage_count | number | Number of components using this token | Informational |

**Current Design Tokens** (from `index.css`):
- 11 color tokens (background, foreground, primary, secondary, destructive, muted, accent, popover, card, border, input, ring)
- 1 radius token (`--radius`)
- Typography via Tailwind config (Inter font family)

**Validation Rules**:
- No component may use hardcoded color values (hex, rgb, hsl) — must reference tokens via Tailwind classes
- No component may use hardcoded spacing outside Tailwind's spacing scale
- No component may use hardcoded font-family, font-size, or font-weight outside Tailwind utilities

---

## Entity: UI Component Audit Record

**Purpose**: Audit status of each customer-facing component, tracking compliance with visual, interactive, and accessibility standards.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| component_path | string | File path relative to `frontend/src/` | Required |
| component_name | string | Component display name | Required |
| visual_consistency | enum | `pass` \| `fail` \| `n/a` | Required |
| interactive_states | enum | `pass` \| `fail` \| `n/a` | Required (`n/a` for non-interactive) |
| accessibility | enum | `pass` \| `fail` \| `n/a` | Required |
| ui_states | enum | `pass` \| `fail` \| `n/a` | Required (`n/a` for non-data components) |
| form_validation | enum | `pass` \| `fail` \| `n/a` | Required (`n/a` for non-form components) |
| responsive | enum | `pass` \| `fail` \| `n/a` | Required |
| test_coverage | enum | `covered` \| `uncovered` \| `partial` | Required |
| findings | list[string] | Finding IDs linked to this component | Optional |

**Component Categories**:
- **UI Primitives** (3): button, card, input
- **Board** (11): BoardColumn, IssueCard, AgentConfigRow, CreateIssueModal, IssueDetailModal, etc.
- **Chat** (6): ChatInterface, ChatMessage, ChatPopup, etc.
- **Settings** (12): SettingsSection, McpSettings, GlobalSettings, etc.
- **Auth** (2): LoginButton, LoginButton.test
- **Common** (2): ErrorBoundary, ErrorBoundary.test
- **Pages** (2): ProjectBoardPage, SettingsPage
- **Theme** (1): ThemeProvider

---

## Entity: Test Coverage Record

**Purpose**: Tracks which critical user flows have automated test coverage.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| flow_name | string | Name of the user flow | Required |
| flow_type | enum | `navigation` \| `form-submission` \| `data-display` \| `authentication` \| `real-time` | Required |
| test_type | enum | `unit` \| `integration` \| `e2e` | Required |
| test_file | string | Path to test file | Required |
| query_approach | enum | `by-role` \| `by-label` \| `by-text` \| `by-testid` | Required; `by-role` or `by-label` preferred |
| user_story_ref | string | Spec user story this test validates | Required |

**Critical User Flows**:
1. Authentication (login/logout via GitHub OAuth)
2. Project selection (dropdown → board reload)
3. Board navigation (view columns, view issue details)
4. Chat interaction (send message → receive response → confirm/reject proposal)
5. Settings management (change settings → save → success/error feedback)
6. Form submission (MCP creation, agent config save)
7. Real-time sync (board updates via WebSocket/polling)

**Validation Rules**:
- Every critical user flow must have at least one test record
- Tests must use behavior-driven queries (getByRole, getByLabelText preferred over getByTestId)
- Snapshot tests require documented justification

---

## Relationships

```
Findings Log Entry *──1 UI Component Audit Record  (findings discovered during component audit)
Findings Log Entry 1──0..1 Test Coverage Record      (fixed findings get regression tests)
UI Component Audit Record 1──* Test Coverage Record  (components may have multiple test records)
Design Token *──* UI Component Audit Record           (tokens used by components)
```

## State Transitions

### Findings Lifecycle
```
discovered → [log entry created] → open
  open + critical/major → [fix applied] → fixed (regression test required)
  open + minor/cosmetic → [fix applied] → fixed (regression test recommended)
  open → [justified] → wont-fix (rationale required)
```

### Component Audit Lifecycle
```
unaudited → [visual review] → visual_checked
  → [interactive state review] → interactive_checked
  → [a11y audit] → accessibility_checked
  → [state handling review] → states_checked
  → [responsive review] → fully_audited
  → [tests added] → covered
```
