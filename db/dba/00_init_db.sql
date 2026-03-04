DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'telemetry') THEN
        CREATE DATABASE telemetry;
    END IF;
END $$ LANGUAGE plpgsql;
\c telemetry

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS "raw";
