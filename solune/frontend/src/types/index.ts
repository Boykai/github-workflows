/**
 * TypeScript types for Solune API.
 * Aligned with backend Pydantic models and OpenAPI contract.
 */

// ============ Enums ============

export type ProjectType = 'organization' | 'user' | 'repository';

export type SenderType = 'user' | 'assistant' | 'system';

export type ActionType = 'task_create' | 'status_update' | 'project_select' | 'issue_create';

export type ProposalStatus = 'pending' | 'confirmed' | 'edited' | 'cancelled';

export type RecommendationStatus = 'pending' | 'confirmed' | 'rejected';

// ============ User & Auth ============

export interface User {
  github_user_id: string;
  github_username: string;
  github_avatar_url?: string;
  selected_project_id?: string;
}

export interface AuthResponse {
  user: User;
  message: string;
}

// ============ Projects ============

export interface StatusColumn {
  field_id: string;
  name: string;
  option_id: string;
  color?: string;
}

export interface Project {
  project_id: string;
  owner_id: string;
  owner_login: string;
  name: string;
  type: ProjectType;
  url: string;
  description?: string;
  status_columns: StatusColumn[];
  item_count?: number;
  cached_at: string;
}

export interface ProjectListResponse {
  projects: Project[];
}

// ============ Tasks ============

export interface Task {
  task_id: string;
  project_id: string;
  github_item_id: string;
  github_content_id?: string;
  title: string;
  description?: string;
  status: string;
  status_option_id: string;
  assignees?: string[];
  labels?: Array<{ name: string; color: string }>;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateRequest {
  project_id: string;
  title: string;
  description?: string;
}

export interface TaskListResponse {
  tasks: Task[];
}

// ============ Chat Messages ============

export interface TaskCreateActionData {
  proposal_id: string;
  task_id?: string;
  status: ProposalStatus;
  proposed_title?: string;
  proposed_description?: string;
}

export interface StatusUpdateActionData {
  task_id: string;
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

export interface ChatMessage {
  message_id: string;
  session_id: string;
  sender_type: SenderType;
  content: string;
  action_type?: ActionType;
  action_data?: ActionData;
  timestamp: string;
  status?: MessageStatus;
}

export interface ChatMessageRequest {
  content: string;
  ai_enhance?: boolean;
  file_urls?: string[];
  pipeline_id?: string;
}

// ============ @Mention Types ============

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

// ============ Chat Enhancement Types ============

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
  allowedDocTypes: ['.pdf', '.txt', '.md', '.csv', '.json', '.yaml', '.yml', '.vtt', '.srt'],
  allowedArchiveTypes: ['.zip'],
  blockedTypes: ['.exe', '.sh', '.bat', '.cmd', '.js', '.py', '.rb'],
} as const;

export const ALLOWED_TYPES = [
  ...FILE_VALIDATION.allowedImageTypes,
  ...FILE_VALIDATION.allowedDocTypes,
  ...FILE_VALIDATION.allowedArchiveTypes,
];

/** File upload response from backend */
export interface FileUploadResponse {
  filename: string;
  file_url: string;
  file_size: number;
  content_type: string;
}

/** File upload error response from backend */
export interface FileUploadError {
  filename: string;
  error: string;
  error_code: string;
}

export interface ChatMessagesResponse {
  messages: ChatMessage[];
}

// ============ AI Task Proposals ============

export interface AITaskProposal {
  proposal_id: string;
  session_id: string;
  original_input: string;
  proposed_title: string;
  proposed_description: string;
  status: ProposalStatus;
  edited_title?: string;
  edited_description?: string;
  created_at: string;
  expires_at: string;
  pipeline_name?: string;
  pipeline_source?: string;
}

export interface ProposalConfirmRequest {
  edited_title?: string;
  edited_description?: string;
}

// ============ API Error ============

export interface APIError {
  error: string;
  details?: Record<string, unknown>;
}

// ============ Issue Recommendation (T051) ============

export type IssuePriority = 'P0' | 'P1' | 'P2' | 'P3';

export type IssueSize = 'XS' | 'S' | 'M' | 'L' | 'XL';

// Pre-defined labels for GitHub Issues
export type IssueLabel =
  // Type labels
  | 'feature'
  | 'bug'
  | 'enhancement'
  | 'refactor'
  | 'documentation'
  | 'testing'
  | 'infrastructure'
  // Scope labels
  | 'frontend'
  | 'backend'
  | 'database'
  | 'api'
  // Status labels
  | 'ai-generated'
  | 'good first issue'
  | 'help wanted'
  // Domain labels
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

// ============ Agent Assignment (004-agent-workflow-config-ui) ============

export type AgentSource = 'builtin' | 'repository';

export interface AgentAssignment {
  id: string; // UUID string
  slug: string; // Agent identifier
  display_name?: string | null;
  config?: Record<string, unknown> | null;
}

export interface AvailableAgent {
  slug: string;
  display_name: string;
  description?: string | null;
  avatar_url?: string | null;
  icon_name?: string | null;
  default_model_id?: string;
  default_model_name?: string;
  tools_count?: number | null;
  source: AgentSource;
}

export interface AgentPreset {
  id: string;
  label: string;
  description: string;
  mappings: Record<string, AgentAssignment[]>;
}

// ============ Workflow Result (T052) ============

export interface WorkflowResult {
  success: boolean;
  issue_id?: string;
  issue_number?: number;
  issue_url?: string;
  project_item_id?: string;
  current_status?: string;
  message: string;
}

export interface PipelineIssueLaunchRequest {
  issue_description: string;
  pipeline_id: string;
}

export interface WorkflowConfiguration {
  project_id: string;
  repository_owner: string;
  repository_name: string;
  copilot_assignee: string;
  review_assignee?: string;
  agent_mappings: Record<string, AgentAssignment[]>;
  status_backlog: string;
  status_ready: string;
  status_in_progress: string;
  status_in_review: string;
  enabled: boolean;
}

export interface AgentNotification {
  type: 'agent_assigned' | 'agent_completed';
  issue_number: number;
  agent_name: string;
  status: string;
  next_agent: string | null;
  timestamp: string;
}

export interface PipelineStateInfo {
  issue_number: number;
  project_id: string;
  status: string;
  agents: string[];
  current_agent_index: number;
  current_agent: string | null;
  completed_agents: string[];
  is_complete: boolean;
  started_at: string | null;
  error: string | null;
  queued: boolean;
}

// ============ Board Types ============

// ============ Status Change Proposal ============

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

// ============ Settings Types (006-sqlite-settings-storage) ============

export type AIProviderType = 'copilot' | 'azure_openai';

export type ThemeModeType = 'dark' | 'light';

export type DefaultViewType = 'chat' | 'board' | 'settings';

export interface AIPreferences {
  provider: AIProviderType;
  model: string;
  temperature: number;
  agent_model: string;
}

export interface DisplayPreferences {
  theme: ThemeModeType;
  default_view: DefaultViewType;
  sidebar_collapsed: boolean;
}

export interface WorkflowDefaults {
  default_repository: string | null;
  default_assignee: string;
  copilot_polling_interval: number;
}

export interface NotificationPreferences {
  task_status_change: boolean;
  agent_completion: boolean;
  new_recommendation: boolean;
  chat_mention: boolean;
}

export interface EffectiveUserSettings {
  ai: AIPreferences;
  display: DisplayPreferences;
  workflow: WorkflowDefaults;
  notifications: NotificationPreferences;
}

export interface GlobalSettings {
  ai: AIPreferences;
  display: DisplayPreferences;
  workflow: WorkflowDefaults;
  notifications: NotificationPreferences;
  allowed_models: string[];
}

export interface ProjectBoardConfig {
  column_order: string[];
  collapsed_columns: string[];
  show_estimates: boolean;
  queue_mode: boolean;
  auto_merge: boolean;
}

export interface ProjectAgentMapping {
  slug: string;
  display_name?: string | null;
}

export interface ProjectSpecificSettings {
  project_id: string;
  board_display_config?: ProjectBoardConfig | null;
  agent_pipeline_mappings?: Record<string, ProjectAgentMapping[]> | null;
}

export interface EffectiveProjectSettings {
  ai: AIPreferences;
  display: DisplayPreferences;
  workflow: WorkflowDefaults;
  notifications: NotificationPreferences;
  project: ProjectSpecificSettings;
}

// ── Update (PUT) request types ──

export interface AIPreferencesUpdate {
  provider?: AIProviderType | null;
  model?: string | null;
  temperature?: number | null;
  agent_model?: string | null;
}

export interface DisplayPreferencesUpdate {
  theme?: ThemeModeType | null;
  default_view?: DefaultViewType | null;
  sidebar_collapsed?: boolean | null;
}

export interface WorkflowDefaultsUpdate {
  default_repository?: string | null;
  default_assignee?: string | null;
  copilot_polling_interval?: number | null;
}

export interface NotificationPreferencesUpdate {
  task_status_change?: boolean | null;
  agent_completion?: boolean | null;
  new_recommendation?: boolean | null;
  chat_mention?: boolean | null;
}

export interface UserPreferencesUpdate {
  ai?: AIPreferencesUpdate;
  display?: DisplayPreferencesUpdate;
  workflow?: WorkflowDefaultsUpdate;
  notifications?: NotificationPreferencesUpdate;
}

export interface GlobalSettingsUpdate {
  ai?: AIPreferencesUpdate;
  display?: DisplayPreferencesUpdate;
  workflow?: WorkflowDefaultsUpdate;
  notifications?: NotificationPreferencesUpdate;
  allowed_models?: string[];
}

export interface ProjectSettingsUpdate {
  board_display_config?: ProjectBoardConfig | null;
  agent_pipeline_mappings?: Record<string, ProjectAgentMapping[]> | null;
  queue_mode?: boolean | null;
  auto_merge?: boolean | null;
}

// ============ Dynamic Model Fetching Types (012-settings-dynamic-ux) ============

export interface ModelOption {
  id: string;
  name: string;
  provider: string;
}

export interface ModelsResponse {
  status: 'success' | 'auth_required' | 'rate_limited' | 'error';
  models: ModelOption[];
  fetched_at: string | null;
  cache_hit: boolean;
  rate_limit_warning: boolean;
  message: string | null;
}

// ============ Signal Messaging Types (011-signal-chat-integration) ============

export type SignalConnectionStatus = 'pending' | 'connected' | 'error' | 'disconnected';

export type SignalNotificationMode = 'all' | 'actions_only' | 'confirmations_only' | 'none';

export type SignalLinkStatus = 'pending' | 'connected' | 'failed' | 'expired';

export interface SignalConnection {
  connection_id: string | null;
  status: SignalConnectionStatus | null;
  signal_identifier: string | null;
  notification_mode: SignalNotificationMode | null;
  linked_at: string | null;
  last_active_project_id: string | null;
}

export interface SignalLinkResponse {
  qr_code_base64: string;
  expires_in_seconds: number;
}

export interface SignalLinkStatusResponse {
  status: SignalLinkStatus;
  signal_identifier: string | null;
  error_message: string | null;
}

export interface SignalPreferences {
  notification_mode: SignalNotificationMode;
}

export interface SignalPreferencesUpdate {
  notification_mode: SignalNotificationMode;
}

export interface SignalBanner {
  id: string;
  message: string;
  created_at: string;
}

export interface SignalBannersResponse {
  banners: SignalBanner[];
}

// ============ MCP Configuration Types (012-mcp-settings-config) ============

export interface McpConfiguration {
  id: string;
  name: string;
  endpoint_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface McpConfigurationListResponse {
  mcps: McpConfiguration[];
  count: number;
}

export interface McpConfigurationCreate {
  name: string;
  endpoint_url: string;
}

// ============ Board Types (continued) ============

export type StatusColor =
  | 'GRAY'
  | 'BLUE'
  | 'GREEN'
  | 'YELLOW'
  | 'ORANGE'
  | 'RED'
  | 'PINK'
  | 'PURPLE';

export type ContentType = 'issue' | 'draft_issue' | 'pull_request';

export type PRState = 'open' | 'closed' | 'merged';

export interface BoardStatusOption {
  option_id: string;
  name: string;
  color: StatusColor;
  description?: string;
}

export interface BoardStatusField {
  field_id: string;
  options: BoardStatusOption[];
}

export interface BoardProject {
  project_id: string;
  name: string;
  description?: string;
  url: string;
  owner_login: string;
  status_field: BoardStatusField;
}

export interface BoardRepository {
  owner: string;
  name: string;
}

export interface BoardAssignee {
  login: string;
  avatar_url: string;
}

export interface BoardCustomFieldValue {
  name: string;
  color?: StatusColor;
}

export interface LinkedPR {
  pr_id: string;
  number: number;
  title: string;
  state: PRState;
  url: string;
}

export interface BoardLabel {
  id: string;
  name: string;
  color: string;
}

export interface SubIssue {
  id: string;
  number: number;
  title: string;
  url: string;
  state: string;
  assigned_agent?: string | null;
  assignees: BoardAssignee[];
  linked_prs: LinkedPR[];
}

export interface BoardItem {
  item_id: string;
  content_id?: string;
  content_type: ContentType;
  title: string;
  number?: number;
  repository?: BoardRepository;
  url?: string;
  body?: string;
  status: string;
  status_option_id: string;
  assignees: BoardAssignee[];
  priority?: BoardCustomFieldValue;
  size?: BoardCustomFieldValue;
  estimate?: number;
  linked_prs: LinkedPR[];
  sub_issues: SubIssue[];
  labels: BoardLabel[];
  issue_type?: string;
  created_at?: string;
  updated_at?: string;
  milestone?: string;
  queued?: boolean;
}

export interface BoardColumn {
  status: BoardStatusOption;
  items: BoardItem[];
  item_count: number;
  estimate_total: number;
  next_cursor?: string | null;
  has_more?: boolean;
}

// ============ Pagination ============

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset_at: number;
  used: number;
}

export type RefreshErrorType = 'rate_limit' | 'network' | 'auth' | 'server' | 'unknown';

export interface RefreshError {
  type: RefreshErrorType;
  message: string;
  rateLimitInfo?: RateLimitInfo;
  retryAfter?: Date;
}

export interface BoardDataResponse {
  project: BoardProject;
  columns: BoardColumn[];
  rate_limit?: RateLimitInfo | null;
}

export interface BoardProjectListResponse {
  projects: BoardProject[];
  rate_limit?: RateLimitInfo | null;
}

// ============ Cleanup Types ============

export interface BranchInfo {
  name: string;
  eligible_for_deletion: boolean;
  linked_issue_number: number | null;
  linked_issue_title: string | null;
  linking_method: string | null;
  preservation_reason: string | null;
  deletion_reason: string | null;
}

export interface PullRequestInfo {
  number: number;
  title: string;
  head_branch: string;
  referenced_issues: number[];
  eligible_for_deletion: boolean;
  preservation_reason: string | null;
  deletion_reason: string | null;
}

export interface OrphanedIssueInfo {
  number: number;
  title: string;
  labels: string[];
  html_url: string | null;
  node_id: string | null;
}

export interface IssueInfo {
  number: number;
  title: string;
  labels: string[];
  html_url: string | null;
  node_id: string | null;
  preservation_reason: string | null;
}

export interface IssueToDelete {
  number: number;
  node_id: string;
}

export interface CleanupPreflightResponse {
  branches_to_delete: BranchInfo[];
  branches_to_preserve: BranchInfo[];
  prs_to_close: PullRequestInfo[];
  prs_to_preserve: PullRequestInfo[];
  orphaned_issues: OrphanedIssueInfo[];
  issues_to_preserve: IssueInfo[];
  open_issues_on_board: number;
  has_permission: boolean;
  permission_error: string | null;
}

export interface CleanupItemResult {
  item_type: 'branch' | 'pr' | 'issue';
  identifier: string;
  action: 'deleted' | 'closed' | 'preserved' | 'failed';
  reason: string | null;
  error: string | null;
}

export interface CleanupExecuteRequest {
  owner: string;
  repo: string;
  project_id: string;
  branches_to_delete: string[];
  prs_to_close: number[];
  issues_to_delete: IssueToDelete[];
}

/** Payload from the confirm modal — the user's final selections after toggling. */
export interface CleanupConfirmPayload {
  branches_to_delete: string[];
  prs_to_close: number[];
  issues_to_delete: IssueToDelete[];
}

export interface CleanupExecuteResponse {
  operation_id: string;
  branches_deleted: number;
  branches_preserved: number;
  prs_closed: number;
  prs_preserved: number;
  issues_deleted: number;
  errors: CleanupItemResult[];
  results: CleanupItemResult[];
}

export interface CleanupAuditLogEntry {
  id: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  branches_deleted: number;
  branches_preserved: number;
  prs_closed: number;
  prs_preserved: number;
  errors_count: number;
  details: {
    results: CleanupItemResult[];
  } | null;
}

export interface CleanupHistoryResponse {
  operations: CleanupAuditLogEntry[];
  count: number;
}

// ============ Chores Types (016-replace-housekeeping-chores) ============

export type ScheduleType = 'time' | 'count';
export type ChoreStatus = 'active' | 'paused';

export interface Chore {
  id: string;
  project_id: string;
  name: string;
  template_path: string;
  template_content: string;
  schedule_type: ScheduleType | null;
  schedule_value: number | null;
  status: ChoreStatus;
  last_triggered_at: string | null;
  last_triggered_count: number;
  current_issue_number: number | null;
  current_issue_node_id: string | null;
  pr_number: number | null;
  pr_url: string | null;
  tracking_issue_number: number | null;
  execution_count: number;
  ai_enhance_enabled: boolean;
  agent_pipeline_id: string;
  is_preset: boolean;
  preset_id: string;
  created_at: string;
  updated_at: string;
}

export interface ChoreCreate {
  name: string;
  template_content: string;
}

export interface ChoreTemplate {
  name: string;
  about: string;
  path: string;
  content: string;
}

export interface ChoreUpdate {
  schedule_type?: ScheduleType | null;
  schedule_value?: number | null;
  status?: ChoreStatus;
  ai_enhance_enabled?: boolean;
  agent_pipeline_id?: string;
}

export interface ChoreTriggerResult {
  chore_id: string;
  chore_name: string;
  triggered: boolean;
  issue_number: number | null;
  issue_url: string | null;
  skip_reason: string | null;
}

export interface EvaluateChoreTriggersResponse {
  evaluated: number;
  triggered: number;
  skipped: number;
  results: ChoreTriggerResult[];
}

export interface ChoreChatMessage {
  content: string;
  conversation_id?: string | null;
  ai_enhance?: boolean;
}

export interface ChoreChatResponse {
  message: string;
  conversation_id: string;
  template_ready: boolean;
  template_content: string | null;
  template_name: string | null;
}

// ── Inline Editing Types ──

export interface ChoreInlineUpdate {
  name?: string;
  template_content?: string;
  schedule_type?: ScheduleType | null;
  schedule_value?: number | null;
  ai_enhance_enabled?: boolean;
  agent_pipeline_id?: string;
  expected_sha?: string;
}

export interface ChoreInlineUpdateResponse {
  chore: Chore;
  pr_number: number | null;
  pr_url: string | null;
  pr_merged: boolean;
  merge_error: string | null;
}

export interface ChoreCreateWithConfirmation {
  name: string;
  template_content: string;
  ai_enhance_enabled: boolean;
  agent_pipeline_id: string;
  auto_merge: boolean;
}

export interface ChoreCreateResponse {
  chore: Chore;
  issue_number: number | null;
  pr_number: number | null;
  pr_url: string | null;
  pr_merged: boolean;
  merge_error: string | null;
}

// ── Featured Rituals Types ──

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

// ============ Solune UI Redesign Types (025) ============

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
  type: 'agent' | 'chore' | 'pipeline';
  title: string;
  timestamp: string;
  read: boolean;
  source?: string;
}

// ============ Activity Event Types (054) ============

export interface ActivityEvent {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  project_id: string;
  actor: string;
  action: string;
  summary: string;
  detail?: Record<string, unknown>;
  created_at: string;
}

// ============ Pipeline Types ============

export interface PipelineAgentNode {
  id: string;
  agent_slug: string;
  agent_display_name: string;
  model_id: string;
  model_name: string;
  tool_ids: string[];
  tool_count: number;
  config: Record<string, unknown>;
}

export interface ExecutionGroup {
  id: string;
  order: number;
  execution_mode: 'sequential' | 'parallel';
  agents: PipelineAgentNode[];
}

export interface PipelineStage {
  id: string;
  name: string;
  order: number;
  /** Ordered execution groups within this stage. */
  groups?: ExecutionGroup[];
  agents: PipelineAgentNode[];
  execution_mode?: 'sequential' | 'parallel';
}

export interface PipelineConfig {
  id: string;
  project_id: string;
  name: string;
  description: string;
  stages: PipelineStage[];
  is_preset: boolean;
  preset_id: string;
  created_at: string;
  updated_at: string;
  auto_merge?: boolean;
}

export interface PipelineConfigSummary {
  id: string;
  name: string;
  description: string;
  stage_count: number;
  agent_count: number;
  total_tool_count: number;
  is_preset: boolean;
  preset_id: string;
  stages: PipelineStage[];
  updated_at: string;
}

export interface PipelineConfigListResponse {
  pipelines: PipelineConfigSummary[];
  total: number;
}

export interface PipelineConfigCreate {
  name: string;
  description?: string;
  stages: PipelineStage[];
}

export interface PipelineConfigUpdate {
  name?: string;
  description?: string;
  stages?: PipelineStage[];
}

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

export interface ProjectPipelineAssignment {
  project_id: string;
  pipeline_id: string;
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

// ============ MCP Tools Types (027-mcp-tools-page) ============

export type McpToolSyncStatus = 'synced' | 'pending' | 'error';

export interface McpToolConfig {
  id: string;
  name: string;
  description: string;
  endpoint_url: string;
  config_content: string;
  sync_status: McpToolSyncStatus;
  sync_error: string;
  synced_at: string | null;
  github_repo_target: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface McpToolConfigCreate {
  name: string;
  description: string;
  config_content: string;
  github_repo_target: string;
}

export interface McpToolConfigUpdate {
  name?: string;
  description?: string;
  config_content?: string;
  github_repo_target?: string;
}

export interface McpToolConfigListResponse {
  tools: McpToolConfig[];
  count: number;
}

export interface McpToolSyncResult {
  id: string;
  sync_status: McpToolSyncStatus;
  sync_error: string;
  synced_at: string | null;
  synced_paths: string[];
}

export interface RepoMcpServerConfig {
  name: string;
  config: Record<string, unknown>;
  source_paths: string[];
}

export interface RepoMcpServerUpdate {
  name: string;
  config_content: string;
}

export interface RepoMcpConfigResponse {
  paths_checked: string[];
  available_paths: string[];
  primary_path: string | null;
  servers: RepoMcpServerConfig[];
}

export interface McpPreset {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  config_content: string;
}

export interface McpPresetListResponse {
  presets: McpPreset[];
  count: number;
}

export interface ToolChip {
  id: string;
  name: string;
  description: string;
}

export interface ToolDeleteResult {
  success: boolean;
  deleted_id: string | null;
  affected_agents: ToolChip[];
}

// ============ Onboarding Tour & Help Types (042) ============

export type TourStepPlacement = 'top' | 'bottom' | 'left' | 'right';

export interface TourStep {
  id: number;
  targetSelector: string | null;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  placement: TourStepPlacement;
}

export type FaqCategory = 'getting-started' | 'agents-pipelines' | 'chat-voice' | 'settings-integration';

export interface FaqEntry {
  id: string;
  question: string;
  answer: string;
  category: FaqCategory;
}
