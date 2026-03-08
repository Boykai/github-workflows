# Research: Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues

**Feature**: 030-fix-chore-issue-counter | **Date**: 2026-03-08

## R1: How Are Chore Issues Currently Classified?

**Task**: Determine how issues created by the Chore trigger system are marked so they can be excluded from the "Every X Issues" counter.

**Decision**: Chore-triggered issues are labelled with the `"chore"` label at creation time. This label is the authoritative classification marker.

**Rationale**: In `backend/src/services/chores/service.py:372`, the `trigger_chore()` method creates GitHub issues with `labels=["chore"]`. The `cleanup_service.py:50` defines `APP_CREATED_LABELS = frozenset(["ai-generated", "chore", "agent-config"])`, confirming `"chore"` is the canonical label. The board data pipeline already fetches `labels` for each `BoardItem` via the GraphQL query (`labels(first:20)`), and these are available as `BoardItem.labels: BoardLabel[]` on the frontend. Filtering by this label in the `parentIssueCount` computation is the minimal change.

**Alternatives Considered**:
- **Filter by issue type metadata**: Rejected — GitHub Issues don't have a native "chore" type. The label is the only reliable classification.
- **Maintain a server-side list of chore-created issue numbers**: Rejected — over-engineered; the label already provides this information and is available on every board item.

---

## R2: How Are Sub-Issues Currently Excluded?

**Task**: Verify that Sub-Issues are already excluded from the `parentIssueCount` computation, or identify the fix needed.

**Decision**: Sub-Issues are **already correctly excluded** in the current `parentIssueCount` computation in `ChoresPage.tsx:28-55`. No change needed for Sub-Issue filtering.

**Rationale**: The existing code performs a two-pass algorithm:
1. **Pass 1**: Collects all `subIssue.number` values from every `item.sub_issues` array across all columns into a `subIssueNumbers` Set.
2. **Pass 2**: Iterates all board items, skipping any item whose `number` is in the `subIssueNumbers` Set.

This correctly excludes any issue that appears as a child in GitHub's parent-child relationship. The `sub_issues` data comes from the backend's GraphQL query (and the REST `get_sub_issues()` endpoint cached for 10 minutes). The board data pipeline in `service.py:995-1007` also removes sub-issues from column items before returning the board, providing a second layer of filtering.

**Alternatives Considered**:
- **Backend-side sub-issue filtering for counter**: Rejected — the frontend already handles this correctly using board data. Adding a backend endpoint would duplicate logic.

---

## R3: What Is Missing From the Current `parentIssueCount` Computation?

**Task**: Identify the specific gap causing the counter to be inflated.

**Decision**: The current `parentIssueCount` computation excludes Sub-Issues and non-issue content types (PRs, drafts) but does **not** exclude issues with the `"chore"` label. This means Chore-triggered issues inflate the counter.

**Rationale**: Examining `ChoresPage.tsx:44-52`, the filter chain is:
1. `item.content_type !== 'issue'` → skip non-issues ✅
2. `seenItemIds.has(item.item_id)` → dedup ✅
3. `subIssueNumbers.has(item.number)` → skip sub-issues ✅
4. **Missing**: No check for `item.labels.some(l => l.name === 'chore')` → chore-labelled issues are counted ❌

Adding a fourth filter condition to skip items with the `"chore"` label will resolve the bug. The `item.labels` array (type `BoardLabel[]`) is already populated by the GraphQL query and available on every `BoardItem`.

**Alternatives Considered**:
- **Filter by a broader label set (e.g., all APP_CREATED_LABELS)**: Rejected — the spec specifically says "exclude issues classified as Chores." The `"ai-generated"` and `"agent-config"` labels may apply to legitimate parent issues that should be counted. Only `"chore"` should be excluded.

---

## R4: Per-Chore Counter Independence

**Task**: Verify that the counter is already scoped independently per Chore, or identify changes needed.

**Decision**: The per-Chore counter scoping is **already correctly implemented** via the `last_triggered_count` field on each `Chore` record. No change needed.

**Rationale**: Each `Chore` has its own `last_triggered_count` which snapshots the global `parentIssueCount` at the time that specific Chore was last triggered. The counter calculation `issues_since = parentIssueCount - chore.last_triggered_count` (used in both `counter.py` and `ChoreCard.tsx`) gives each Chore an independent count of issues since its last run. Triggering Chore A updates only Chore A's `last_triggered_count` (via CAS update in `update_chore_after_trigger()`), leaving Chore B's counter unaffected.

**Alternatives Considered**:
- **Per-chore timestamp-bounded GitHub API query**: Rejected — the snapshot-delta approach achieves the same accuracy with zero additional API calls.

---

## R5: Counter Reset After Chore Execution

**Task**: Verify that the counter resets correctly when a Chore fires.

**Decision**: Counter reset is **already correctly implemented**. When a Chore triggers, `trigger_chore()` sets `last_triggered_count = parent_issue_count` (the current global count), which effectively resets the delta to 0.

**Rationale**: In `service.py:485-498`, after a successful trigger:
```python
new_count = (
    parent_issue_count if parent_issue_count is not None
    else chore.last_triggered_count
)
cas_ok = await self.update_chore_after_trigger(
    chore.id,
    last_triggered_count=new_count,
    ...
)
```
This re-anchors the baseline, so the next `parentIssueCount - last_triggered_count` starts from 0. The CAS (Compare-And-Swap) pattern prevents double-firing. The only requirement is that the **corrected** `parentIssueCount` (excluding chore-labelled issues) is passed to `trigger_chore()`.

**Alternatives Considered**:
- **Separate reset endpoint**: Rejected — reset is already atomic with the trigger operation. YAGNI.

---

## R6: Consistency Between Tile Display and Trigger Evaluation

**Task**: Verify that the tile counter and trigger evaluation use the same filtered count.

**Decision**: Both tile display and trigger evaluation **already share the same data path** — both use `parentIssueCount` and `chore.last_triggered_count` to compute the delta. Once `parentIssueCount` is corrected to exclude chore-labelled issues, both will be consistent.

**Rationale**: 
- **Tile display** (`ChoreCard.tsx:60-64`): `issuesSince = parentIssueCount - chore.last_triggered_count`
- **Trigger evaluation** (`counter.py:22`): `issues_since = current_count - chore.last_triggered_count`
- Both use the same formula. The `parentIssueCount` is computed once in `ChoresPage.tsx` and passed as a prop to both `ChoreCard` and `FeaturedRitualsPanel`.
- The backend trigger evaluation receives the count via the `parent_issue_count` parameter to `evaluate_triggers()`, which must be the same corrected value.

**Alternatives Considered**:
- **Single source-of-truth function shared between frontend and backend**: Rejected as impractical across language boundaries. The formula is simple enough (`total - baseline = delta`) that consistency is maintained by using the same input value.

---

## R7: Edge Case — Chore Never Executed

**Task**: Determine how a Chore with no `last_triggered_at` timestamp handles the counter.

**Decision**: A never-executed Chore has `last_triggered_count = 0` (the default). This means the counter shows `parentIssueCount - 0 = parentIssueCount`, which counts all qualifying Parent Issues since project inception. This behaviour aligns with FR-009 ("use the Chore's creation timestamp as the baseline"), because the Chore was created when the project had some number of issues, and `last_triggered_count = 0` would overcount.

**Caveat**: The spec says to use the Chore's creation date as baseline (FR-009). Currently, a new Chore starts with `last_triggered_count = 0`. If the project already has 50 parent issues when a Chore with "Every 5 issues" is created, the counter would immediately show "Ready to trigger" (50 >= 5). This is a pre-existing behaviour inherited from the 029 implementation and is **not in scope** for this bug fix. The 029 spec's R1 decision explicitly chose the global count approach and this fix preserves that behaviour while correcting the label filter.

**Alternatives Considered**:
- **Initialize `last_triggered_count` to current `parentIssueCount` on Chore creation**: Would address the edge case but is out of scope for this bug fix and would require a backend change. Noted for future enhancement.
