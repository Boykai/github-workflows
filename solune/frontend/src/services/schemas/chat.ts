import { z } from 'zod';

const ActionTypeSchema = z.enum(['task_create', 'status_update', 'project_select', 'issue_create']);
const ProposalStatusSchema = z.enum(['pending', 'confirmed', 'edited', 'cancelled']);
const RecommendationStatusSchema = z.enum(['pending', 'confirmed', 'rejected']);
const IssuePrioritySchema = z.enum(['P0', 'P1', 'P2', 'P3']);
const IssueSizeSchema = z.enum(['XS', 'S', 'M', 'L', 'XL']);
const IssueLabelSchema = z.enum([
  'feature',
  'bug',
  'enhancement',
  'refactor',
  'documentation',
  'testing',
  'infrastructure',
  'frontend',
  'backend',
  'database',
  'api',
  'ai-generated',
  'good first issue',
  'help wanted',
  'security',
  'performance',
  'accessibility',
  'ux',
]);

const IssueMetadataSchema = z.object({
  priority: IssuePrioritySchema,
  size: IssueSizeSchema,
  estimate_hours: z.number(),
  start_date: z.string(),
  target_date: z.string(),
  labels: z.array(IssueLabelSchema),
  assignees: z.array(z.string()).optional(),
  milestone: z.string().nullable().optional(),
  branch: z.string().nullable().optional(),
});

const TaskCreateActionDataSchema = z.object({
  proposal_id: z.string(),
  task_id: z.string().optional(),
  status: ProposalStatusSchema,
  proposed_title: z.string().optional(),
  proposed_description: z.string().optional(),
});

const StatusUpdateActionDataSchema = z.object({
  task_id: z.string(),
  new_status: z.string().optional(),
  confirmed: z.boolean().optional(),
  proposal_id: z.string().optional(),
  task_title: z.string().optional(),
  current_status: z.string().optional(),
  target_status: z.string().optional(),
  status_option_id: z.string().optional(),
  status_field_id: z.string().optional(),
  status: z.string().optional(),
});

const ProjectSelectActionDataSchema = z.object({
  project_id: z.string(),
  project_name: z.string(),
});

const IssueCreateActionDataSchema = z.object({
  recommendation_id: z.string(),
  proposed_title: z.string(),
  user_story: z.string(),
  ui_ux_description: z.string(),
  functional_requirements: z.array(z.string()),
  metadata: IssueMetadataSchema.optional(),
  status: RecommendationStatusSchema,
});

const ActionDataSchema = z.union([
  TaskCreateActionDataSchema,
  StatusUpdateActionDataSchema,
  ProjectSelectActionDataSchema,
  IssueCreateActionDataSchema,
]);

const ChatMessageSchema = z.object({
  message_id: z.string(),
  session_id: z.string(),
  sender_type: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  action_type: ActionTypeSchema.optional(),
  action_data: ActionDataSchema.optional(),
  timestamp: z.string(),
  status: z.enum(['pending', 'sent', 'failed']).optional(),
});

export const ChatMessagesResponseSchema = z.object({
  messages: z.array(ChatMessageSchema),
});