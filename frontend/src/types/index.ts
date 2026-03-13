/**
 * TypeScript types for Agent Projects API.
 *
 * Types are auto-derived from the backend OpenAPI schema where available.
 * Frontend-only types (UI state, form state, etc.) are defined manually below.
 *
 * To regenerate: `npm run generate:types`
 */

import type { components } from './generated';

/** Shorthand for accessing generated schema types. */
type Schema = components['schemas'];

/** Makes specific keys of T both required and non-nullable. */
type WithRequired<T, K extends keyof T> = Omit<T, K> & { [P in K]-?: NonNullable<T[P]> };

// ============ Generated Type Aliases — Enums ============

export type ProjectType = Schema['ProjectType'];
export type SenderType = Schema['SenderType'];
export type ActionType = Schema['ActionType'];
export type ProposalStatus = Schema['ProposalStatus'];
export type ContentType = Schema['ContentType'];
export type PRState = Schema['PRState'];
export type StatusColor = Schema['StatusColor'];
export type ScheduleType = Schema['ScheduleType'];
export type ChoreStatus = Schema['ChoreStatus'];
export type SignalConnectionStatus = Schema['SignalConnectionStatus'];
export type SignalNotificationMode = Schema['SignalNotificationMode'];
export type SignalLinkStatus = Schema['SignalLinkStatus'];
export type AIProviderType = Schema['AIProvider'];
export type ThemeModeType = Schema['ThemeMode'];
export type DefaultViewType = Schema['DefaultView'];

// ============ Generated Type Aliases — User & Auth ============

export type User = Schema['UserResponse'];
export type StatusColumn = Schema['StatusColumn'];
export type Project = Schema['GitHubProject'];
export type ProjectListResponse = Schema['ProjectListResponse'];

// ============ Generated Type Aliases — Tasks ============

export type Task = Schema['Task'];
export type TaskCreateRequest = Schema['TaskCreateRequest'];
export type TaskListResponse = Schema['TaskListResponse'];

// ============ Generated Type Aliases — Chat ============
// ChatMessage: make message_id/timestamp required (always present in responses),
// add frontend-only status field, and narrow action_data for safe casting.

type _ChatMessage = WithRequired<Schema['ChatMessage'], 'message_id' | 'timestamp'>;
export type ChatMessage = Omit<_ChatMessage, 'action_data'> & {
  status?: MessageStatus;
  action_data?: ActionData | null;
};
export type ChatMessageRequest = Schema['ChatMessageRequest'];
export type ChatMessagesResponse = Omit<Schema['ChatMessagesResponse'], 'messages'> & {
  messages: ChatMessage[];
};
export type FileUploadResponse = Schema['FileUploadResponse'];

// ============ Generated Type Aliases — Proposals ============

export type AITaskProposal = Schema['AITaskProposal'];
export type ProposalConfirmRequest = Schema['ProposalConfirmRequest'];

// ============ Generated Type Aliases — Agents ============

export type AgentAssignment = Schema['AgentAssignment'];
export type AvailableAgent = Schema['AvailableAgent'];

// ============ Generated Type Aliases — Workflow ============

export type WorkflowResult = Schema['WorkflowResult'];
export type PipelineIssueLaunchRequest = Schema['PipelineIssueLaunchRequest'];
export type WorkflowConfiguration = Schema['WorkflowConfiguration'];
export type WorkflowDefaults = Schema['WorkflowDefaults'];
export type WorkflowDefaultsUpdate = Schema['WorkflowDefaultsUpdate'];
export type PipelineStateInfo = Schema['PipelineStateItem'];

// ============ Generated Type Aliases — Board ============

export type BoardProject = Schema['BoardProject'];
export type BoardItem = Omit<Schema['BoardItem'], 'assignees' | 'linked_prs' | 'sub_issues' | 'labels'> & {
  assignees: Schema['Assignee'][];
  linked_prs: Schema['LinkedPR'][];
  sub_issues: SubIssue[];
  labels: Schema['Label'][];
};
export type BoardColumn = Omit<Schema['BoardColumn'], 'items'> & { items: BoardItem[] };
export type BoardDataResponse = Omit<Schema['BoardDataResponse'], 'columns'> & {
  columns: BoardColumn[];
};
export type BoardProjectListResponse = Schema['BoardProjectListResponse'];
export type LinkedPR = Schema['LinkedPR'];
export type SubIssue = WithRequired<Schema['SubIssue'], 'assignees' | 'linked_prs'>;
export type RateLimitInfo = Schema['RateLimitInfo'];
export type BoardAssignee = Schema['Assignee'];
export type BoardStatusOption = Schema['StatusOption'];
export type BoardStatusField = Schema['StatusField'];
export type BoardCustomFieldValue = Schema['CustomFieldValue'];
export type BoardRepository = Schema['Repository'];
export type BoardLabel = Schema['Label'];

// ============ Generated Type Aliases — Settings ============

export type AIPreferences = Schema['AIPreferences'];
export type AIPreferencesUpdate = Schema['AIPreferencesUpdate'];
export type DisplayPreferences = Schema['DisplayPreferences'];
export type DisplayPreferencesUpdate = Schema['DisplayPreferencesUpdate'];
export type NotificationPreferences = Schema['NotificationPreferences'];
export type NotificationPreferencesUpdate = Schema['NotificationPreferencesUpdate'];
export type EffectiveUserSettings = Schema['EffectiveUserSettings'];
export type GlobalSettings = WithRequired<Schema['GlobalSettingsResponse'], 'allowed_models'>;
export type GlobalSettingsUpdate = Schema['GlobalSettingsUpdate'];
export type UserPreferencesUpdate = Schema['UserPreferencesUpdate'];
export type ProjectBoardConfig = WithRequired<Schema['ProjectBoardConfig'], 'column_order' | 'collapsed_columns'>;
export type ProjectAgentMapping = Schema['ProjectAgentMapping'];
export type ProjectSpecificSettings = Schema['ProjectSpecificSettings'];
export type EffectiveProjectSettings = Schema['EffectiveProjectSettings'];
export type ProjectSettingsUpdate = Schema['ProjectSettingsUpdate'];

// ============ Generated Type Aliases — Models ============

export type ModelOption = Schema['ModelOption'];
export type ModelsResponse = Schema['ModelsResponse'];

// ============ Generated Type Aliases — Signal ============

export type SignalConnection = Schema['SignalConnectionResponse'];
export type SignalLinkResponse = Schema['SignalLinkResponse'];
export type SignalLinkStatusResponse = Schema['SignalLinkStatusResponse'];
export type SignalPreferences = Schema['SignalPreferencesResponse'];
export type SignalPreferencesUpdate = Schema['SignalPreferencesUpdate'];
export type SignalBanner = Schema['SignalBanner'];
export type SignalBannersResponse = Schema['SignalBannersResponse'];

// ============ Generated Type Aliases — MCP Configuration ============

export type McpConfiguration = Schema['McpConfigurationResponse'];
export type McpConfigurationListResponse = Schema['McpConfigurationListResponse'];
export type McpConfigurationCreate = Schema['McpConfigurationCreate'];

// ============ Generated Type Aliases — Cleanup ============

export type BranchInfo = Schema['BranchInfo'];
export type PullRequestInfo = Schema['PullRequestInfo'];
export type OrphanedIssueInfo = Schema['OrphanedIssueInfo'];
export type CleanupPreflightResponse = Schema['CleanupPreflightResponse'];
export type CleanupItemResult = Schema['CleanupItemResult'];
export type CleanupExecuteRequest = Schema['CleanupExecuteRequest'];
export type CleanupExecuteResponse = Schema['CleanupExecuteResponse'];
export type CleanupAuditLogEntry = Schema['CleanupAuditLogRow'];
export type CleanupHistoryResponse = Schema['CleanupHistoryResponse'];

// ============ Generated Type Aliases — Chores ============

export type Chore = Schema['Chore'];
export type ChoreCreate = Schema['ChoreCreate'];
export type ChoreTemplate = Schema['ChoreTemplate'];
export type ChoreUpdate = Schema['ChoreUpdate'];
export type ChoreTriggerResult = Schema['ChoreTriggerResult'];
export type EvaluateChoreTriggersResponse = Schema['EvaluateChoreTriggersResponse'];
export type ChoreChatMessage = Schema['ChoreChatMessage'];
export type ChoreChatResponse = Schema['ChoreChatResponse'];
export type ChoreInlineUpdate = Schema['ChoreInlineUpdate'];
export type ChoreInlineUpdateResponse = Schema['ChoreInlineUpdateResponse'];
export type ChoreCreateWithConfirmation = Schema['ChoreCreateWithConfirmation'];
export type ChoreCreateResponse = Schema['ChoreCreateResponse'];

// ============ Generated Type Aliases — Pipeline ============

export type PipelineAgentNode = WithRequired<Schema['PipelineAgentNode'], 'tool_ids' | 'config'>;
export type ExecutionGroup = Omit<Schema['ExecutionGroup'], 'agents'> & {
  agents: PipelineAgentNode[];
};
export type PipelineStage = Omit<Schema['PipelineStage'], 'groups' | 'agents'> & {
  groups: ExecutionGroup[];
  agents: PipelineAgentNode[];
};
export type PipelineConfig = Omit<Schema['PipelineConfig'], 'stages'> & {
  stages: PipelineStage[];
};
export type PipelineConfigSummary = Omit<Schema['PipelineConfigSummary'], 'stages'> & {
  stages: PipelineStage[];
};
export type PipelineConfigListResponse = Omit<Schema['PipelineConfigListResponse'], 'pipelines'> & {
  pipelines: PipelineConfigSummary[];
};
export type PipelineConfigCreate = Schema['PipelineConfigCreate'];
export type PipelineConfigUpdate = Schema['PipelineConfigUpdate'];
export type ProjectPipelineAssignment = Schema['ProjectPipelineAssignment'];

// ============ Generated Type Aliases — MCP Tools ============

export type McpToolConfig = Schema['McpToolConfigResponse'];
export type McpToolConfigCreate = Schema['McpToolConfigCreate'];
export type McpToolConfigUpdate = Schema['McpToolConfigUpdate'];
export type McpToolConfigListResponse = Schema['McpToolConfigListResponse'];
export type McpToolSyncResult = Schema['McpToolConfigSyncResult'];
export type RepoMcpServerConfig = WithRequired<Schema['RepoMcpServerConfig'], 'source_paths'>;
export type RepoMcpServerUpdate = Schema['RepoMcpServerUpdate'];
export type RepoMcpConfigResponse = Omit<Schema['RepoMcpConfigResponse'], 'paths_checked' | 'available_paths' | 'servers'> & {
  paths_checked: string[];
  available_paths: string[];
  servers: RepoMcpServerConfig[];
};
export type McpPreset = Schema['McpPresetResponse'];
export type McpPresetListResponse = Schema['McpPresetListResponse'];
export type ToolDeleteResult = WithRequired<Schema['ToolDeleteResult'], 'affected_agents'>;

// ============ Frontend-Only Types ============
// These types exist only in the frontend and are not in the API schema.

// -- Auth (not exposed via OpenAPI) --

export interface AuthResponse {
  user: User;
  message: string;
}

// -- Chat Action Data --

export interface TaskCreateActionData {
  proposal_id: string;
  task_id?: string;
  status: ProposalStatus;
  proposed_title?: string;
  proposed_description?: string;
}

export interface StatusUpdateActionData {
  task_id: string;
  old_status?: string;
  new_status?: string;
  confirmed?: boolean;
  proposal_id?: string;
  task_title?: string;
  current_status?: string;
  target_status?: string;
  status_option_id?: string;
  status_field_id?: string;
  status?: string;
}

export interface ProjectSelectActionData {
  project_id: string;
  project_name: string;
}

export type ActionData =
  | TaskCreateActionData
  | StatusUpdateActionData
  | ProjectSelectActionData
  | IssueCreateActionData;

export type MessageStatus = 'pending' | 'sent' | 'failed';

// -- @Mention Types --

/** Represents a single @mention reference within the chat input. */
export interface MentionToken {
  pipelineId: string;
  pipelineName: string;
  isValid: boolean;
  position: number;
}

/** Internal state managed by the useMentionAutocomplete hook. */
export interface MentionInputState {
  isAutocompleteOpen: boolean;
  filterQuery: string;
  highlightedIndex: number;
  mentionTriggerOffset: number | null;
  activePipelineId: string | null;
  activePipelineName: string | null;
  tokens: MentionToken[];
  hasInvalidTokens: boolean;
}

/** A pipeline matching the current filter query for autocomplete display. */
export interface MentionFilterResult {
  pipeline: PipelineConfigSummary;
  matchIndices: [number, number][];
}

// -- Chat Enhancement Types --

/** State of a file pending upload or already uploaded */
export interface FileAttachment {
  id: string;
  file: File;
  filename: string;
  fileSize: number;
  contentType: string;
  status: 'pending' | 'uploading' | 'uploaded' | 'error';
  progress: number;
  fileUrl: string | null;
  error: string | null;
}

/** Voice input recording state */
export interface VoiceInputState {
  isSupported: boolean;
  isRecording: boolean;
  isProcessing: boolean;
  interimTranscript: string;
  finalTranscript: string;
  error: string | null;
}

/** AI Enhance toggle state */
export interface ChatPreferences {
  aiEnhance: boolean;
}

/** File upload validation constants */
export const FILE_VALIDATION = {
  maxFileSize: 10 * 1024 * 1024, // 10 MB
  maxFilesPerMessage: 5,
  allowedImageTypes: ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'],
  allowedDocTypes: ['.pdf', '.txt', '.md', '.csv', '.json', '.yaml', '.yml'],
  allowedArchiveTypes: ['.zip'],
  blockedTypes: ['.exe', '.sh', '.bat', '.cmd', '.js', '.py', '.rb'],
} as const;

export const ALLOWED_TYPES = [
  ...FILE_VALIDATION.allowedImageTypes,
  ...FILE_VALIDATION.allowedDocTypes,
  ...FILE_VALIDATION.allowedArchiveTypes,
];

/** File upload error response from backend */
export interface FileUploadError {
  filename: string;
  error: string;
  error_code: string;
}

// -- API Error --

export interface APIError {
  error: string;
  details?: Record<string, unknown>;
}

// -- Issue Recommendation --

export type IssuePriority = 'P0' | 'P1' | 'P2' | 'P3';

export type IssueSize = 'XS' | 'S' | 'M' | 'L' | 'XL';

export type IssueLabel =
  | 'feature'
  | 'bug'
  | 'enhancement'
  | 'refactor'
  | 'documentation'
  | 'testing'
  | 'infrastructure'
  | 'frontend'
  | 'backend'
  | 'database'
  | 'api'
  | 'ai-generated'
  | 'good first issue'
  | 'help wanted'
  | 'security'
  | 'performance'
  | 'accessibility'
  | 'ux';

export interface IssueMetadata {
  priority: IssuePriority;
  size: IssueSize;
  estimate_hours: number;
  start_date: string;
  target_date: string;
  labels: IssueLabel[];
  assignees?: string[];
  milestone?: string | null;
  branch?: string | null;
}

export interface RepositoryMetadata {
  repo_key: string;
  labels: Array<{ name: string; color: string; description: string }>;
  branches: Array<{ name: string; protected: boolean }>;
  milestones: Array<{ number: number; title: string; due_on: string | null; state: string }>;
  collaborators: Array<{ login: string; avatar_url: string }>;
  fetched_at: string;
  is_stale: boolean;
  source: 'fresh' | 'cache' | 'fallback';
}

export interface IssueRecommendation {
  recommendation_id: string;
  session_id: string;
  original_input: string;
  title: string;
  user_story: string;
  ui_ux_description: string;
  functional_requirements: string[];
  metadata: IssueMetadata;
  status: RecommendationStatus;
  created_at: string;
  confirmed_at?: string;
}

export interface IssueCreateActionData {
  recommendation_id: string;
  proposed_title: string;
  user_story: string;
  ui_ux_description: string;
  functional_requirements: string[];
  metadata?: IssueMetadata;
  status: RecommendationStatus;
}

export type RecommendationStatus = 'pending' | 'confirmed' | 'rejected';

export type AgentSource = 'builtin' | 'repository';

// -- Agent Preset (frontend-only) --

export interface AgentPreset {
  id: string;
  label: string;
  description: string;
  mappings: Record<string, AgentAssignment[]>;
}

// -- Agent Notification (WebSocket) --

export interface AgentNotification {
  type: 'agent_assigned' | 'agent_completed';
  issue_number: number;
  agent_name: string;
  status: string;
  next_agent: string | null;
  timestamp: string;
}

// -- Status Change Proposal --

export interface StatusChangeProposal {
  proposal_id: string;
  task_id: string;
  task_title: string;
  current_status: string;
  target_status: string;
  status_option_id: string;
  status_field_id: string;
  status: string;
}

// -- Board UI Types --

export type RefreshErrorType = 'rate_limit' | 'network' | 'auth' | 'server' | 'unknown';

export interface RefreshError {
  type: RefreshErrorType;
  message: string;
  rateLimitInfo?: RateLimitInfo;
  retryAfter?: Date;
}

// -- Chore UI Types --

export interface FeaturedRitualCard {
  choreId: string;
  choreName: string;
  stat: string;
  statValue: number;
}

export interface FeaturedRituals {
  nextRun: FeaturedRitualCard | null;
  mostRecentlyRun: FeaturedRitualCard | null;
  mostRun: FeaturedRitualCard | null;
}

export interface ChoreEditState {
  original: Chore;
  current: Partial<ChoreInlineUpdate>;
  isDirty: boolean;
  fileSha: string | null;
}

export interface ChoreCounterData {
  choreId: string;
  remaining: number;
  totalThreshold: number;
  issuesSinceLastRun: number;
}

// -- Solune UI Redesign Types --

export interface NavRoute {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

export interface SidebarState {
  isCollapsed: boolean;
}

export interface RecentInteraction {
  item_id: string;
  title: string;
  number?: number;
  repository?: {
    owner: string;
    name: string;
  };
  updatedAt: string;
  status: string;
  statusColor: StatusColor;
}

export interface Notification {
  id: string;
  type: 'agent' | 'chore';
  title: string;
  timestamp: string;
  read: boolean;
  source?: string;
}

// -- Pipeline UI Types --

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  context_window_size?: number;
  cost_tier?: 'economy' | 'standard' | 'premium';
  capability_category?: string;
}

export interface ModelGroup {
  provider: string;
  models: AIModel[];
}

export type PipelineBoardState = 'empty' | 'creating' | 'editing';

export interface PipelineModelOverride {
  mode: 'auto' | 'specific' | 'mixed';
  modelId: string;
  modelName: string;
}

export interface PipelineValidationErrors {
  name?: string;
  stages?: string;
  [key: string]: string | undefined;
}

export interface PresetPipelineDefinition {
  presetId: string;
  name: string;
  description: string;
  stages: PipelineStage[];
}

export interface FlowGraphNode {
  id: string;
  label: string;
  agentCount: number;
  x: number;
  y: number;
}

export interface PresetSeedResult {
  seeded: string[];
  skipped: string[];
  total: number;
}

// -- MCP Tools UI Types --

export type McpToolSyncStatus = 'synced' | 'pending' | 'error';

export interface ToolChip {
  id: string;
  name: string;
  description: string;
}
