# Research: AI-Assisted GitHub Issue Creation and Workflow Management

**Date**: February 2, 2026  
**Spec**: [spec.md](./spec.md)

## Technology Decisions

### 1. GitHub Issues API vs Draft Issues

**Decision**: Use GitHub REST API to create real Issues (not Draft Issues), then add them to Projects via GraphQL API.

**Rationale**: 
- User requirement explicitly states "No Draft Issues, create open Issues from the start"
- GitHub Issues REST API (`POST /repos/{owner}/{repo}/issues`) creates real issues with full metadata support
- GraphQL `addProjectV2ItemById` mutation can attach existing issues to projects
- Draft issues have limited functionality and aren't visible outside the project board

**Alternatives Considered**:
- GraphQL `addProjectV2DraftIssue` - Rejected because user wants real Issues
- Creating issues via GraphQL `createIssue` mutation - Works but REST API is simpler for this use case

### 2. GitHub Projects V2 Status Management

**Decision**: Use GraphQL API with `updateProjectV2ItemFieldValue` mutation for status updates.

**Rationale**:
- GitHub Projects V2 uses GraphQL exclusively for field value updates
- Status is a "SingleSelect" field type requiring the field ID and option ID
- Existing `GitHubProjectsService` in codebase already implements this pattern
- REST API cannot update project-specific custom fields

**API Pattern**:
```graphql
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { singleSelectOptionId: $optionId }
    }
  ) {
    projectV2Item { id }
  }
}
```

### 3. GitHub Issue Assignee Management

**Decision**: Use REST API `PATCH /repos/{owner}/{repo}/issues/{issue_number}` with `assignees` array.

**Rationale**:
- REST API provides straightforward assignee management
- Supports multiple assignees via array
- "GitHub Copilot" assignment requires a valid GitHub user/bot account with repo access
- Need to verify assignee exists before assignment using `GET /repos/{owner}/{repo}/assignees/{assignee}`

**Key Finding**: GitHub Copilot user must be added to repository collaborators or organization members to be assignable.

### 4. AI Recommendation Generation

**Decision**: Extend existing `AIAgentService` with new prompt template for issue recommendation generation.

**Rationale**:
- Existing Azure OpenAI integration already configured in `backend/src/services/ai_agent.py`
- Supports both Azure OpenAI SDK and Azure AI Inference SDK
- DRY principle: reuse existing `_call_completion` method
- Add new prompt template following existing pattern in `src/prompts/`

**Output Structure**: AI generates structured JSON with:
- `title`: Issue title (concise, actionable)
- `user_story`: User story in "As a... I want... So that..." format
- `ui_ux_description`: UI/UX description for implementation guidance
- `functional_requirements`: Array of specific, testable requirements

### 5. Workflow State Machine (Single-File Design)

**Decision**: Create `backend/src/services/workflow_orchestrator.py` containing all workflow logic in one readable file.

**Rationale**:
- User explicitly requested: "contain it within 1 file, make it easy for a human to read and update the logical flow"
- State machine pattern makes transitions explicit and auditable
- Single file enables: understanding flow at a glance, easy modification, clear debugging
- DRY: shared helper functions for common operations (status update, assignment)

**State Machine**:
```
[Feature Request] → AI generates recommendation
       ↓
[User Confirms] → Create GitHub Issue (REST)
       ↓
[Issue Created] → Add to Project (GraphQL) → Status: "Backlog"
       ↓
[Auto-transition] → Status: "Ready"
       ↓
[Detection: Ready] → Status: "In Progress" + Assign Copilot
       ↓
[Detection: Complete] → Status: "In Review" + Assign Owner
```

### 6. Status Change Detection

**Decision**: Use polling mechanism with `poll_project_changes` (already implemented).

**Rationale**:
- GitHub Webhooks require public endpoint and infrastructure complexity
- Existing codebase uses polling via `GitHubProjectsService.poll_project_changes`
- Polling interval of 10-30 seconds meets success criteria (transitions within 10 seconds)
- DRY: leverage existing `_detect_changes` method

**Alternative Considered**:
- GitHub Webhooks - More complex setup, requires ngrok or public server for local dev

### 7. Project Owner Determination

**Decision**: Use repository owner as default Project Owner (per user clarification).

**Rationale**:
- User selected Option A: "Use the repository owner as the default Project Owner"
- Fetch via REST API `GET /repos/{owner}/{repo}` → `owner.login`
- Simple and works for most individual/small team repos
- Can be extended later to support explicit configuration

### 8. Issue Content Formatting

**Decision**: Use Markdown template for GitHub Issue body with clear sections.

**Rationale**:
- GitHub renders Markdown natively
- Structured sections improve readability
- Enables parsing/updating sections programmatically if needed

**Template Structure**:
```markdown
## User Story
{user_story}

## UI/UX Description
{ui_ux_description}

## Functional Requirements
- [ ] {requirement_1}
- [ ] {requirement_2}
...

---
*Generated by AI Assistant from feature request*
```

## Dependencies

| Dependency | Purpose | Version | Source |
|------------|---------|---------|--------|
| `azure-ai-inference` | Azure OpenAI chat completions | >=1.0.0b1 | Already in pyproject.toml |
| `httpx` | HTTP client for GitHub API | >=0.26.0 | Already in pyproject.toml |
| `pydantic` | Data models and validation | >=2.5.0 | Already in pyproject.toml |

No new dependencies required - all functionality can be built with existing packages.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GitHub API rate limits | Medium | High | Implement exponential backoff, cache responses |
| "GitHub Copilot" user not assignable | High | Medium | Verify user exists before assignment, provide clear error |
| AI generates poor recommendations | Medium | Medium | Include examples in prompt, allow user editing before confirm |
| Status field IDs change | Low | Medium | Fetch field metadata dynamically, don't hardcode IDs |

## Integration Points

1. **Chat API** (`backend/src/api/chat.py`): 
   - Add new message handler for feature request intent
   - Create `ActionType.ISSUE_CREATE` for confirmation flow

2. **AI Agent Service** (`backend/src/services/ai_agent.py`):
   - Add `generate_issue_recommendation()` method
   - New prompt template in `backend/src/prompts/`

3. **GitHub Projects Service** (`backend/src/services/github_projects.py`):
   - Add `create_issue()` method (REST API)
   - Add `add_issue_to_project()` method (GraphQL)
   - Add `assign_issue()` method (REST API)

4. **Workflow Orchestrator** (`backend/src/services/workflow_orchestrator.py`):
   - New file containing all workflow state machine logic
   - Coordinates AI → Issue Creation → Project → Status transitions
