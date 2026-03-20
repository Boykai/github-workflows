import { z } from 'zod';

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
  queued: z.boolean().optional().default(false),
});