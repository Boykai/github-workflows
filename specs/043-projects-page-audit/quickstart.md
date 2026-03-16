# Quickstart: Projects Page Audit

**Feature**: `043-projects-page-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Node.js 22+ with `npm`
- Git repository cloned with full history
- Access to `solune/frontend/` directory

## Setup

### Frontend Environment

```bash
cd solune/frontend
npm ci
```

No new dependencies are required for this audit — all changes use the existing dependency set.

## Development Workflow

### Running the Dev Server

```bash
cd solune/frontend
npm run dev
```

The development server starts at `http://localhost:5173` with hot module replacement. Navigate to `/projects` to see the Projects page.

### Running Tests

```bash
cd solune/frontend

# Run all unit tests
npx vitest run

# Run tests in watch mode (recommended during development)
npx vitest

# Run project-related tests only
npx vitest run src/pages/ProjectsPage
npx vitest run src/hooks/useProjectBoard
npx vitest run src/hooks/useProjects
npx vitest run src/hooks/useBoardControls
npx vitest run src/hooks/useBoardRefresh
npx vitest run src/components/board/

# Run tests matching a pattern
npx vitest run --reporter=verbose board
npx vitest run --reporter=verbose project
```

### Type Checking

```bash
cd solune/frontend
npm run type-check
```

### Linting

```bash
cd solune/frontend
npm run lint

# Lint specific files
npx eslint src/pages/ProjectsPage.tsx src/components/board/
```

### Building

```bash
cd solune/frontend
npm run build
```

## Implementation Guide

### Phase 2: Page Decomposition

#### Step 1: Extract `ProjectSelector.tsx`

**File**: `solune/frontend/src/components/board/ProjectSelector.tsx`

Extract the project selector dropdown from `ProjectsPage.tsx` (~lines 170–270). This component renders:

1. A dropdown trigger showing the selected project name (or "Select a project" placeholder)
2. A searchable list of available projects
3. Project metadata (owner, type badge, item count) per list item
4. Selection callback to the parent

```tsx
// Component signature
interface ProjectSelectorProps {
  projects: BoardProject[];
  selectedProject: BoardProject | null;
  onSelect: (projectId: string) => void;
  isLoading: boolean;
}

export function ProjectSelector({ projects, selectedProject, onSelect, isLoading }: ProjectSelectorProps) {
  // Internal state: search query, dropdown open/closed
  // Renders: dropdown trigger, filtered project list
}
```

#### Step 2: Extract `PipelineSelector.tsx`

**File**: `solune/frontend/src/components/board/PipelineSelector.tsx`

Extract the pipeline selector and agent grid section from `ProjectsPage.tsx` (~lines 450–580). This component renders:

1. A dropdown to select/assign a pipeline to the project
2. A grid showing pipeline columns with agent dots
3. Agent assignment display per column
4. Mutation logic for pipeline assignment

```tsx
// Component signature
interface PipelineSelectorProps {
  projectId: string;
  boardData: BoardDataResponse | null;
  availableAgents: Agent[];
}

export function PipelineSelector({ projectId, boardData, availableAgents }: PipelineSelectorProps) {
  // Internal state: selector open/closed, pipeline list query, assignment mutation
  // Renders: dropdown, pipeline grid, agent dots
}
```

#### Step 3: Extract `BoardHeader.tsx`

**File**: `solune/frontend/src/components/board/BoardHeader.tsx`

Extract the board header section from `ProjectsPage.tsx` (~lines 280–380). This component renders:

1. Project name as a heading
2. Sync status indicator (connected/disconnected/syncing)
3. Refresh button with `<RefreshButton>` component
4. Last updated timestamp

```tsx
// Component signature
interface BoardHeaderProps {
  projectName: string;
  syncStatus: 'connected' | 'disconnected' | 'syncing';
  lastUpdated: Date | null;
  syncLastUpdate: Date | null;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export function BoardHeader({ projectName, syncStatus, lastUpdated, syncLastUpdate, onRefresh, isRefreshing }: BoardHeaderProps) {
  // Pure presentation — no internal state or queries
}
```

#### Step 4: Extract `RateLimitBanner.tsx`

**File**: `solune/frontend/src/components/board/RateLimitBanner.tsx`

Extract the rate limit warning section from `ProjectsPage.tsx` (~lines 380–430). This component renders:

1. A warning banner when rate limit is low or exhausted
2. Reset countdown using `formatTimeUntil()`
3. A message explaining the rate limit situation

```tsx
// Component signature
interface RateLimitBannerProps {
  rateLimitInfo: RateLimitInfo | null;
  isLow: boolean;
}

export function RateLimitBanner({ rateLimitInfo, isLow }: RateLimitBannerProps) {
  // Pure presentation — no internal state or queries
  // Renders conditionally based on isLow flag
}
```

### Phase 3: States & Error Handling

#### Error State Pattern

For API errors, use this consistent format (FR-026):

```tsx
{error && (
  <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
    <TriangleAlert className="h-8 w-8 text-destructive" aria-hidden="true" />
    <div>
      <p className="text-sm font-medium text-foreground">
        Could not load board data.
      </p>
      <p className="text-sm text-muted-foreground">
        {isRateLimitApiError(error)
          ? `GitHub API rate limit exceeded. Resets ${formatTimeUntil(extractRateLimitInfo(error)?.reset)}.`
          : 'An unexpected error occurred. Please try again.'}
      </p>
    </div>
    <Button variant="outline" size="sm" onClick={onRetry}>
      Try Again
    </Button>
  </div>
)}
```

### Phase 4: Accessibility

#### ARIA Pattern for Custom Dropdowns

For the project and pipeline selector dropdowns:

```tsx
<div role="combobox" aria-expanded={isOpen} aria-haspopup="listbox" aria-label="Select project">
  <button onClick={toggle} aria-label={selectedProject ? `Selected: ${selectedProject.name}` : 'Select a project'}>
    {/* trigger content */}
  </button>
  {isOpen && (
    <ul role="listbox" aria-label="Available projects">
      {projects.map(project => (
        <li
          key={project.project_id}
          role="option"
          aria-selected={project.project_id === selectedProject?.project_id}
          onClick={() => onSelect(project.project_id)}
        >
          {project.name}
        </li>
      ))}
    </ul>
  )}
</div>
```

## Verification

### Automated Checks

```bash
cd solune/frontend

# Run all tests
npx vitest run

# Type check
npm run type-check

# Lint
npm run lint

# Lint specific files
npx eslint src/pages/ProjectsPage.tsx src/components/board/

# Build (ensures no compilation errors)
npm run build
```

### Manual Verification

1. **Loading state**: Navigate to `/projects` — verify loading indicator appears, never a blank screen
2. **Error state**: Disconnect network/mock API error — verify user-friendly message with retry
3. **Empty state**: Use account with no projects — verify meaningful empty state
4. **Rate limit**: Mock rate limit response — verify banner with reset countdown
5. **Page decomposition**: Verify `ProjectsPage.tsx` is ≤250 lines (`wc -l src/pages/ProjectsPage.tsx`)
6. **Dark mode**: Toggle theme — verify all elements visible with adequate contrast
7. **Responsive**: Resize viewport 768px → 1920px — verify no layout breaks
8. **Keyboard**: Tab through all interactive elements — verify focus visibility and activation
9. **Screen reader**: Verify ARIA labels read correctly (or use axe DevTools audit)

### Audit Scoring

After each phase, score the relevant checklist items:

```bash
# Quick reference — count lines
wc -l src/pages/ProjectsPage.tsx                    # Should be ≤250
wc -l src/components/board/ProjectSelector.tsx       # Should exist
wc -l src/components/board/PipelineSelector.tsx      # Should exist
wc -l src/components/board/BoardHeader.tsx           # Should exist
wc -l src/components/board/RateLimitBanner.tsx       # Should exist

# Check for any types
grep -rn 'as any\|: any\|<any>' src/pages/ProjectsPage.tsx src/components/board/ src/hooks/useProject*.ts src/hooks/useBoard*.ts

# Check for console.log
grep -rn 'console\.log' src/pages/ProjectsPage.tsx src/components/board/

# Check for inline styles
grep -rn 'style=' src/pages/ProjectsPage.tsx src/components/board/

# Check for relative imports
grep -rn "from '\.\." src/pages/ProjectsPage.tsx src/components/board/
```
