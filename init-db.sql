-- Face Recognition System Database Initialization
-- This script sets up the PostgreSQL database with required extensions and initial data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enable row level security (optional for future use)
-- ALTER DATABASE face_tracking SET row_security = on;

-- Create indexes for better performance (these will be created by SQLAlchemy as well)
-- Additional indexes can be added here for specific query patterns

-- Initial data setup
-- This will be handled by the backend application, but you can add default data here

-- Example: Default camera configuration
-- INSERT INTO cameras (location, camera_type, resolution_width, resolution_height, fps, is_active) 
-- VALUES ('Main Entrance', 'entry', 1920, 1080, 30, true);

-- Example: Default roles (if using role table)
-- INSERT INTO roles (role_name, permissions) VALUES 
-- ('employee', '{"can_view_dashboard": true}'),
-- ('admin', '{"can_view_dashboard": true, "can_view_all_users": true, "can_create_users": true}'),
-- ('super_admin', '{"can_view_dashboard": true, "can_view_all_users": true, "can_create_users": true, "can_manage_system": true}');

-- Set up any additional database-level configurations
-- Configure timezone
SET timezone = 'UTC';

-- Performance tuning (adjust based on your server capacity)
-- These are examples - actual values should be tuned based on your hardware
-- ALTER SYSTEM SET shared_buffers = '256MB';
-- ALTER SYSTEM SET effective_cache_size = '1GB';
-- ALTER SYSTEM SET maintenance_work_mem = '64MB';
-- ALTER SYSTEM SET checkpoint_completion_target = 0.9;
-- ALTER SYSTEM SET wal_buffers = '16MB';
-- ALTER SYSTEM SET default_statistics_target = 100;

-- Note: The actual table creation is handled by SQLAlchemy in the backend application
-- This script is for database-level setup and initial data only

COMMIT;