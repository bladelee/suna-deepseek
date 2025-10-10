-- Initial database schema setup
-- This migration script sets up the necessary schemas and permissions for Suna

-- Create pgcrypto extension for cryptographic functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create public schema if not exists
CREATE SCHEMA IF NOT EXISTS public;

-- Create graphql_public schema for GraphQL API
CREATE SCHEMA IF NOT EXISTS graphql_public;

-- Create basejump schema for core functionality
CREATE SCHEMA IF NOT EXISTS basejump;

-- Create anon role (used for unauthenticated access)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
END
$$;

-- Create authenticated role (used for authenticated access)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
END
$$;

-- Create service_role (used for server-side operations)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
END
$$;

-- Set default permissions for public schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE ON SEQUENCES TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated, service_role;

-- Set permissions for graphql_public schema
GRANT USAGE ON SCHEMA graphql_public TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA graphql_public
  GRANT SELECT ON TABLES TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA graphql_public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated, service_role;

-- Set permissions for basejump schema
-- IMPORTANT: This schema needs to be exposed in Supabase dashboard
GRANT USAGE ON SCHEMA basejump TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA basejump
  GRANT SELECT ON TABLES TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA basejump
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated, service_role;

-- Ensure postgres user has full access
GRANT ALL PRIVILEGES ON SCHEMA public, graphql_public, basejump TO postgres;

-- Set search path for convenience
ALTER DATABASE postgres SET search_path TO public, graphql_public, basejump;

-- Create a sample table to verify the setup
CREATE TABLE IF NOT EXISTS public.health_check (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert a sample record
INSERT INTO public.health_check (message) VALUES ('Database initialized successfully') ON CONFLICT DO NOTHING;

-- Grant permissions on health_check table
GRANT SELECT ON public.health_check TO anon, authenticated;
GRANT ALL PRIVILEGES ON public.health_check TO authenticated, service_role, postgres;

-- Make sure the sequences are accessible
GRANT USAGE, SELECT ON SEQUENCE public.health_check_id_seq TO anon, authenticated, service_role;