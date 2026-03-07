ALTER TABLE agent_configs
ADD COLUMN default_model_id TEXT NOT NULL DEFAULT '';

ALTER TABLE agent_configs
ADD COLUMN default_model_name TEXT NOT NULL DEFAULT '';