# Contract: Frontend API Response Schemas (Zod)

**Feature**: 047-advanced-testing  
**Purpose**: Define Zod schemas for the 5 highest-traffic frontend API responses, enabling runtime validation in development/test mode.

## Schema Definitions

### 1. ProjectsListResponse

Endpoint: `projectsApi.getUserProjects()` → `GET /api/projects`

```typescript
import { z } from "zod";

const StatusColumnSchema = z.object({
  id: z.string(),
  name: z.string(),
});

const ProjectSchema = z.object({
  project_id: z.string(),
  owner_id: z.string(),
  owner_login: z.string(),
  name: z.string(),
  type: z.enum(["organization", "user", "repository"]),
  url: z.string(),
  description: z.string().optional(),
  status_columns: z.array(StatusColumnSchema),
  item_count: z.number().optional(),
  cached_at: z.string(),
});

export const ProjectListResponseSchema = z.object({
  projects: z.array(ProjectSchema),
});
```

### 2. BoardDataResponse

Endpoint: `boardApi.getBoardData()` → `GET /api/board/{projectId}`

```typescript
const RateLimitInfoSchema = z.object({
  remaining: z.number(),
  limit: z.number(),
  reset_at: z.string().nullable(),
}).nullable().optional();

const BoardProjectSchema = z.object({
  id: z.string(),
  title: z.string(),
  number: z.number(),
  owner: z.string(),
  url: z.string(),
  description: z.string().nullable().optional(),
});

const BoardIssueSchema = z.object({
  id: z.string(),
  title: z.string(),
  number: z.number(),
  status: z.string(),
  assignees: z.array(z.string()),
  labels: z.array(z.string()),
  url: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

const BoardColumnSchema = z.object({
  name: z.string(),
  items: z.array(BoardIssueSchema),
});

export const BoardDataResponseSchema = z.object({
  project: BoardProjectSchema,
  columns: z.array(BoardColumnSchema),
  rate_limit: RateLimitInfoSchema,
});
```

### 3. ChatMessagesResponse

Endpoint: `chatApi.getMessages()` → `GET /api/chat/messages`

```typescript
const ChatMessageSchema = z.object({
  message_id: z.string(),
  session_id: z.string(),
  sender_type: z.enum(["user", "assistant", "system"]),
  content: z.string(),
  action_type: z.string().optional(),
  action_data: z.record(z.unknown()).optional(),
  timestamp: z.string(),
  status: z.string().optional(),
});

export const ChatMessagesResponseSchema = z.object({
  messages: z.array(ChatMessageSchema),
});
```

### 4. EffectiveUserSettings

Endpoint: `settingsApi.getUserSettings()` → `GET /api/settings`

```typescript
const AIPreferencesSchema = z.object({
  provider: z.enum(["copilot", "azure_openai"]),
  model: z.string(),
  temperature: z.number(),
  agent_model: z.string(),
});

const DisplayPreferencesSchema = z.object({
  theme: z.enum(["dark", "light"]),
  default_view: z.enum(["chat", "board", "settings"]),
  sidebar_collapsed: z.boolean(),
});

const WorkflowDefaultsSchema = z.object({
  default_repository: z.string().nullable(),
  default_assignee: z.string(),
  copilot_polling_interval: z.number(),
});

const NotificationPreferencesSchema = z.object({
  task_status_change: z.boolean(),
  agent_completion: z.boolean(),
  new_recommendation: z.boolean(),
  chat_mention: z.boolean(),
});

export const EffectiveUserSettingsSchema = z.object({
  ai: AIPreferencesSchema,
  display: DisplayPreferencesSchema,
  workflow: WorkflowDefaultsSchema,
  notifications: NotificationPreferencesSchema,
});
```

### 5. PipelineStateInfo

Endpoint: `workflowApi.getPipelineState()` → `GET /api/workflow/pipeline/{issueNumber}/state`

```typescript
export const PipelineStateInfoSchema = z.object({
  issue_number: z.number(),
  project_id: z.string(),
  status: z.string(),
  agents: z.array(z.string()),
  current_agent_index: z.number(),
  current_agent: z.string().nullable(),
  completed_agents: z.array(z.string()),
  is_complete: z.boolean(),
  started_at: z.string().nullable(),
  error: z.string().nullable(),
});
```

## Integration Pattern

In `api.ts`, wrap response parsing in dev-mode-only validation:

```typescript
import { ProjectListResponseSchema } from './schemas/projects';

// Helper for dev-mode validation
function validateResponse<T>(schema: z.ZodType<T>, data: unknown, endpoint: string): T {
  if (import.meta.env.DEV) {
    try {
      return schema.parse(data);
    } catch (error) {
      console.error(`[API Schema Validation] ${endpoint}:`, error);
      throw error;
    }
  }
  return data as T;
}

// Usage in projectsApi:
async getUserProjects(): Promise<ProjectListResponse> {
  const data = await fetchJson('/api/projects');
  return validateResponse(ProjectListResponseSchema, data, 'getUserProjects');
}
```

## Validation Behavior

- **Dev mode** (`import.meta.env.DEV`): Logs validation errors to console and rethrows schema failures
- **Test mode**: Schema validation failures surface as test failures via thrown `ZodError`
- **Production**: Schema code is tree-shaken by Vite; zero runtime overhead
