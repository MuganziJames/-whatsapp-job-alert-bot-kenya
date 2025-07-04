-- Update database schema for dual-platform support
-- Run this in your Supabase SQL Editor

-- Add new columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'whatsapp';
ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS interests JSONB DEFAULT '[]';

-- Update existing users to have platform info
UPDATE users SET platform = 'whatsapp' WHERE platform IS NULL;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_users_platform ON users(platform);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position; 