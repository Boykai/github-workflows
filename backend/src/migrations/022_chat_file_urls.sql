-- Add file_urls column to chat_proposals for persisting attachment URLs
ALTER TABLE chat_proposals ADD COLUMN file_urls TEXT DEFAULT NULL;

-- Add file_urls column to chat_recommendations for persisting attachment URLs
ALTER TABLE chat_recommendations ADD COLUMN file_urls TEXT DEFAULT NULL;
