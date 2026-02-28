/**
 * TypeScript types for Agent Projects API.
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
}

export interface StatusUpdateActionData {
  task_id: string;
  old_status: string;
  new_status: string;
  confirmed: boolean;
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

export interface ChatMessage {
  message_id: string;
  session_id: string;
  sender_type: SenderType;
  content: string;
  action_type?: ActionType;
  action_data?: ActionData;
  timestamp: string;
}

export interface ChatMessageRequest {
  content: string;
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
  id: string;           // UUID string
  slug: string;         // Agent identifier
  display_name?: string | null;
  config?: Record<string, unknown> | null;
}

export interface AvailableAgent {
  slug: string;
  display_name: string;
  description?: string | null;
  avatar_url?: string | null;
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

export interface BoardProjectListResponse {
  projects: BoardProject[];
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
}

export interface BoardColumn {
  status: BoardStatusOption;
  items: BoardItem[];
  item_count: number;
  estimate_total: number;
}

export interface BoardDataResponse {
  project: BoardProject;
  columns: BoardColumn[];
}
