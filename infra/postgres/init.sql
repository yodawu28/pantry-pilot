-- Database initialization
-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on email
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);

-- Insert demo user
INSERT INTO users (id, email, name, created_at)
VALUES (1, 'demo@pantrypilot.com', 'Demo User', NOW())
ON CONFLICT (id) DO NOTHING;

SELECT 'PostgreSQL initialized with demo user: demo@pantrypilot.com' AS message;