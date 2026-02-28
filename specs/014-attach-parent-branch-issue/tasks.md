# Tasks: Attach Parent Branch to GitHub Issue Upon Branch Creation

**Input**: Design documents from `/specs/014-attach-parent-branch-issue/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in feature specification. Manual testing via branch creation is sufficient. `actionlint` recommended for workflow syntax validation (see quickstart.md).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- All paths are relative to repository root

## Path Conventions

- **Project type**: Single (one workflow file, no application code changes)
- **Workflow file**: `.github/workflows/branch-issue-link.yml`
- **Spec docs**: `specs/014-attach-parent-branch-issue/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the workflow file with trigger configuration, permissions, and concurrency control

- [ ] T001 Create workflow file `.github/workflows/branch-issue-link.yml` with `name: Branch Issue Link`, `on: create` trigger, top-level `permissions: {}`, and job skeleton (`link-branch` job targeting `ubuntu-latest`)
- [ ] T002 [P] Configure job-level permissions with `issues: write` and `contents: read` in `.github/workflows/branch-issue-link.yml`
- [ ] T003 [P] Add concurrency group `branch-issue-link-${{ github.event.ref }}` with `cancel-in-progress: true` in `.github/workflows/branch-issue-link.yml`
- [ ] T004 [P] Add job-level condition `if: github.event.ref_type == 'branch' && github.event.repository.fork == false` to filter out tag events and fork events (FR-010) in `.github/workflows/branch-issue-link.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement branch name parsing logic that ALL user stories depend on — extracts issue number from branch name using regex

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Add "Parse branch name" step in `.github/workflows/branch-issue-link.yml` that: (1) reads branch name from `${{ github.event.ref }}`, (2) strips path prefix via `base_name="${BRANCH_NAME##*/}"`, (3) matches with bash regex `[[ "$base_name" =~ ^(issue-)?0*([0-9]+) ]]` to extract the leading issue number with leading-zero removal into `BASH_REMATCH[2]`, (4) writes `ISSUE_NUMBER` to `$GITHUB_OUTPUT` if matched (per contracts/branch-issue-link-workflow.md Step 1 regex logic)

**Checkpoint**: Branch name parsing works for all documented patterns (`042-fix-navigation` → 42, `feature/issue-15-add-search` → 15, `007-feature` → 7, `hotfix-urgent` → no match). User story implementation can now begin.

---

## Phase 3: User Story 1 — Automatic Branch-to-Issue Linking on Branch Creation (Priority: P1) 🎯 MVP

**Goal**: When a branch with a recognized issue number is created, automatically post a comment on the corresponding GitHub Issue linking the branch — no manual developer action required.

**Independent Test**: Create a branch named `042-test-link` in a repo with open Issue #42. Verify Issue #42 receives a comment with the branch reference within seconds. Also test with `feature/issue-15-description` pattern.

### Implementation for User Story 1

- [ ] T006 [US1] Add "Check issue existence" step that runs `gh issue view $ISSUE_NUMBER --json state,number` to verify the issue exists and capture its state (`OPEN`/`CLOSED`), setting `ISSUE_STATE` output via `$GITHUB_OUTPUT`, conditioned on `steps.parse.outputs.ISSUE_NUMBER != ''` in `.github/workflows/branch-issue-link.yml`
- [ ] T007 [US1] Add "Post branch link comment" step that constructs the comment body with hidden idempotency marker `<!-- branch-link: {BRANCH_NAME} -->` followed by visible text `🔗 **Branch linked:** \`{BRANCH_NAME}\`` and workflow run URL, then posts via `gh issue comment $ISSUE_NUMBER --body "$COMMENT_BODY"`, conditioned on successful issue existence check in `.github/workflows/branch-issue-link.yml`

**Checkpoint**: User Story 1 fully functional — branches matching naming conventions automatically get linked to their issues via comments.

---

## Phase 4: User Story 2 — Idempotent Branch Attachment (Priority: P2)

**Goal**: Ensure duplicate branch references are never created on an issue, even when the same branch creation event is processed multiple times or a branch is deleted and recreated.

**Independent Test**: Trigger the workflow twice for the same branch (e.g., delete and recreate `042-test-link`). Verify Issue #42 has exactly one branch link comment, not two. Check workflow logs show "already linked" skip message on second run.

### Implementation for User Story 2

- [ ] T008 [US2] Add "Check for existing link" step in `.github/workflows/branch-issue-link.yml` between the issue existence check and comment posting that: (1) fetches comments via `gh issue view $ISSUE_NUMBER --json comments --jq '.comments[].body'`, (2) pipes output through `grep -F "<!-- branch-link: $BRANCH_NAME -->"` to search for the idempotency marker, (3) sets `ALREADY_LINKED=true` in `$GITHUB_OUTPUT` if grep exits 0, (4) logs `echo "::notice::Branch is already linked to issue #${ISSUE_NUMBER}"` when duplicate detected
- [ ] T009 [US2] Add condition `steps.check-link.outputs.ALREADY_LINKED != 'true'` to the "Post branch link comment" step to skip posting when the branch is already linked in `.github/workflows/branch-issue-link.yml`

**Checkpoint**: User Story 2 fully functional — duplicate branch references are never created. Idempotency verified through marker-based deduplication.

---

## Phase 5: User Story 3 — Graceful Handling When No Issue Can Be Determined (Priority: P2)

**Goal**: Branches without a recognizable issue number in their name are handled gracefully — an informational notice is logged and no further action is taken. Branch creation is never blocked or delayed.

**Independent Test**: Create a branch named `hotfix-urgent` (no issue number). Verify the workflow logs a notice annotation and exits successfully without errors. Verify no issues are modified.

### Implementation for User Story 3

- [ ] T010 [US3] Add notice annotation `echo "::notice::Branch '{BRANCH_NAME}' does not contain a recognizable issue number. No issue will be linked."` when the parse step finds no match (FR-005), and ensure subsequent steps are skipped via their conditions on `ISSUE_NUMBER` output in `.github/workflows/branch-issue-link.yml`

**Checkpoint**: User Story 3 fully functional — unrecognized branch names produce a visible notice without errors or failures.

---

## Phase 6: User Story 4 — Handling Non-Existent or Closed Issues (Priority: P3)

**Goal**: When a branch references an issue number that does not exist or is already closed, the system surfaces clear warnings rather than failing silently.

**Independent Test**: Create a branch named `99999-nonexistent-feature` (non-existent issue). Verify a warning annotation is logged and the workflow exits successfully. Create a branch referencing a closed issue and verify a warning is logged but the comment is still posted.

### Implementation for User Story 4

- [ ] T011 [US4] Add error handling to the "Check issue existence" step: when `gh issue view` returns a non-zero exit code (issue not found), output `::warning::Issue #${ISSUE_NUMBER} was not found in this repository. Branch '${BRANCH_NAME}' will not be linked.` and set `ISSUE_EXISTS=false` output to skip subsequent steps (FR-006) in `.github/workflows/branch-issue-link.yml`
- [ ] T012 [US4] Add closed-issue warning: when the issue state is `CLOSED`, output `::warning::Issue #${ISSUE_NUMBER} is closed. The branch link comment will still be posted.` and allow the workflow to continue with comment posting (FR-007) in `.github/workflows/branch-issue-link.yml`

**Checkpoint**: User Story 4 fully functional — non-existent and closed issues produce descriptive warnings. Non-existent issues skip linking; closed issues still receive the link comment.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Add retry logic for transient failures, final validation, and documentation

- [ ] T013 [P] Implement retry logic in the "Post branch link comment" step in `.github/workflows/branch-issue-link.yml` using a bash for-loop (3 attempts) that: (1) runs `gh issue comment` and checks exit code, (2) on non-zero exit code sleeps with exponential backoff (`sleep $((2 ** attempt))` → 2s, 4s, 8s), (3) breaks on success (exit code 0), (4) after all retries exhausted outputs `::warning::Failed to post branch link comment after 3 attempts` and exits 0 to avoid blocking (FR-008)
- [ ] T014 [P] Add `env` block at the job level setting `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` for `gh` CLI authentication in `.github/workflows/branch-issue-link.yml`
- [ ] T015 Validate workflow syntax by running `actionlint .github/workflows/branch-issue-link.yml` (or `yamllint` if actionlint is unavailable) and fix any issues
- [ ] T016 Run quickstart.md manual validation scenarios: create a test branch with issue number, verify comment posted; create branch without issue number, verify notice logged; verify idempotency by re-triggering

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - US1 (Phase 3) should be completed first as MVP
  - US2 (Phase 4) depends on US1 (adds idempotency check before US1's comment posting step)
  - US3 (Phase 5) can proceed independently after Foundational
  - US4 (Phase 6) can proceed independently after Foundational, but integrates with US1's issue check step
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (modifies the comment posting flow with an idempotency gate)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Independent of other stories
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) — Integrates with US1's issue check step but is independently testable

### Within Each User Story

- All tasks modify the same workflow file (`.github/workflows/branch-issue-link.yml`)
- Tasks within a story should be completed sequentially (same file)
- Core flow first (check → post), then edge case handling

### Parallel Opportunities

- Setup tasks T001–T004 marked [P] can be authored in parallel (different YAML sections of the same file)
- US3 (Phase 5) can be implemented in parallel with US1 (Phase 3) since they affect different workflow steps
- US4 (Phase 6) can be implemented in parallel with US2 (Phase 4) since they affect different workflow steps
- Polish tasks T013 and T014 marked [P] can be done in parallel (different sections of the workflow file)

---

## Parallel Example: User Story 1

```bash
# US1 tasks are sequential (same file, dependent steps):
Task: "Add 'Check issue existence' step in .github/workflows/branch-issue-link.yml"
Task: "Add 'Post branch link comment' step in .github/workflows/branch-issue-link.yml"

# But US3 can run in parallel with US1 (different step, no dependency):
Task: "Add notice annotation for unrecognized branches in .github/workflows/branch-issue-link.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — workflow file skeleton with trigger, permissions, concurrency
2. Complete Phase 2: Foundational — branch name parsing regex
3. Complete Phase 3: User Story 1 — issue check + comment posting
4. **STOP and VALIDATE**: Create a test branch, verify comment appears on the issue
5. Deploy/demo if ready — core value is delivered

### Incremental Delivery

1. Complete Setup + Foundational → Workflow skeleton ready
2. Add User Story 1 → Test with branch creation → Deploy (MVP!)
3. Add User Story 2 → Test idempotency (delete/recreate branch) → Deploy
4. Add User Story 3 → Test with non-issue branches → Deploy
5. Add User Story 4 → Test with non-existent/closed issues → Deploy
6. Add Polish → Retry logic, final validation → Deploy
7. Each story adds reliability without breaking previous stories

### Parallel Team Strategy

With multiple developers (less applicable — single file feature):

1. Developer A: Setup + Foundational + US1 (core flow)
2. Developer B: US3 (no-match handling — independent step)
3. After US1 is done: Developer A takes US2 (idempotency), Developer B takes US4 (error handling)
4. Polish phase done by either developer after all stories merge

---

## Notes

- [P] tasks = different files or file sections, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- This is a single-file feature (`.github/workflows/branch-issue-link.yml`) — all tasks modify the same file
- The workflow always exits with code 0 to avoid blocking other CI workflows
- All failures are surfaced as GitHub Actions annotations (`::warning::` or `::notice::`)
- The `gh` CLI is pre-installed on GitHub Actions runners — no additional dependencies needed
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, cross-story dependencies that break independence
