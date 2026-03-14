# API Contract: Model Field Removal

**Branch**: `035-remove-blocking-feature` | **Date**: 2026-03-12 | **Plan**: [plan.md](../plan.md)

## Model Fields Being Removed

The following fields are referenced in code but were never added to the Pydantic models. All code that accesses these non-existent fields must be removed.

---

### AITaskProposal.is_blocking

**Model file**: `backend/src/models/recommendation.py`
**Field status**: ❌ Never added to model
**Referenced at**:
- `backend/src/api/chat.py:763` — `proposal_is_blocking = proposal.is_blocking`
- `backend/src/services/signal_chat.py:453` — `labels=with_blocking_label([], proposal.is_blocking)`

**Action**: Remove all lines that access `proposal.is_blocking`. Remove the `proposal_is_blocking` variable and all downstream uses.

---

### IssueRecommendation.is_blocking

**Model file**: `backend/src/models/recommendation.py`
**Field status**: ❌ Never added to model
**Referenced at**:
- `backend/src/api/workflow.py:269` — `is_blocking=recommendation.is_blocking`
- `backend/src/services/signal_chat.py:389` — `labels=with_blocking_label([], rec.is_blocking)`
- `backend/src/services/workflow_orchestrator/orchestrator.py:619` — `return with_blocking_label(labels, recommendation.is_blocking)`

**Action**: Remove all lines that access `.is_blocking` on recommendation objects. Simplify label-building code to not include blocking labels.

---

### ProjectPipelineAssignment.blocking_override

**Model file**: `backend/src/models/pipeline.py`
**Field status**: ❌ Never added to model
**Database column**: `pipeline_blocking_override` on `project_settings` (added by Migration 018)
**Referenced at**:
- `backend/src/services/chores/service.py:548-549` — `assignment.blocking_override`

**Action**: Remove the blocking resolution logic block in chores/service.py that accesses this field.

---

### Chore Preset "blocking" Keys

**Location**: `backend/src/services/chores/service.py` (lines 21–55)
**Current values**:
```python
"security-review": {"blocking": False, ...}
"performance-review": {"blocking": False, ...}
"bug-basher": {"blocking": True, ...}
```

**Action**: Remove the `"blocking"` key from all preset dictionaries.

---

### _CHORE_UPDATABLE_COLUMNS "blocking" Entry

**Location**: `backend/src/services/chores/service.py` (line 77)
**Current**: `"blocking"` is in the set of updatable columns

**Action**: Remove `"blocking"` from the `_CHORE_UPDATABLE_COLUMNS` set.

---

## Frontend Mock Data Fields

### PipelineConfig.blocking

**Test files**:
- `frontend/src/components/board/ProjectIssueLaunchPanel.test.tsx` — `blocking: false`
- `frontend/src/components/pipeline/SavedWorkflowsList.test.tsx` — `blocking: false`

**Action**: Remove `blocking` field from mock pipeline config objects.

### PipelineAssignment.blocking_override

**Test file**: `frontend/src/pages/ProjectsPage.test.tsx` — `mocks.pipelineAssignment.blocking_override = true`

**Action**: Remove `blocking_override` assignment from test mocks.
