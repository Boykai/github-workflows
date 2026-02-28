# Quickstart: Preserve Full User-Provided GitHub Issue Description Without Truncation

**Feature**: 014-preserve-issue-description
**Date**: 2026-02-28

## Prerequisites

- Python 3.12+
- Node.js 20+
- Repository cloned and dependencies installed

## Backend Setup

```bash
cd backend
pip install -e ".[dev]"
```

## Frontend Setup

```bash
cd frontend
npm install
```

## Running Tests

### Backend Tests (targeted)

```bash
cd backend

# Run all tests related to this feature
pytest tests/unit/test_api_chat.py -v -k "description"
pytest tests/unit/test_api_workflow.py -v -k "description"

# Run the full test suite
pytest -v
```

### Frontend Tests (targeted)

```bash
cd frontend
npm test
```

## Key Files to Modify

### Backend

| File | Change |
|------|--------|
| `backend/src/models/recommendation.py` | Fix `max_length` from 65535 → 65536 on `proposed_description` and `edited_description` |
| `backend/src/constants.py` | Add `GITHUB_ISSUE_BODY_MAX_LENGTH = 65_536` constant |
| `backend/src/services/workflow_orchestrator/orchestrator.py` | Add body length validation in `create_issue_from_recommendation()` |
| `backend/src/api/chat.py` | Add body length validation in `confirm_proposal()` |

### Backend Tests

| File | Change |
|------|--------|
| `backend/tests/unit/test_api_chat.py` | Add tests for description preservation at boundary lengths |
| `backend/tests/unit/test_api_workflow.py` | Add tests for description preservation at boundary lengths |
| `backend/tests/unit/test_recommendation_models.py` | Add tests for max_length=65536 on model fields |

## Verification Checklist

- [ ] `AITaskProposal.proposed_description` accepts 65,536 characters
- [ ] `ProposalConfirmRequest.edited_description` accepts 65,536 characters
- [ ] `confirm_proposal()` passes full description to `create_issue(body=...)`
- [ ] `create_issue_from_recommendation()` passes full body to `create_issue(body=...)`
- [ ] Body exceeding 65,536 characters returns HTTP 422 with clear message
- [ ] Body at exactly 65,536 characters succeeds
- [ ] All markdown formatting preserved (headers, lists, code blocks, etc.)
- [ ] Unicode and emoji characters preserved
- [ ] All backend tests pass
- [ ] All frontend tests pass

## Architecture Notes

The chat-to-issue pipeline has two paths:

### Path 1: Workflow Recommendation (Primary)
```
User chat → AI recommendation → confirm_recommendation() → format_issue_body() → create_issue()
```

### Path 2: Task Proposal (Secondary)
```
User chat → AI task proposal → confirm_proposal() → create_issue()
```

Both paths ultimately call `github_projects_service.create_issue(body=...)`. The body validation should be applied at both call sites to ensure coverage.
