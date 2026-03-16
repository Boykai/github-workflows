import { z } from 'zod';

const StatusColumnSchema = z.object({
  field_id: z.string(),
  name: z.string(),
  option_id: z.string(),
  color: z.string().optional(),
});

const ProjectSchema = z.object({
  project_id: z.string(),
  owner_id: z.string(),
  owner_login: z.string(),
  name: z.string(),
  type: z.enum(['organization', 'user', 'repository']),
  url: z.string(),
  description: z.string().optional(),
  status_columns: z.array(StatusColumnSchema),
  item_count: z.number().optional(),
  cached_at: z.string(),
});

export const ProjectListResponseSchema = z.object({
  projects: z.array(ProjectSchema),
});