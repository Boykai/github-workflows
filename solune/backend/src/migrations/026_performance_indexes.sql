-- 026: Add performance indexes on frequently filtered columns
-- (security-performance-contracts.md)

CREATE INDEX IF NOT EXISTS idx_global_settings_admin
    ON global_settings (admin_github_user_id);

CREATE INDEX IF NOT EXISTS idx_user_sessions_project
    ON user_sessions (selected_project_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON chat_messages (session_id);

CREATE INDEX IF NOT EXISTS idx_chat_proposals_session
    ON chat_proposals (session_id);

CREATE INDEX IF NOT EXISTS idx_chat_recommendations_session
    ON chat_recommendations (session_id);
