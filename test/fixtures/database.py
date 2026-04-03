import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    toml = Path.cwd() / "pyproject.toml"
    assert toml.exists(), f"Pytest must be ran at project root folder not {Path.cwd()}"

    alembic_conf = Config(toml_file=toml)
    try:
        command.upgrade(alembic_conf, "head")
    finally:
        pass


@pytest.fixture(scope="session")
def database_engine():
    """Create a test database engine and setup schema."""
    engine = create_engine(
        os.environ["DB_URL"],
        echo=False,
        isolation_level="READ COMMITTED",
        pool_size=5,
        max_overflow=5,
        pool_reset_on_return="rollback",
    )
    yield engine

    # Cleanup
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
            conn.execute(text('CREATE SCHEMA "raw";'))
            conn.execute(text("TRUNCATE TABLE alembic_version;"))
            conn.commit()
    finally:
        engine.dispose()


@pytest.fixture
def database_session(database_engine: Engine):
    """Create a fresh database session for each test."""
    SessionLocal = sessionmaker(
        bind=database_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    with SessionLocal(autocommit=False) as session:
        try:
            yield session
        finally:
            session.rollback()
            session.close()


@pytest.fixture
def sample_events_batch(database_session: Session):
    """Populate test database with sample events."""
    from datetime import UTC, datetime

    from api.models import EventTypesEnum, RawEvent

    events = [
        RawEvent(
            event_type=EventTypesEnum.cpu_usage,  # type: ignore
            service="worker-1",
            value=75.5,
            host="host001.example.com",
            timestamp=datetime.now(UTC),
        ),
        RawEvent(
            event_type=EventTypesEnum.memory_usage,  # type: ignore
            service="worker-1",
            value=82.3,
            host="host001.example.com",
            timestamp=datetime.now(UTC),
        ),
        RawEvent(
            event_type=EventTypesEnum.disk_io,  # type: ignore
            service="worker-2",
            value=45.1,
            host="host002.example.com",
            timestamp=datetime.now(UTC),
        ),
    ]  # type: ignore

    for event in events:
        database_session.add(event)

    database_session.commit()
    return events
