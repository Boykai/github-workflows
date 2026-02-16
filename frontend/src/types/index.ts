/**
 * TypeScript types for GitHub Projects Chat Interface API.
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

export const AVAILABLE_LABELS: IssueLabel[] = [
  'feature', 'bug', 'enhancement', 'refactor', 'documentation', 'testing', 'infrastructure',
  'frontend', 'backend', 'database', 'api',
  'ai-generated', 'good first issue', 'help wanted',
  'security', 'performance', 'accessibility', 'ux'
];

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
  agent_mappings: Record<string, string[]>;
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

// ============ Project Board Types ============

export interface BoardAssignee {
  login: string;
  avatar_url: string;
}

export interface LinkedPullRequest {
  pr_number: number;
  title: string;
  state: 'OPEN' | 'CLOSED' | 'MERGED';
  url: string;
}

export interface BoardIssueCard {
  item_id: string;
  content_id: string | null;
  issue_number: number | null;
  title: string;
  body: string | null;
  state: string | null;
  url: string | null;
  repo_name: string | null;
  repo_full_name: string | null;
  status: string | null;
  priority: string | null;
  size: string | null;
  estimate: number | null;
  assignees: BoardAssignee[];
  linked_prs: LinkedPullRequest[];
}

export interface BoardStatusColumn {
  name: string;
  color: string;
  option_id: string;
  description: string | null;
  item_count: number;
  total_estimate: number | null;
  items: BoardIssueCard[];
}

export interface BoardProject {
  project_id: string;
  title: string;
  description: string | null;
  url: string;
  item_count: number;
  status_columns: { name: string; color: string; option_id: string }[];
}

export interface BoardProjectListResponse {
  projects: BoardProject[];
}

export interface BoardDataResponse {
  project_id: string;
  title: string;
  columns: BoardStatusColumn[];
}

export interface LinkedPRsRequest {
  content_ids: string[];
}

export interface LinkedPRsResponse {
  linked_prs: Record<string, LinkedPullRequest[]>;
}
