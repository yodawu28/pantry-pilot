INSERT INTO users (id, email, name, created_at)
VALUES (1, 'demo@pantrypilot.com', 'Demo User', NOW())
ON CONFLICT (id) DO NOTHING;

SELECT 'Seeded user: demo@pantrypilot.com' AS message;