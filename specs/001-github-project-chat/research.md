# Research: GitHub Projects Chat Interface

**Date**: 2026-01-30
**Feature**: 001-github-project-chat

## Technology Decisions

### 1. Backend Framework: FastAPI

**Decision**: Use FastAPI with Python 3.11+

**Rationale**:
- Native async support for concurrent GitHub API and Azure OpenAI calls
- Built-in OAuth2 security utilities (`OAuth2PasswordBearer`, `Security`)
- Automatic OpenAPI documentation generation
- Pydantic v2 integration for request/response validation
- WebSocket support for real-time updates (P3 story)

**Alternatives Considered**:
- Flask: Rejected - no native async, requires extensions for WebSocket
- Django: Rejected - too heavy for API-only backend, slower development

**Key Patterns from Context7 Research**:
```python
# OAuth2 security scheme with scopes
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"github": "GitHub API access"}
)

# Dependency injection for authentication
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate GitHub token
    pass
```

### 2. Frontend Framework: Vite + React 18

**Decision**: Use Vite as build tool with React 18 and TypeScript

**Rationale**:
- Instant dev server start with native ESM
- Lightning-fast HMR (Hot Module Replacement)
- Optimized production builds with Rollup
- First-class TypeScript support
- Minimal configuration required

**Alternatives Considered**:
- Create React App: Rejected - deprecated, slow builds
- Next.js: Rejected - SSR not needed for this SPA chat interface

### 3. AI Integration: Azure OpenAI via azure-ai-inference SDK

**Decision**: Use `azure-ai-inference` Python SDK for chat completions

**Rationale**:
- Official Microsoft SDK with full Azure OpenAI support
- Supports streaming responses for real-time chat
- Tool/function calling support for structured task extraction
- Easy migration path to Microsoft Agent Framework

**Key Patterns from Context7 Research**:
```python
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

client = ChatCompletionsClient(
    endpoint=os.environ["AZURE_AI_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_AI_KEY"])
)

# Chat completion with tool support
response = client.chat.completions.create(
    messages=[{"role": "user", "content": user_input}],
    model=deployment_name,
    tools=[task_extraction_tool],
    temperature=0.7,
    max_tokens=500
)
```

### 4. Microsoft Agent Framework Integration Plan

**Decision**: Design for future Microsoft 365 Agent SDK integration

**Rationale**:
- User requested planning for Microsoft Agent Framework
- SDK provides `AgentApplication` for multi-channel agents
- Supports Teams integration for enterprise deployment
- Built-in OAuth authorization flows

**Migration Path**:
1. MVP: Direct Azure OpenAI integration via `azure-ai-inference`
2. Phase 2: Wrap AI service in Agent-compatible structure
3. Phase 3: Full `microsoft_agents` SDK integration for Teams channel

**Key Integration Points from Context7**:
```python
from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState
from microsoft_agents.hosting.aiohttp import CloudAdapter

# Future: Agent-style message handling
@app.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"Processing: {context.activity.text}")
```

### 5. GitHub Projects V2 API

**Decision**: Use GitHub GraphQL API for Projects V2 operations

**Rationale**:
- Projects V2 only accessible via GraphQL (not REST)
- Single request can fetch project with all items
- Supports mutations for creating/updating items
- Better performance than multiple REST calls

**Key Operations Required**:
1. **List Projects**: Query user's accessible projects (org, user, repo)
2. **Get Project Items**: Query items with status, title, body
3. **Create Item**: `addProjectV2ItemById` mutation
4. **Update Status**: `updateProjectV2ItemFieldValue` mutation

**Example GraphQL Queries**:
```graphql
# List user's projects
query {
  viewer {
    projectsV2(first: 20) {
      nodes {
        id
        title
        url
      }
    }
  }
}

# Create item in project
mutation {
  addProjectV2ItemById(input: {
    projectId: "PVT_xxx"
    contentId: "ISSUE_xxx"
  }) {
    item {
      id
    }
  }
}
```

### 6. Authentication Flow: GitHub OAuth 2.0

**Decision**: Standard OAuth 2.0 Authorization Code flow with PKCE

**Rationale**:
- Required by GitHub for user authentication
- Provides access tokens for GraphQL API calls
- Supports token refresh for long sessions
- Scopes: `read:project`, `project`, `read:org`, `repo`

**Flow**:
1. Frontend redirects to GitHub authorization URL
2. User grants permissions
3. GitHub redirects back with authorization code
4. Backend exchanges code for access token
5. Token stored in encrypted session
6. Token refresh on expiration

### 7. State Management: TanStack Query (React Query)

**Decision**: Use TanStack Query for server state management

**Rationale**:
- Automatic caching and background refetching
- Built-in loading/error states
- Optimistic updates for task creation
- Reduces boilerplate vs Redux/Zustand for API state

**Alternatives Considered**:
- Redux Toolkit: Rejected - overkill for primarily server state
- Zustand: Rejected - better for local state, less API features

### 8. Real-Time Updates (P3 Story)

**Decision**: WebSocket with polling fallback

**Rationale**:
- GitHub doesn't provide webhooks for Projects V2 changes
- WebSocket enables push-based UI updates within session
- Polling fallback ensures reliability on connection issues

**Implementation**:
- Socket.io for WebSocket abstraction
- 30-second polling interval as fallback
- Optimistic UI updates for user's own changes

## Security Considerations

### Token Storage
- Backend: Encrypted in-memory session (MVP), Redis with encryption (production)
- Frontend: Never stored - all API calls through backend proxy
- Token refresh handled transparently by backend

### Rate Limiting
- GitHub API: 5000 requests/hour per user
- Implement client-side request coalescing
- Cache project lists for 5 minutes (configurable TTL)
- Queue mutations to avoid burst limits

### CORS Configuration
- Strict origin whitelist for production
- Credentials required for session cookies
- No token exposure to frontend

## Performance Optimizations

### Caching Strategy
| Data | TTL | Invalidation |
|------|-----|--------------|
| Project list | 5 min | Manual refresh, on project selection |
| Project items | 30 sec | On mutation, manual refresh |
| User session | 8 hours | On logout, token expiration |

### Request Optimization
- Batch GraphQL queries where possible
- Prefetch project items on hover
- Debounce chat input (300ms)
- Stream AI responses for perceived speed

## Dependencies Summary

### Backend (Python)
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
httpx>=0.26.0
python-jose[cryptography]>=3.3.0
azure-ai-inference>=1.0.0
pydantic>=2.5.0
python-dotenv>=1.0.0
```

### Frontend (Node.js)
```
react>=18.2.0
react-dom>=18.2.0
typescript>=5.3.0
vite>=5.0.0
@tanstack/react-query>=5.17.0
socket.io-client>=4.7.0
```
