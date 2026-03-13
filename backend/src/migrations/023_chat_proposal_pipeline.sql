-- Add selected_pipeline_id column to chat_proposals for pipeline context
ALTER TABLE chat_proposals ADD COLUMN selected_pipeline_id TEXT DEFAULT NULL;
