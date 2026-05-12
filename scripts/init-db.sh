#!/bin/bash
# Creates sessions_test database for integration tests
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE sessions_test' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sessions_test')\gexec
EOSQL
