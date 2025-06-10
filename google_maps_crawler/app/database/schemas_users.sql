-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    
    -- Indexes
    CONSTRAINT users_username_key UNIQUE (username),
    CONSTRAINT users_email_key UNIQUE (email)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Add created_by column to crawl_sessions to track which user initiated the crawl
ALTER TABLE crawl_sessions 
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS created_by_username VARCHAR(50);

-- Create a default admin user (password: crawlmapUS)
-- Note: Change this password immediately in production!
INSERT INTO users (username, email, password_hash, full_name, is_superuser)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$eQTrkJYHqOISxn5n2WYMpe1GBdL9JXqP.BZQcLvkU.bK9cYRhFW86',  -- bcrypt hash of 'crawlmapUS'
    'Administrator',
    true
) ON CONFLICT (username) DO NOTHING;

-- Create a sample regular user (password: user123)
INSERT INTO users (username, email, password_hash, full_name, is_superuser)
VALUES (
    'user',
    'user@example.com',
    '$2b$12$YRgRrZRVQeM.mJGQZKPxLus6pGZjlL8YZuTwK0bvN5zH3kC3gNy3a',  -- bcrypt hash of 'user123'
    'Regular User',
    false
) ON CONFLICT (username) DO NOTHING;