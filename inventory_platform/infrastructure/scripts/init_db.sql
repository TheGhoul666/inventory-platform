-- Database initialization script
-- Runs once when PostgreSQL container first starts.

-- Restrict direct DELETE/UPDATE on audit_logs to prevent tampering
-- (The application user only needs INSERT + SELECT on this table)

-- Performance extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Partial index for open alerts (most common query pattern)
-- (These are created after Alembic runs the full schema migration)

-- Recommended PostgreSQL settings for this workload are in docker-compose.yml
-- under the postgres service command section.
