from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.schema import MetaData

from .config import Config


class DBBase(DeclarativeBase):
    metadata = MetaData(schema="raw")


_engine = create_engine(
    Config["DB_URL"],
    echo=False,
    echo_pool=False,
    isolation_level="READ COMMITTED",
    pool_size=Config["DB_POOL_SIZE"],
    max_overflow=15,
    connect_args={"options": f"-c timezone={Config['TIMEZONE'] or 'UTC'}"},
)

SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)

PG_VERSION = _engine.dialect.server_version_info
PG_MINIMUM_VERSION = (18, 0)
if not PG_VERSION:
    try:
        with _engine.connect() as conn:
            version = conn.execute(text("SHOW server_version")).first()
            PG_VERSION = version and tuple(int(x) for x in version[0].split("."))
    except SQLAlchemyError:
        PG_VERSION = (18, 0)  # Assume the minimum supported version if we can't determine it
elif PG_VERSION < PG_MINIMUM_VERSION:
    raise RuntimeError(
        f"PostgreSQL version {PG_VERSION} is not supported. Upgrade to a newer version to use this application."
    )
