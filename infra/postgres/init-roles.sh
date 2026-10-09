#!/bin/bash
set -euo pipefail

psql -v ON_ERROR_STOP=1 -v app_password="$APP_DB_PASSWORD" \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
CREATE DATABASE examslot_test;
CREATE ROLE examslot_app WITH LOGIN PASSWORD :'app_password';
ALTER ROLE examslot_app SET statement_timeout = '10s';
ALTER ROLE examslot_app SET idle_in_transaction_session_timeout = '30s';
SQL

for database in "$POSTGRES_DB" examslot_test; do
  psql -v ON_ERROR_STOP=1 -v database="$database" \
    --username "$POSTGRES_USER" --dbname "$database" <<'SQL'
GRANT CONNECT ON DATABASE :"database" TO examslot_app;
GRANT USAGE ON SCHEMA public TO examslot_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO examslot_app;
SQL
done
