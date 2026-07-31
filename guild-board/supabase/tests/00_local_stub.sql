-- ============================================================================
-- Local test stub for the Supabase-managed objects.
--
-- Supabase provides `auth`, `storage`, the `supabase_realtime` publication and
-- the anon/authenticated/service_role roles. A bare Postgres does not, so this
-- creates just enough of them to apply the migrations and exercise the RLS
-- policies locally.
--
-- NOT part of the deployed schema. Never run this against a Supabase project.
--
--   createdb guildboard_test
--   psql -d guildboard_test -f supabase/tests/00_local_stub.sql
--   psql -d guildboard_test -f supabase/migrations/001_initial_schema.sql
--   psql -d guildboard_test -f supabase/migrations/002_escrow_automation.sql
--   psql -d guildboard_test -f supabase/seed.sql
--   psql -d guildboard_test -f supabase/tests/01_schema_logic.sql
--   psql -d guildboard_test --single-transaction -f supabase/tests/02_rls.sql
--
-- Requires PostGIS (postgresql-16-postgis-3).
-- ============================================================================

create role anon nologin;
create role authenticated nologin;
create role service_role nologin;

create schema if not exists auth;
create schema if not exists storage;

create table auth.users (
  id uuid primary key default gen_random_uuid(),
  email text,
  raw_user_meta_data jsonb default '{}'::jsonb
);

create or replace function auth.uid() returns uuid
  language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create or replace function auth.role() returns text
  language sql stable as $$ select coalesce(nullif(current_setting('request.jwt.claim.role', true), ''), 'authenticated') $$;

create table storage.buckets (
  id text primary key, name text not null, public boolean default false,
  file_size_limit bigint, allowed_mime_types text[]
);
create table storage.objects (
  id uuid primary key default gen_random_uuid(),
  bucket_id text references storage.buckets(id),
  name text, owner uuid
);
alter table storage.objects enable row level security;

create or replace function storage.foldername(name text) returns text[]
  language sql immutable as $$ select string_to_array(name, '/') $$;

create publication supabase_realtime;
