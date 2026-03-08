# Quickstart: Chores Page — Counter Fixes, Featured Rituals Panel, Inline Editing, AI Enhance Toggle, Agent Pipeline Config & Auto-Merge PR Flow

**Feature**: 029-chores-page-enhancements | **Date**: 2026-03-07

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 029-chores-page-enhancements
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
# Database migrations run automatically on startup
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## New Files to Create

### Backend

| File | Purpose |
|------|---------|
| `backend/src/migrations/016_chores_enhancements.sql` | Add `execution_count`, `ai_enhance_enabled`, `agent_pipeline_id` columns to `chores` table |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/components/chores/FeaturedRitualsPanel.tsx` | Three-card panel showing Next Run, Most Recently Run, Most Run Chores |
| `frontend/src/components/chores/ChoreInlineEditor.tsx` | Inline editable Chore definition fields (name, template, schedule) |
| `frontend/src/components/chores/ConfirmChoreModal.tsx` | Two-step confirmation modal for new Chore creation with auto-merge |
| `frontend/src/components/chores/PipelineSelector.tsx` | Per-Chore Agent Pipeline dropdown (saved pipelines + Auto) |
| `frontend/src/hooks/useUnsavedChanges.ts` | Generic unsaved-changes navigation guard hook |

## Files to Modify

### Backend

| File | Changes |
|------|---------|
| `backend/src/models/chores.py` | Add `execution_count`, `ai_enhance_enabled`, `agent_pipeline_id` fields to `Chore`; extend `ChoreUpdate`; add `ChoreInlineUpdate`, `ChoreInlineUpdateResponse`, `ChoreCreateWithConfirmation`, `ChoreCreateResponse` models; add `ai_enhance` to `ChoreChatMessage` |
| `backend/src/services/chores/service.py` | Increment `execution_count` in `trigger_chore()`; add `inline_update_chore()` method with PR creation; add `create_chore_with_auto_merge()` method; add pipeline resolution logic in `trigger_chore()` |
| `backend/src/services/chores/counter.py` | No logic change needed (existing delta computation is correct); add helper to compute remaining count |
| `backend/src/services/chores/template_builder.py` | Add `update_template_in_repo()` method for inline edit PRs; add `merge_pull_request()` method for auto-merge |
| `backend/src/services/chores/chat.py` | Add `ai_enhance` parameter to `generate_chat_response()`; add metadata-only system prompt for AI Enhance OFF path |
| `backend/src/api/chores.py` | Add `PUT /{project_id}/{chore_id}/inline-update` endpoint; modify `POST /{project_id}` to support `ChoreCreateWithConfirmation` with auto-merge; pass `ai_enhance` to chat endpoint |

### Frontend

| File | Changes |
|------|---------|
| `frontend/src/types/index.ts` | Add `execution_count`, `ai_enhance_enabled`, `agent_pipeline_id` to `Chore` interface; add `ChoreInlineUpdate`, `ChoreInlineUpdateResponse`, `ChoreCreateWithConfirmation`, `ChoreCreateResponse`, `FeaturedRituals`, `FeaturedRitualCard`, `ChoreEditState`, `ChoreCounterData`, `ChoreChatMessage` types |
| `frontend/src/services/api.ts` | Add `inlineUpdate()`, `createWithAutoMerge()` to `choresApi`; extend `chat()` to accept `ai_enhance` parameter |
| `frontend/src/hooks/useChores.ts` | Add `useInlineUpdateChore()` mutation hook; add `useCreateChoreWithAutoMerge()` mutation hook; extend `useChoreChat()` to pass `ai_enhance` |
| `frontend/src/pages/ChoresPage.tsx` | Add `FeaturedRitualsPanel` above `ChoresPanel`; add `useUnsavedChanges` hook; pass parent issue count to panel |
| `frontend/src/components/chores/ChoresPanel.tsx` | Add inline edit state management (`editState` map); wire dirty tracking; add Save button; pass `parentIssueCount` for counter computation |
| `frontend/src/components/chores/ChoreCard.tsx` | Switch to view/edit mode; show corrected counter (remaining = threshold - issuesSince); add AI Enhance toggle; add PipelineSelector dropdown; show inline edit fields |
| `frontend/src/components/chores/AddChoreModal.tsx` | Add AI Enhance toggle; add PipelineSelector; replace simple save with ConfirmChoreModal two-step flow |
| `frontend/src/components/chores/ChoreChatFlow.tsx` | Accept and pass `ai_enhance` flag to chat API; adjust UI for metadata-only mode |

## Implementation Order

### Phase 1: Backend Schema & Models

1. **Migration** (`016_chores_enhancements.sql`)
   - Add `execution_count INTEGER NOT NULL DEFAULT 0` to `chores`
   - Add `ai_enhance_enabled INTEGER NOT NULL DEFAULT 1` to `chores`
   - Add `agent_pipeline_id TEXT NOT NULL DEFAULT ''` to `chores`
   - Add indexes on `execution_count` and `last_triggered_at`

2. **Models** (`models/chores.py`)
   - Add `execution_count`, `ai_enhance_enabled`, `agent_pipeline_id` to `Chore`
   - Extend `ChoreUpdate` with `ai_enhance_enabled`, `agent_pipeline_id`
   - Add `ChoreInlineUpdate`, `ChoreInlineUpdateResponse`
   - Add `ChoreCreateWithConfirmation`, `ChoreCreateResponse`
   - Add `ai_enhance` to `ChoreChatMessage`

3. **Service — Counter Fix** (`services/chores/service.py`)
   - Modify `trigger_chore()` to increment `execution_count` on each trigger
   - Add pipeline resolution: if `agent_pipeline_id` is non-empty, use it; if empty, read `project_settings.assigned_pipeline_id`
   - Handle deleted pipeline fallback (log warning, use Auto)

4. **Service — Inline Update** (`services/chores/service.py` + `template_builder.py`)
   - Add `inline_update_chore(chore_id, body: ChoreInlineUpdate)` method
   - If `template_content` changed: commit updated file via `commit_files_workflow`, create PR
   - If `expected_sha` provided: check for conflict before committing
   - Update Chore record in database

5. **Service — Auto-Merge** (`services/chores/template_builder.py`)
   - Add `merge_pull_request(access_token, owner, repo, pr_number)` method
   - Use GitHub REST API `PUT /repos/{owner}/{repo}/pulls/{pr_number}/merge` with squash method
   - Return success/failure with error message

6. **Service — Chat AI Enhance** (`services/chores/chat.py`)
   - Add `ai_enhance` parameter to `generate_chat_response()`
   - When `ai_enhance=false`: use metadata-only system prompt; inject user's raw content as body
   - Assemble final template: AI front matter + user verbatim body

7. **API Endpoints** (`api/chores.py`)
   - Add `PUT /{project_id}/{chore_id}/inline-update` → `ChoreInlineUpdateResponse`
   - Modify `POST /{project_id}` to accept `ChoreCreateWithConfirmation`, auto-merge if requested
   - Pass `ai_enhance` in `POST /{project_id}/chat`

### Phase 2: Frontend Types & API

8. **Types** (`types/index.ts`)
   - Extend `Chore` interface with new fields
   - Add all new interfaces (see data-model.md)

9. **API Client** (`services/api.ts`)
   - Add `inlineUpdate(projectId, choreId, data: ChoreInlineUpdate)` to `choresApi`
   - Add `createWithAutoMerge(projectId, data: ChoreCreateWithConfirmation)` to `choresApi`
   - Extend `chat()` signature to accept `ai_enhance` boolean

### Phase 3: Frontend Hooks

10. **useChores** hook extensions
    - Add `useInlineUpdateChore(projectId)` mutation that calls `choresApi.inlineUpdate()`
    - Add `useCreateChoreWithAutoMerge(projectId)` mutation that calls `choresApi.createWithAutoMerge()`
    - Extend `useChoreChat` to pass `ai_enhance` parameter

11. **useUnsavedChanges** hook (new)
    - Accept `isDirty: boolean` parameter
    - Register `beforeunload` event listener when dirty
    - Use `react-router-dom` `useBlocker` for SPA navigation blocking
    - Return `{ blocker, isBlocked }` for custom modal rendering

### Phase 4: Frontend Components

12. **FeaturedRitualsPanel** (new, standalone)
    - Accepts `chores: Chore[]` and `parentIssueCount: number`
    - Computes three rankings (Next Run, Most Recently Run, Most Run)
    - Renders three cards with Chore name, stat, and link
    - Handles empty state (no Chores)

13. **PipelineSelector** (new, standalone)
    - Accepts `selectedPipelineId: string`, `onPipelineChange: (id: string) => void`
    - Fetches pipeline list via `usePipelinesList(projectId)`
    - Renders dropdown: "Auto" + saved pipelines
    - Shows warning if selected pipeline no longer exists

14. **ConfirmChoreModal** (new, standalone)
    - Accepts `isOpen`, `onConfirm`, `onCancel`, `choreName`
    - Internal `step` state (1 or 2)
    - Step 1: Information + "I Understand, Continue" + "Cancel"
    - Step 2: Final confirmation + "Yes, Create Chore" + "Back"

15. **ChoreInlineEditor** (new, used within ChoreCard)
    - Accepts `chore: Chore`, `onChange: (updates: Partial<ChoreInlineUpdate>) => void`
    - Renders editable inputs for name, template_content, schedule config
    - Reports changes to parent for dirty tracking

16. **ChoreCard** (modified)
    - Add inline editing mode (always editable per FR-005)
    - Fix counter display: show `remaining = schedule_value - (parentIssueCount - last_triggered_count)` for count-based Chores
    - Add AI Enhance toggle (reuse ChatToolbar pattern)
    - Add PipelineSelector dropdown

17. **ChoresPanel** (modified)
    - Add `editState: Record<string, ChoreEditState>` for tracking per-Chore dirty state
    - Add Save button (prominent when any Chore is dirty)
    - Compute dirty state: compare `editState[id].current` vs `editState[id].original`
    - Pass `parentIssueCount` to ChoreCards for counter display

18. **AddChoreModal** (modified)
    - Add AI Enhance toggle (default ON)
    - Add PipelineSelector dropdown (default "Auto")
    - Replace save flow with ConfirmChoreModal two-step confirmation
    - On confirmation: call `createWithAutoMerge` mutation

19. **ChoreChatFlow** (modified)
    - Accept `aiEnhance: boolean` prop
    - When `aiEnhance=false`: pass `ai_enhance: false` in chat API calls
    - Show indicator in chat UI: "Your input will be used verbatim as the template body"

### Phase 5: Integration

20. **ChoresPage** (modified)
    - Add `FeaturedRitualsPanel` above `ChoresPanel`
    - Compute `parentIssueCount` from board data (filter parent issues from `useProjectBoard()`)
    - Wire `useUnsavedChanges` hook to `editState` dirty tracking

21. **Verification** (see checklist below)

## Key Patterns to Follow

### Per-Chore Counter Computation (Client-Side)

```typescript
// In ChoresPanel or ChoreCard:
function computeRemaining(chore: Chore, parentIssueCount: number): number {
  if (chore.schedule_type !== 'count' || !chore.schedule_value) return -1;
  const issuesSince = parentIssueCount - chore.last_triggered_count;
  const remaining = chore.schedule_value - issuesSince;
  return Math.max(0, remaining);
}
```

### Featured Rituals Ranking (Client-Side)

```typescript
function computeFeaturedRituals(
  chores: Chore[],
  parentIssueCount: number
): FeaturedRituals {
  const activeChores = chores.filter(c => c.status === 'active');

  // Next Run: lowest remaining count (count-based) or days (time-based)
  const nextRun = activeChores
    .filter(c => c.schedule_type)
    .sort((a, b) => {
      const remA = computeRemainingGeneric(a, parentIssueCount);
      const remB = computeRemainingGeneric(b, parentIssueCount);
      return remA - remB;
    })[0] ?? null;

  // Most Recently Run: latest last_triggered_at
  const mostRecent = activeChores
    .filter(c => c.last_triggered_at)
    .sort((a, b) =>
      new Date(b.last_triggered_at!).getTime() - new Date(a.last_triggered_at!).getTime()
    )[0] ?? null;

  // Most Run: highest execution_count
  const mostRun = activeChores
    .filter(c => c.execution_count > 0)
    .sort((a, b) => b.execution_count - a.execution_count)[0] ?? null;

  return { nextRun: toCard(nextRun), mostRecentlyRun: toCard(mostRecent), mostRun: toCard(mostRun) };
}
```

### Unsaved Changes Hook Pattern

```typescript
import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

export function useUnsavedChanges(isDirty: boolean) {
  // Browser close/refresh
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isDirty]);

  // SPA route transitions
  const blocker = useBlocker(isDirty);

  return { blocker, isBlocked: blocker.state === 'blocked' };
}
```

### AI Enhance Toggle Pattern (Reusing ChatToolbar Style)

```typescript
// In AddChoreModal or ChoreCard:
<button
  type="button"
  onClick={() => setAiEnhance(!aiEnhance)}
  className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full transition-colors border ${
    aiEnhance
      ? 'bg-primary/10 text-primary border-primary/30 hover:bg-primary/20'
      : 'bg-muted text-muted-foreground border-border/50 hover:bg-muted/80'
  }`}
  aria-pressed={aiEnhance}
  aria-label={`AI Enhance ${aiEnhance ? 'on' : 'off'}`}
>
  <Sparkles className="w-4 h-4" />
  <span>AI Enhance</span>
  <span className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${
    aiEnhance ? 'bg-primary text-primary-foreground' : 'bg-muted-foreground/20 text-muted-foreground'
  }`}>
    {aiEnhance ? 'ON' : 'OFF'}
  </span>
</button>
```

### Two-Step Confirmation Pattern

```typescript
function ConfirmChoreModal({ isOpen, onConfirm, onCancel, choreName }: Props) {
  const [step, setStep] = useState<1 | 2>(1);

  return (
    <Modal isOpen={isOpen} onClose={onCancel}>
      {step === 1 ? (
        <>
          <h3>Add Chore to Repository</h3>
          <p>This will create a file in <code>.github/ISSUE_TEMPLATE/</code> and auto-merge a PR into main.</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onCancel}>Cancel</Button>
            <Button onClick={() => setStep(2)}>I Understand, Continue</Button>
          </div>
        </>
      ) : (
        <>
          <h3>Create "{choreName}"?</h3>
          <p>A GitHub Issue will be created, a PR opened, and automatically merged into main.</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
            <Button variant="primary" onClick={onConfirm}>Yes, Create Chore</Button>
          </div>
        </>
      )}
    </Modal>
  );
}
```

### Auto-Merge PR Pattern (Backend)

```python
async def merge_pull_request(
    access_token: str,
    owner: str,
    repo: str,
    pr_number: int,
    merge_method: str = "squash",
) -> tuple[bool, str | None]:
    """Merge a PR via GitHub REST API. Returns (success, error_message)."""
    import httpx

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/merge"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = {"merge_method": merge_method}

    async with httpx.AsyncClient() as client:
        resp = await client.put(url, json=body, headers=headers)

    if resp.status_code == 200:
        return True, None
    else:
        error = resp.json().get("message", "Unknown merge error")
        return False, error
```

## Verification

After implementation, verify:

1. **Counter Fix**: Create a Chore with "Every 5 issues" → create 3 Parent Issues → verify tile shows "2 remaining" (not a global count)
2. **Counter Reset**: Trigger the Chore → verify counter resets and starts counting from the new `last_triggered_count`
3. **Featured Rituals — Next Run**: Create two count-based Chores with different thresholds → verify the panel shows the one closest to triggering
4. **Featured Rituals — Most Recently Run**: Trigger a Chore → verify it appears as "Most Recently Run" in the panel
5. **Featured Rituals — Most Run**: Trigger a Chore multiple times → verify it appears as "Most Run" with the correct count
6. **Featured Rituals — Empty State**: Delete all Chores → verify the panel shows an onboarding/empty state
7. **Inline Edit — Dirty State**: Edit a Chore name → verify asterisk/banner appears → edit back to original → verify indicator disappears
8. **Inline Edit — Navigation Guard**: Edit a Chore → click a navigation link → verify "unsaved changes" confirmation appears
9. **Inline Edit — Save with PR**: Edit a Chore's template content → click Save → verify a PR is created with the changes
10. **Inline Edit — Conflict Detection**: Edit a Chore while another user modifies the same file → click Save → verify 409 conflict is shown
11. **AI Enhance ON**: Create a Chore with AI Enhance ON → verify full AI-generated template (body + metadata)
12. **AI Enhance OFF**: Create a Chore with AI Enhance OFF → provide specific body text → verify the body appears verbatim in the template with AI-generated metadata
13. **Pipeline Selector — Saved Pipeline**: Create a Chore with a specific pipeline → verify it uses that pipeline at execution time
14. **Pipeline Selector — Auto**: Create a Chore with "Auto" → change the project's pipeline → trigger the Chore → verify it uses the updated project pipeline
15. **Pipeline Selector — Deleted Pipeline**: Delete a pipeline referenced by a Chore → verify warning shown and fallback to Auto
16. **Double Confirmation — Step 1**: Click Save on new Chore → verify first modal appears with repository warning
17. **Double Confirmation — Step 2**: Proceed from Step 1 → verify second modal appears with final confirmation
18. **Double Confirmation — Cancel**: Cancel at either step → verify no Issue/PR created, input preserved
19. **Auto-Merge — Success**: Create new Chore → confirm both steps → verify Issue created, PR created, PR merged, success toast
20. **Auto-Merge — Failure**: Simulate merge conflict → create new Chore → verify PR left open, Chore saved locally, error toast with PR link
