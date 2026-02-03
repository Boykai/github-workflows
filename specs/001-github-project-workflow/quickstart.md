# Quickstart: AI-Assisted GitHub Issue Creation and Workflow Management

**Date**: February 2, 2026  
**Spec**: [spec.md](./spec.md)

## Prerequisites

Before implementing this feature, ensure you have:

1. **GitHub OAuth App** configured with scopes: `repo`, `project`, `user`
2. **Azure OpenAI** deployment with GPT-4 or compatible model
3. **GitHub Project** with status columns: Backlog, Ready, In Progress, In Review
4. **GitHub Copilot** user/bot account with repository access (for assignment)

## Environment Variables

Add to your `.env` file:

```bash
# Existing (already required)
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# New (optional - defaults provided)
WORKFLOW_COPILOT_ASSIGNEE=github-copilot
WORKFLOW_POLL_INTERVAL_SECONDS=30
```

## Implementation Order

Follow this order for smooth incremental development:

### Phase 1: AI Issue Recommendation (P1)

**Files to create/modify:**

1. `backend/src/prompts/issue_generation.py` - New prompt template
2. `backend/src/services/ai_agent.py` - Add `generate_issue_recommendation()` method
3. `backend/src/models/chat.py` - Add `IssueRecommendation` model and `ActionType.ISSUE_CREATE`
4. `backend/src/api/chat.py` - Extend message handler to detect feature requests

**Test**: Send a feature request in chat, verify AI returns structured recommendation.

### Phase 2: GitHub Issue Creation (P2)

**Files to create/modify:**

1. `backend/src/services/github_projects.py` - Add `create_issue()` and `add_issue_to_project()` methods
2. `backend/src/services/workflow_orchestrator.py` - New file with workflow state machine
3. `backend/src/api/workflow.py` - New API router for workflow endpoints

**Test**: Confirm a recommendation, verify GitHub Issue is created and attached to project.

### Phase 3: Status Automation (P3-P5)

**Files to modify:**

1. `backend/src/services/workflow_orchestrator.py` - Add status transition and assignment logic
2. `backend/src/services/github_projects.py` - Add `assign_issue()` method

**Test**: Verify automatic status transitions and assignments work.

## Key Code Patterns

### 1. Issue Recommendation Generation

```python
# backend/src/prompts/issue_generation.py
ISSUE_GENERATION_SYSTEM_PROMPT = """You are an expert product manager helping structure feature requests.
Generate a well-structured GitHub issue with:
- A clear, concise title (max 256 chars)
- A user story in "As a... I want... So that..." format
- UI/UX description for designers/developers
- Specific, testable functional requirements

Output as JSON with keys: title, user_story, ui_ux_description, functional_requirements (array)
"""
```

### 2. Workflow Orchestrator Pattern (Single File)

```python
# backend/src/services/workflow_orchestrator.py
"""
GitHub Issue Workflow Orchestrator

This file contains all workflow logic in one place for easy reading and modification.

WORKFLOW STATES:
  ANALYZING → RECOMMENDATION_PENDING → CREATING → BACKLOG → READY → IN_PROGRESS → IN_REVIEW

TRANSITIONS:
  1. User message → AI generates recommendation (ANALYZING → RECOMMENDATION_PENDING)
  2. User confirms → Create GitHub Issue (RECOMMENDATION_PENDING → CREATING)
  3. Issue created → Add to project with Backlog status (CREATING → BACKLOG)
  4. Auto-transition → Update to Ready status (BACKLOG → READY)
  5. Status detection → Move to In Progress, assign Copilot (READY → IN_PROGRESS)
  6. Completion detection → Move to In Review, assign owner (IN_PROGRESS → IN_REVIEW)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Workflow states for tracking issue lifecycle."""
    ANALYZING = "analyzing"
    RECOMMENDATION_PENDING = "recommendation_pending"
    CREATING = "creating"
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    ERROR = "error"


@dataclass
class WorkflowContext:
    """Context passed through workflow transitions."""
    session_id: str
    project_id: str
    access_token: str
    recommendation_id: Optional[str] = None
    issue_id: Optional[str] = None
    issue_number: Optional[int] = None
    current_state: WorkflowState = WorkflowState.ANALYZING


class WorkflowOrchestrator:
    """Orchestrates the full GitHub issue creation and status workflow."""

    def __init__(self, ai_service, github_service):
        self.ai = ai_service
        self.github = github_service

    # ──────────────────────────────────────────────────────────────────
    # STEP 1: Generate AI Recommendation
    # ──────────────────────────────────────────────────────────────────
    async def generate_recommendation(self, ctx: WorkflowContext, user_input: str):
        """Generate issue recommendation from user feature request."""
        logger.info("Generating recommendation for: %s", user_input[:50])
        # ... implementation
        ctx.current_state = WorkflowState.RECOMMENDATION_PENDING

    # ──────────────────────────────────────────────────────────────────
    # STEP 2: Create GitHub Issue
    # ──────────────────────────────────────────────────────────────────
    async def create_issue(self, ctx: WorkflowContext, recommendation):
        """Create GitHub Issue from confirmed recommendation."""
        logger.info("Creating issue: %s", recommendation.title)
        ctx.current_state = WorkflowState.CREATING
        # ... implementation

    # ──────────────────────────────────────────────────────────────────
    # STEP 3: Add to Project
    # ──────────────────────────────────────────────────────────────────
    async def add_to_project(self, ctx: WorkflowContext):
        """Add created issue to GitHub Project with Backlog status."""
        logger.info("Adding issue %s to project", ctx.issue_id)
        # ... implementation
        ctx.current_state = WorkflowState.BACKLOG

    # ──────────────────────────────────────────────────────────────────
    # STEP 4: Auto-transition to Ready
    # ──────────────────────────────────────────────────────────────────
    async def transition_to_ready(self, ctx: WorkflowContext):
        """Automatically transition from Backlog to Ready."""
        logger.info("Transitioning issue %s to Ready", ctx.issue_id)
        # ... implementation
        ctx.current_state = WorkflowState.READY

    # ──────────────────────────────────────────────────────────────────
    # STEP 5: Handle Ready Detection
    # ──────────────────────────────────────────────────────────────────
    async def handle_ready_status(self, ctx: WorkflowContext):
        """When Ready status detected: move to In Progress, assign Copilot."""
        logger.info("Issue %s is Ready, assigning Copilot", ctx.issue_id)
        # ... implementation
        ctx.current_state = WorkflowState.IN_PROGRESS

    # ──────────────────────────────────────────────────────────────────
    # STEP 6: Handle Completion Detection
    # ──────────────────────────────────────────────────────────────────
    async def handle_completion(self, ctx: WorkflowContext):
        """When completion detected: move to In Review, assign owner."""
        logger.info("Issue %s complete, assigning owner for review", ctx.issue_id)
        # ... implementation
        ctx.current_state = WorkflowState.IN_REVIEW

    # ──────────────────────────────────────────────────────────────────
    # FULL WORKFLOW: Execute all steps
    # ──────────────────────────────────────────────────────────────────
    async def execute_full_workflow(self, ctx: WorkflowContext, recommendation):
        """Execute the complete workflow from confirmation to Ready status."""
        try:
            await self.create_issue(ctx, recommendation)
            await self.add_to_project(ctx)
            await self.transition_to_ready(ctx)
            return True
        except Exception as e:
            logger.error("Workflow failed: %s", e)
            ctx.current_state = WorkflowState.ERROR
            return False
```

### 3. GitHub Issue Creation (REST API)

```python
# In backend/src/services/github_projects.py

async def create_issue(
    self,
    access_token: str,
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: list[str] = None,
) -> dict:
    """
    Create a GitHub Issue using REST API.
    
    Returns dict with: id, node_id, number, html_url
    """
    response = await self._client.post(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        json={"title": title, "body": body, "labels": labels or []},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    response.raise_for_status()
    return response.json()
```

### 4. Add Issue to Project (GraphQL)

```python
# GraphQL mutation to add existing issue to project
ADD_ISSUE_TO_PROJECT_MUTATION = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item {
      id
    }
  }
}
"""
```

### 5. Issue Assignment (REST API)

```python
async def assign_issue(
    self,
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    assignees: list[str],
) -> bool:
    """Assign users to a GitHub Issue."""
    response = await self._client.patch(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
        json={"assignees": assignees},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    return response.status_code == 200
```

## Testing

### Manual Testing Flow

1. **Start the application**
   ```bash
   cd backend && uvicorn src.main:app --reload
   ```

2. **Login with GitHub** and select a project

3. **Send a feature request**:
   > "I need a feature that allows users to filter tasks by date range"

4. **Verify AI recommendation** appears with:
   - Title
   - User story
   - UI/UX description
   - Functional requirements

5. **Confirm the recommendation**

6. **Verify in GitHub**:
   - Issue created in repository
   - Issue attached to project
   - Status shows "Ready"

### Unit Tests

```python
# backend/tests/unit/test_workflow_orchestrator.py

@pytest.mark.asyncio
async def test_generate_recommendation():
    """Test AI generates valid recommendation structure."""
    orchestrator = WorkflowOrchestrator(mock_ai, mock_github)
    ctx = WorkflowContext(session_id="test", project_id="proj", access_token="token")
    
    result = await orchestrator.generate_recommendation(ctx, "Add CSV export")
    
    assert result.title is not None
    assert len(result.functional_requirements) > 0
    assert ctx.current_state == WorkflowState.RECOMMENDATION_PENDING
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "GitHub Copilot user not found" | Add `github-copilot` as repository collaborator or use different username |
| "Cannot update project item field" | Ensure field ID and option ID are fetched dynamically from project metadata |
| "Rate limit exceeded" | Implement exponential backoff, reduce polling frequency |
| "AI generates generic responses" | Improve prompt with more examples, increase temperature slightly |

## Success Verification

- [ ] Feature request generates structured recommendation
- [ ] Confirming recommendation creates real GitHub Issue (not draft)
- [ ] Issue appears in GitHub Project with "Backlog" status
- [ ] Status automatically updates to "Ready"
- [ ] Status detection triggers "In Progress" + Copilot assignment
- [ ] Completion detection triggers "In Review" + owner assignment
