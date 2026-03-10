-- Migration 019: Add ai_agent_model to user_preferences and global_settings
--
-- Adds a dedicated fallback model field for GitHub Copilot Agents, separate
-- from the existing ai_model (chat model) field.  When set, this value is used
-- as Tier 3 in agent model resolution instead of the user's chat model.
ALTER TABLE user_preferences ADD COLUMN ai_agent_model TEXT;
ALTER TABLE global_settings ADD COLUMN ai_agent_model TEXT;
