-- WhatsApp Job Alert Bot Database Schema
-- Run this in your Supabase SQL editor

-- Users table to store user information and credits
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    interest VARCHAR(50),
    balance INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs sent table to prevent duplicate job sends
CREATE TABLE IF NOT EXISTS jobs_sent (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    job_id VARCHAR(100) NOT NULL,
    job_title TEXT,
    job_url TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(phone, job_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_interest ON users(interest);
CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance);
CREATE INDEX IF NOT EXISTS idx_jobs_sent_phone ON jobs_sent(phone);
CREATE INDEX IF NOT EXISTS idx_jobs_sent_job_id ON jobs_sent(job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_sent_sent_at ON jobs_sent(sent_at);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs_sent ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated access
-- This allows your backend service to access all data when authenticated
CREATE POLICY "Allow all operations for authenticated users" ON users
FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON jobs_sent
FOR ALL USING (auth.role() = 'authenticated');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at timestamp
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing (optional)
-- INSERT INTO users (phone, interest, balance) VALUES 
-- ('+254700000001', 'fundi', 5),
-- ('+254700000002', 'cleaner', 3),
-- ('+254700000003', 'tutor', 10);

-- Views for analytics (optional)
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    interest,
    COUNT(*) as user_count,
    SUM(balance) as total_balance,
    AVG(balance) as avg_balance
FROM users 
WHERE interest IS NOT NULL AND interest != ''
GROUP BY interest
ORDER BY user_count DESC;

CREATE OR REPLACE VIEW job_alert_stats AS
SELECT 
    DATE(sent_at) as date,
    COUNT(*) as alerts_sent,
    COUNT(DISTINCT phone) as unique_users
FROM jobs_sent
GROUP BY DATE(sent_at)
ORDER BY date DESC;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated; 