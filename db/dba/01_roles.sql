DO $$
BEGIN
    IF current_database() != 'telemetry' THEN
        RAISE INFO 'Connected to wrong database';
        RETURN;
    END IF;
    -- Revoke privileges from public
    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'telemetry') THEN
        REVOKE ALL ON SCHEMA public FROM PUBLIC;
        REVOKE CONNECT ON DATABASE telemetry FROM PUBLIC;
    END IF;

    -- Assuming that the database is called telemetry
    -- These are some of the roles to have the right and
    -- least privileges in the database
    CREATE ROLE db_telemetry_connect WITH NOLOGIN;
    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'telemetry') THEN
        GRANT CONNECT ON DATABASE telemetry TO db_telemetry_connect;
    END IF;

    CREATE ROLE telemetry_owner WITH NOLOGIN;
    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'telemetry') THEN
        ALTER DATABASE telemetry
            OWNER TO telemetry_owner;

        ALTER SCHEMA "raw"
            OWNER TO telemetry_owner;
    END IF;

    -- Role to use raw schema, this is to avoid boiler plate code
    -- given for every role that can use that schema
    CREATE ROLE telemetry_raw WITH NOLOGIN;
    GRANT USAGE ON SCHEMA "raw" TO telemetry_raw;

    -- These two roles is going to be member our api user
    CREATE ROLE telemetry_raw_write WITH NOLOGIN;
    GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "raw" TO telemetry_raw_write;
    GRANT USAGE ON ALL SEQUENCES IN SCHEMA "raw" TO telemetry_raw_write;

    -- Altering default privileges so when a new sequence is
    -- created the role would be able to use it
    ALTER DEFAULT PRIVILEGES FOR ROLE telemetry_owner IN SCHEMA "raw"
    GRANT USAGE ON SEQUENCES TO telemetry_raw_write;

    ALTER DEFAULT PRIVILEGES FOR ROLE telemetry_owner IN SCHEMA "raw"
    GRANT INSERT, UPDATE, DELETE ON TABLES TO telemetry_raw_write;

    CREATE ROLE telemetry_raw_read WITH NOLOGIN;
    GRANT SELECT ON ALL TABLES IN SCHEMA "raw" TO telemetry_raw_read;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA "raw" TO telemetry_raw_read;

    ALTER DEFAULT PRIVILEGES FOR ROLE telemetry_owner IN SCHEMA "raw"
    GRANT SELECT ON TABLES TO telemetry_raw_read;

    GRANT telemetry_raw_write TO telemetry_raw;
    GRANT telemetry_raw_read TO telemetry_raw;

    CREATE ROLE telemetry_read WITH NOLOGIN;
    GRANT telemetry_raw_read TO telemetry_read;

    CREATE ROLE telemetry_write WITH NOLOGIN;
    GRANT telemetry_raw_write TO telemetry_write;

    CREATE ROLE telemetry_admin WITH NOLOGIN;
    GRANT ALL PRIVILEGES ON DATABASE telemetry TO telemetry_admin;


    GRANT db_telemetry_connect
    TO
        telemetry_raw,
        telemetry_admin;
END $$;
